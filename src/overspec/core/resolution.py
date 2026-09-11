"""Retained resolution inspection, runtime evaluation, and body contributions."""

import shlex

from . import storage
from .change_scope import change_root
from .trait_system.evaluator import evaluate, validate_references
from .trait_system.rendering import variables
from .trait_system.sources import parse_trait
from .variables import file_layers


def contributions(bundle, identity):
    result = []
    groups = {}
    state = bundle["static"]
    for record in bundle["traits"]:
        data = record["declaration"]
        name, attach = data["name"], data["attach"]
        if record["phase"] == "runtime-trait":
            groups.setdefault(attach, []).append(name)
        elif name in state["bodies"] and name not in state["suppressed"]:
            result.append(
                {"name": name, "attach": attach, "body": state["bodies"][name]}
            )
    for attach, names in groups.items():
        command = shlex.join(
            [
                "overspec",
                "trait",
                "resolve",
                "--resolution",
                identity,
                "--attach",
                attach,
            ]
            + [arg for name in names for arg in ("--trait", name)]
        )
        body = (
            "From this project's root, run:\n" + command + "\n"
            "Supply --context-file <path> when current invocation context is available, "
            "and apply the returned guidance to this operation.\n"
        )
        if bundle["version"] >= 2:
            body += (
                "For an active change, obtain changeRoot from OpenSpec using openspec status --change <name> --json "
                "(preserving the selected --store), then append --change-root <changeRoot> to this command. "
                "Without a selected change, use project variables only.\n"
            )
        result.append({"name": ",".join(names), "attach": attach, "body": body})
    return result


def resolve_runtime(root, identity, attach, names, context=None, *, change=None):
    if not isinstance(context if context is not None else {}, dict):
        raise ValueError("Runtime context must be a JSON object")
    bundle = storage.load_bundle(root, "resolutions", identity)
    selected = change_root(change) if change is not None else None
    traits = [
        parse_trait(t["declaration"], t["phase"], t["origin"]) for t in bundle["traits"]
    ]
    validate_references(traits)
    group = [t for t in traits if t.phase == "runtime-trait" and t.attach == attach]
    available = {t.name for t in group}
    if not names or len(set(names)) != len(names) or not set(names) <= available:
        raise ValueError(
            "Unknown or duplicate runtime trait IDs or mismatched attachment"
        )
    values = variables(
        bundle["runtime_defaults"],
        *file_layers(root, "openspec/.over/"),
        *(file_layers(selected) if selected is not None else []),
        context or {},
    )
    runtime = values
    state = evaluate(
        group, root, prior=bundle["static"], values=values, runtime=runtime
    )
    return [
        {"name": t.name, "attach": t.attach, "body": state["bodies"][t.name]}
        for t in group
        if t.name in names
        and t.name in state["matched"]
        and t.name not in state["suppressed"]
    ]


def explain(bundle):
    result = []
    state = bundle["static"]
    for record in bundle["traits"]:
        data = record["declaration"]
        name = data["name"]
        status = (
            "deferred"
            if record["phase"] == "runtime-trait"
            else "unmatched"
            if name not in state["matched"]
            else "suppressed"
            if name in state["suppressed"]
            else "retained"
            if record["phase"] == "compiletime-trait"
            else "matched"
        )
        result.append(
            {
                "name": name,
                "phase": record["phase"],
                "attach": data["attach"],
                "origin": record["origin"],
                "status": status,
                "has_details": bool(data.get("details")),
                "decision": state["decisions"].get(name),
                **(
                    {"provenance": record["provenance"]}
                    if "provenance" in record
                    else {}
                ),
            }
        )
    result.extend({**record, "status": "overridden"} for record in bundle["overridden"])
    result.extend(
        {
            "name": record["source_id"],
            "origin": "saucepan:" + record["source_id"],
            "phase": "source",
            "attach": "-",
            "status": "excluded",
            **record,
        }
        for record in bundle.get("sources", [])
    )
    return result


def show_details(root, name, identity=None):
    from .projection import config_target, owned_fingerprint

    if identity is None:
        receipt = storage.read_state(root)["sync"]
        if receipt is None:
            raise ValueError("Missing successful sync; run sync")
        current = owned_fingerprint(config_target(root).read_text(encoding="utf-8"))
        if current != receipt.get("fingerprint"):
            raise ValueError(
                "Saved synchronization is stale; resync or supply --resolution"
            )
        identity = receipt.get("resolution")
    bundle = storage.load_bundle(root, "resolutions", identity)
    for record in bundle["traits"]:
        data = record["declaration"]
        if data["name"] == name:
            return {
                "name": name,
                "phase": record["phase"],
                "attach": data["attach"],
                "origin": record["origin"],
                "resolution": identity,
                "details": data.get("details"),
                "message": "Details available"
                if data.get("details")
                else "No details available",
            }
    raise ValueError(f"Unknown trait in saved resolution: {name}")
