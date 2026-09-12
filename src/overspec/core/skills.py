"""Select packaged skills and delegate native lifecycle/recovery to ZuAT."""

import json
import os
from dataclasses import asdict
from pathlib import Path, PurePosixPath

from zuat.pub import AssetInput, AssetSelector, Zuat, ZuatRequest
from zuu.case5 import ConfinedPath, TargetState

from . import skill_assets, storage

AGENTS = ("codex", "claude", "kimi", "pi")
OPERATIONS = {"install", "update", "uninstall", "restore", "revert", "recovery"}


def asset_name(item):
    return item.evidence.get("asset_name") or PurePosixPath(item.ref.locator).name


def independent(item):
    return (
        item.ref.kind == "skill"
        and item.ref.scope == "user"
        and item.evidence.get("provider", "global") == "global"
    )


class Skills:
    def __init__(self, home=None, agent_home=None):
        self.home = Path(
            home or os.environ.get("OVERSPEC_HOME", Path.home() / ".overspec")
        ).resolve()
        self.agent_home = Path(agent_home or Path.home()).resolve()
        self.registry = self.home / "zuat"

    def bind_home(self):
        """Relative ZuAT asset locators require one immutable native-home binding."""
        binding = {"version": 1, "agent_home": str(self.agent_home)}
        self.home.mkdir(parents=True, exist_ok=True)
        existing = storage.read_bytes(self.home, "zuat-home.json")
        if existing is None:
            registry = ConfinedPath("zuat").inspect(
                self.home, allowed=(TargetState.DIRECTORY, TargetState.ABSENT)
            )
            if registry.state == TargetState.DIRECTORY and any(
                registry.target.iterdir()
            ):
                raise ValueError(
                    "Unbound ZuAT registry: choose a fresh Overspec home; native home cannot be inferred"
                )
            self.home.mkdir(parents=True, exist_ok=True)
            target = ConfinedPath("zuat-home.json").inspect(
                self.home, allowed=(TargetState.ABSENT, TargetState.FILE)
            )
            try:
                with target.target.open("xb") as stream:
                    stream.write(storage.encoded(binding))
            except FileExistsError:
                pass
            existing = storage.read_bytes(self.home, "zuat-home.json")
        try:
            if json.loads(existing) != binding:
                raise ValueError(
                    "Native home does not match this Overspec skill registry; use its original home"
                )
        except (TypeError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                "Invalid native home binding; restore zuat-home.json"
            ) from exc
        ConfinedPath("zuat").inspect(
            self.home, allowed=(TargetState.DIRECTORY, TargetState.ABSENT)
        )

    @staticmethod
    def events(service):
        result = service.history()
        if not result.ok:
            raise ValueError(
                "Cannot read skill history: " + "; ".join(result.diagnostics)
            )
        return [e for e in result.history if e.kind.value in OPERATIONS]

    def run(
        self,
        operation,
        *,
        agents=(),
        names=(),
        all_skills=False,
        force=False,
        operation_id=None,
    ):
        if operation == "list":
            return {
                "ok": True,
                "skills": [asdict(s) for s in skill_assets.skill_catalog()],
            }
        if operation not in {
            "status",
            "install",
            "update",
            "history",
            "restore",
            "remove",
        }:
            raise ValueError("Unknown skill operation")
        if not agents or len(agents) != len(set(agents)) or set(agents) - set(AGENTS):
            raise ValueError(
                "Select explicit unique --agent values: " + ", ".join(AGENTS)
            )
        if bool(names) == bool(all_skills) or len(names) != len(set(names)):
            raise ValueError("Select unique --name values or --all, exclusively")
        if operation == "restore" and not operation_id:
            raise ValueError("Restore requires an operation ID")
        if force and operation not in {"restore", "remove"}:
            raise ValueError("Force is supported only for restore and remove")
        self.bind_home()
        with Zuat(root=self.registry, home=self.agent_home) as service:
            if operation in {"history", "restore", "remove"}:
                return self.historical(
                    service, operation, agents, names, all_skills, force, operation_id
                )
            catalog = {s.name: s for s in skill_assets.skill_catalog()}
            selected = sorted(catalog) if all_skills else list(names)
            if set(selected) - catalog.keys():
                raise ValueError(
                    "Unknown packaged skill: "
                    + ", ".join(sorted(set(selected) - catalog.keys()))
                )
            rows = []
            with skill_assets.materialize_skills(selected) as sources:
                for agent in agents:
                    for source in sources:
                        row = {
                            "agent": agent,
                            "name": source.name,
                            "origin": source.origin,
                        }
                        try:
                            asset = AssetInput(
                                agent,
                                "skill",
                                scope="user",
                                name=source.name,
                                source=str(source.path),
                            )
                            inspection = service.inspect_asset(asset)
                            row.update(
                                {
                                    "classification": inspection.classification,
                                    "owned": inspection.owned,
                                    "diagnostics": list(inspection.diagnostics),
                                }
                            )
                            if inspection.name and inspection.name != source.name:
                                raise ValueError(
                                    "Packaged skill identity differs from native identity"
                                )
                            if operation == "status":
                                row["ok"] = inspection.classification not in {
                                    "unsupported",
                                    "indeterminate",
                                }
                            elif (
                                operation == "install"
                                and inspection.classification == "absent"
                            ):
                                row.update(
                                    service.install(
                                        ZuatRequest(agents=(agent,), assets=(asset,))
                                    ).to_dict()
                                )
                            else:
                                row.update(
                                    service.update_asset(asset, force=True).to_dict()
                                )
                            row["changed"] = row.get("data", {}).get(
                                "changed",
                                bool(row.get("ok") and row.get("operation_id")),
                            )
                        except (ValueError, OSError, RuntimeError) as exc:
                            row.update(ok=False, diagnostics=[str(exc)])
                        rows.append(row)
            return self.result(operation, rows)

    def result(self, operation, rows):
        return {
            "ok": all(r["ok"] for r in rows),
            "operation": operation,
            "registry": str(self.registry),
            "agent_home": str(self.agent_home),
            "results": rows,
        }

    def historical(
        self, service, operation, agents, names, all_skills, force, operation_id
    ):
        events = self.events(service)
        target = None
        if operation == "restore":
            target = next((e for e in events if e.operation_id == operation_id), None)
            if target is None:
                raise ValueError("Unknown or unrelated skill operation")
            events = [target]
        available = {
            (i.ref.agent, asset_name(i)): i.ref.id
            for e in events
            for i in (*e.before, *e.after)
            if independent(i)
        }
        chosen = {
            (a, n) for a, n in available if a in agents and (all_skills or n in names)
        }
        if names and set(names) - {n for _, n in chosen}:
            raise ValueError("Unknown recorded skill selection")
        if operation != "history" and any(
            not any(a == agent for a, _ in chosen) for agent in agents
        ):
            raise ValueError("No recorded skills for a selected agent")
        if not chosen and operation != "history":
            raise ValueError("No recorded skills match this operation")

        def matches(item):
            return independent(item) and (item.ref.agent, asset_name(item)) in chosen

        if operation == "history":
            history = []
            for event in events:
                if any(matches(i) for i in (*event.before, *event.after)):
                    row = event.to_dict()
                    row["before"] = [i.to_dict() for i in event.before if matches(i)]
                    row["after"] = [i.to_dict() for i in event.after if matches(i)]
                    history.append(row)
            return {**self.result(operation, []), "history": history}
        rows = []
        for agent, name in sorted(chosen):
            try:
                if operation == "remove":
                    result = service.uninstall(
                        ZuatRequest(
                            agents=(agent,),
                            asset_refs=(available[(agent, name)],),
                            force=force,
                        )
                    )
                else:
                    # Successful single-target transitions can be inverted against
                    # their after-state without force; partial recovery uses snapshots.
                    if (
                        target.kind.value in {"install", "update", "uninstall"}
                        and target.outcome.value == "success"
                    ):
                        affected = {
                            (i.ref.agent, asset_name(i))
                            for i in (*target.before, *target.after)
                        }
                        if affected != {(agent, name)}:
                            raise ValueError(
                                "Cannot partially invert this multi-target operation"
                            )
                        result = service.revert(
                            ZuatRequest(
                                agents=(agent,), operation_id=operation_id, force=force
                            )
                        )
                    else:
                        result = service.restore_all(
                            operation_id,
                            AssetSelector(
                                agent,
                                kind="skill",
                                scope="user",
                                provider="global",
                                name=name,
                                present=None,
                            ),
                            force=force,
                        )
                rows.append({"agent": agent, "name": name, **result.to_dict()})
            except (ValueError, OSError, RuntimeError) as exc:
                rows.append(
                    {
                        "agent": agent,
                        "name": name,
                        "ok": False,
                        "diagnostics": [str(exc)],
                    }
                )
        return self.result(operation, rows)
