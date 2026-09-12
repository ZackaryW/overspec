"""Confined atomic files and validated current project state."""

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from zuu.case5 import ConfinedPath, TargetState

STATE_PATH = "openspec/.over/.state.json"


def encoded(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def read_bytes(root, relative):
    plan = ConfinedPath(relative).inspect(
        root, allowed=(TargetState.FILE, TargetState.ABSENT)
    )
    return plan.target.read_bytes() if plan.state == TargetState.FILE else None


def read_json(root, relative):
    raw = read_bytes(root, relative)
    if raw is None:
        raise ValueError(f"Missing {relative}; run init/update or sync")
    try:
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("Expected an object")
        return value
    except (ValueError, UnicodeError) as exc:
        raise ValueError(f"Corrupt {relative}; run init/update or sync") from exc


def atomic_write(root, relative, content, *, recheck=None):
    plan = ConfinedPath(relative).inspect(
        root, allowed=(TargetState.FILE, TargetState.ABSENT)
    )
    if plan.state == TargetState.FILE and plan.target.read_bytes() == content:
        if recheck:
            recheck()
        return False
    plan.target.parent.mkdir(parents=True, exist_ok=True)
    # Parent creation changes absence evidence: inspect again before creating the temp.
    plan = ConfinedPath(relative).inspect(
        root, allowed=(TargetState.FILE, TargetState.ABSENT)
    )
    fd, temporary = tempfile.mkstemp(prefix=".over-", dir=plan.target.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        plan.revalidate()
        if recheck:
            recheck()
        os.replace(temporary, plan.target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return True


def empty_state(root):
    return {
        "version": 1,
        "root": str(root),
        "compilation": None,
        "resolution": None,
        "sync": None,
    }


def section(data):
    return {"id": digest(data), "data": data}


def validate_state(root, state):
    try:
        if (
            set(state) - {'schema'} != {"version", "root", "compilation", "resolution", "sync"}
            or type(state["version"]) is not int
            or state["version"] != 1
            or state["root"] != str(root)
        ):
            raise ValueError("format or root mismatch")
        if 'schema' in state:
            from .schema_assets import validate_baseline
            saved_schema = state['schema']
            if not isinstance(saved_schema, dict) or set(saved_schema) != {'id', 'data'} or saved_schema['id'] != digest(saved_schema['data']):
                raise ValueError('invalid schema content/hash')
            validate_baseline(saved_schema['data'])
        for name, version in [("compilation", 1), ("resolution", 2)]:
            saved = state[name]
            if saved is None:
                continue
            if not isinstance(saved, dict) or set(saved) != {"id", "data"}:
                raise ValueError(f"invalid {name} section")
            data = saved["data"]
            if (
                not isinstance(data, dict)
                or data.get("root") != str(root)
                or type(data.get("version")) is not int
                or data["version"] != version
                or saved["id"] != digest(data)
            ):
                raise ValueError(f"invalid {name} content/hash")
            if not isinstance(data.get("traits"), list) or not isinstance(
                data.get("static"), dict
            ):
                raise ValueError(f"invalid {name} data")
            for key, kind in [
                ("matched", list),
                ("suppressed", list),
                ("bodies", dict),
                ("decisions", dict),
            ]:
                if not isinstance(data["static"].get(key), kind):
                    raise ValueError(f"invalid {name} static {key}")
            if name == "compilation" and (
                not isinstance(data.get("compatibility"), str)
                or not isinstance(data.get("inputs"), dict)
            ):
                raise ValueError("invalid compilation inputs")
            if name == "resolution" and (
                not isinstance(data.get("runtime_defaults"), dict)
                or not isinstance(data.get("variables"), dict)
            ):
                raise ValueError("invalid resolution inputs")
        receipt = state["sync"]
        if (receipt is None) != (state["resolution"] is None):
            raise ValueError("resolution and sync metadata must be stored together")
        if receipt is not None:
            if (
                not isinstance(receipt, dict)
                or set(receipt) != {"resolution", "fingerprint"}
                or state["resolution"] is None
                or receipt["resolution"] != state["resolution"]["id"]
                or not isinstance(receipt["fingerprint"], str)
                or not re.fullmatch("[0-9a-f]{64}", receipt["fingerprint"])
            ):
                raise ValueError("invalid sync linkage")
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"Corrupt current state: {exc}; restore .state.json or move it aside, then update and sync"
        ) from exc
    return state


def read_state(root, *, missing_ok=False):
    raw = read_bytes(root, STATE_PATH)
    if raw is None:
        if missing_ok:
            return empty_state(root)
        raise ValueError(
            "Missing current state; run init or update, then sync (legacy .state/ is not loaded)"
        )
    try:
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("expected an object")
    except (ValueError, UnicodeError) as exc:
        raise ValueError(
            "Corrupt .state.json; restore state or move it aside, then update and sync"
        ) from exc
    return validate_state(root, value)


def has_compilation(root):
    if read_bytes(root, STATE_PATH) is not None:
        return read_state(root)["compilation"] is not None
    return read_bytes(root, "openspec/.over/.state/compiled.json") is not None


def save_state(root, value, *, expected, recheck=None):
    validate_state(root, value)

    def check():
        if read_bytes(root, STATE_PATH) != expected:
            raise ValueError("Current state changed during publication; retry")
        if recheck:
            recheck()

    return atomic_write(root, STATE_PATH, encoded(value), recheck=check)


def load_bundle(root, namespace, identity):
    if not isinstance(identity, str) or not re.fullmatch("[0-9a-f]{64}", identity):
        raise ValueError("Invalid resolution identifier; resync")
    name = {"compilations": "compilation", "resolutions": "resolution"}.get(namespace)
    if name is None:
        raise ValueError("Invalid state section")
    saved = read_state(root)[name]
    if saved is None:
        raise ValueError(f"Missing current {name}; run update then sync")
    if saved["id"] != identity:
        raise ValueError(
            f"Stale {name} ID: superseded by current state; use the current command after sync"
        )
    return saved["data"]
