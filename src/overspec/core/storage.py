"""Validated root-relative state publication using immutable generations."""

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from zuu.case5 import ConfinedPath, TargetState


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


def publish(root, namespace, value):
    identity = digest(value)
    relative = f"openspec/.over/.state/{namespace}/{identity}.json"
    existing = read_bytes(root, relative)
    if existing is not None and existing != encoded(value):
        raise ValueError(
            f"Corrupt immutable {namespace} bundle; restore state or resync"
        )
    atomic_write(root, relative, encoded(value))
    return identity


def load_bundle(root, namespace, identity):
    if not isinstance(identity, str) or not re.fullmatch("[0-9a-f]{64}", identity):
        raise ValueError("Invalid resolution identifier; resync")
    value = read_json(root, f"openspec/.over/.state/{namespace}/{identity}.json")
    if (
        digest(value) != identity
        or value.get("root") != str(root)
        or type(value.get("version")) is not int
        or value.get("version") not in ((1, 2) if namespace == "resolutions" else (1,))
    ):
        raise ValueError("Corrupt or root-mismatched resolution; resync")
    return value
