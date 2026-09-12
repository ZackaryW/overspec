"""Plan and publish the packaged project schema without overwriting local edits."""

import hashlib
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from zuu.case5 import ConfinedPath, TargetState

from .package_assets import payload, resource_tree

DESTINATION = "openspec/schemas/overspec"


def fingerprint(content):
    return hashlib.sha256(content).hexdigest()


def schema_payload():
    files = payload(resource_tree("schemas/overspec", "openspec/schemas/overspec"))
    try:
        schema = YAML(typ="safe").load(files["schema.yaml"].decode("utf-8"))
        if schema["name"] != "overspec" or not schema["artifacts"]:
            raise ValueError("invalid schema")
        for artifact in schema["artifacts"]:
            if "templates/" + artifact["template"] not in files:
                raise ValueError(f"Missing schema template: {artifact['template']}")
    except (KeyError, TypeError, UnicodeError, YAMLError) as exc:
        raise ValueError(f"Invalid packaged schema: {exc}") from exc
    return files


def validate_baseline(baseline):
    if (
        not isinstance(baseline, dict)
        or set(baseline) != {"name", "files"}
        or baseline["name"] != "overspec"
    ):
        raise ValueError("Invalid schema baseline")
    files = baseline["files"]
    if not isinstance(files, dict) or "schema.yaml" not in files:
        raise ValueError("Invalid schema file baseline")
    for name, digest in files.items():
        if (
            not isinstance(name, str)
            or not name
            or "\\" in name
            or ":" in name
            or PurePosixPath(name).is_absolute()
            or any(p in ("", ".", "..") for p in name.split("/"))
            or not isinstance(digest, str)
            or not re.fullmatch("[a-f0-9]{64}", digest)
        ):
            raise ValueError("Invalid schema baseline path or fingerprint")


def installed_payload(root):
    plan = ConfinedPath(DESTINATION).inspect(
        root, allowed=(TargetState.DIRECTORY, TargetState.ABSENT)
    )
    return payload(plan.target) if plan.state == TargetState.DIRECTORY else {}


@dataclass
class SchemaPlan:
    root: object
    desired: dict
    observed: dict
    writes: tuple
    removals: tuple
    status: str

    @property
    def baseline(self):
        return {
            "name": "overspec",
            "files": {n: fingerprint(b) for n, b in self.desired.items()},
        }


def plan_schema_install(root, files, baseline):
    validate_baseline(
        {"name": "overspec", "files": {n: fingerprint(b) for n, b in files.items()}}
    )
    actual = installed_payload(root)
    for name in files:
        ConfinedPath(DESTINATION + "/" + name).inspect(
            root, allowed=(TargetState.FILE, TargetState.ABSENT)
        )
    if baseline is None:
        if actual and actual != files:
            raise ValueError(
                "Schema conflict: existing unmanaged tree differs; reconcile or back it up before retrying"
            )
        status = "adopted-identical" if actual else "installed"
    else:
        validate_baseline(baseline)
        conflicts = [
            n
            for n, h in baseline["files"].items()
            if n not in actual or fingerprint(actual[n]) != h
        ]
        conflicts += [n for n in files if n not in baseline["files"] and n in actual]
        if conflicts:
            raise ValueError("Schema conflict: " + ", ".join(sorted(set(conflicts))))
        status = "updated"
    old = baseline["files"] if baseline else {}
    return SchemaPlan(
        root,
        dict(files),
        actual,
        tuple(n for n in files if actual.get(n) != files[n]),
        tuple(n for n in old if n not in files),
        status,
    )


def install_schema(root):
    from . import storage
    from .projection import config_target, parse_yaml

    # A project lifecycle operation must target an existing valid OpenSpec config.
    config = config_target(root)
    parse_yaml(config.read_text(encoding="utf-8"))
    expected_state = storage.read_bytes(root, storage.STATE_PATH)
    state = storage.read_state(root, missing_ok=True)
    files = schema_payload()
    saved = state.get("schema")
    if saved is not None:
        validate_baseline(saved["data"])
    plan = plan_schema_install(root, files, saved["data"] if saved else None)
    expected = dict(plan.observed)
    completed = []

    def recheck():
        # Atomic writers stage a temporary sibling. Recheck captured and managed
        # identities; unrelated new files are preserved, not publication targets.
        actual = installed_payload(root)
        relevant = set(plan.observed) | set(files)
        if {
            n: b for n, b in actual.items() if n in relevant
        } != expected or schema_payload() != files:
            raise ValueError("Schema source or target changed during publication")
        if storage.read_bytes(root, storage.STATE_PATH) != expected_state:
            raise ValueError("Current state changed during schema publication")

    try:
        recheck()
        for name in plan.writes:
            storage.atomic_write(
                root, DESTINATION + "/" + name, files[name], recheck=recheck
            )
            expected[name] = files[name]
            completed.append(name)
        for name in plan.removals:
            recheck()
            target = ConfinedPath(DESTINATION + "/" + name).inspect(
                root, allowed=(TargetState.FILE,)
            )
            target.revalidate()
            target.target.unlink()
            expected.pop(name)
            completed.append(name)
        state["schema"] = storage.section(plan.baseline)
        storage.save_state(root, state, expected=expected_state, recheck=recheck)
    except (ValueError, OSError) as exc:
        raise ValueError(
            f"Schema publication failed; completed paths: {completed}. "
            f"Compilation not refreshed. Reconcile schema files and retry update: {exc}"
        ) from exc
    return {
        "status": plan.status if completed or saved is None else "current",
        "changed": bool(completed),
        "path": str(root / DESTINATION),
        "files": completed,
        "selection": "Preserved; select schema: overspec explicitly when desired",
    }
