"""Behave configuration and standardized Python dependency evidence."""

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from zuu.case13 import deep_get


def _requirements(value):
    if not isinstance(value, list) or any(not isinstance(v, str) for v in value):
        raise ValueError("dependencies must be a list of requirements")
    return {canonicalize_name(Requirement(v).name) for v in value}


def _groups(groups):
    if not isinstance(groups, dict):
        raise ValueError("dependency-groups must be a table")
    normalized = {}
    for name, entries in groups.items():
        key = canonicalize_name(name, validate=True)
        if key in normalized:
            raise ValueError(f"ambiguous dependency-group: {name}")
        normalized[key] = entries
    resolved = {}

    def visit(name, active):
        if name in active:
            raise ValueError(f"dependency-group cycle: {' -> '.join((*active, name))}")
        if name not in normalized:
            raise ValueError(f"unknown dependency-group: {name}")
        if name in resolved:
            return resolved[name]
        entries = normalized[name]
        if not isinstance(entries, list):
            raise ValueError(f"dependency-group {name} must be a list")
        names = set()
        for entry in entries:
            if isinstance(entry, str):
                names.update(_requirements([entry]))
            elif (isinstance(entry, dict) and set(entry) == {"include-group"}
                  and isinstance(entry['include-group'], str)):
                names.update(visit(canonicalize_name(entry['include-group'], validate=True),
                                   (*active, name)))
            else:
                raise ValueError(f"invalid entry in dependency-group {name}")
        resolved[name] = names
        return names

    return set().union(*(visit(name, ()) for name in normalized))


def detect(evidence):
    if any(evidence.file(name) for name in ("behave.ini", ".behaverc")):
        return True
    document = evidence.document("pyproject.toml", "toml")
    if document is None:
        return False
    try:
        project = document.get("project", {})
        tool = document.get("tool", {})
        if not isinstance(project, dict) or not isinstance(tool, dict):
            raise ValueError("project and tool must be tables")
        if "behave" in tool:
            if not isinstance(tool["behave"], dict):
                raise ValueError("tool.behave must be a table")
            return True
        names = _requirements(deep_get(document, ["project", "dependencies"], default=[]))
        optional = deep_get(document, ["project", "optional-dependencies"], default={})
        if not isinstance(optional, dict):
            raise ValueError("project.optional-dependencies must be a table")
        for value in optional.values():
            names.update(_requirements(value))
        names.update(_groups(document.get("dependency-groups", {})))
        return "behave" in names
    except ValueError as exc:
        raise ValueError(f"pyproject.toml: {exc}") from exc
