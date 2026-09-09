"""Source validation delegates handler payloads to their registered contracts."""

import re
import tomllib

from .conditions import parse_condition
from .models import PHASES, Trait, nonblank
from .registry import builtins


def attachment(value):
    if not isinstance(value, str) or not (
        value in ("context", "operations.apply.guidance", "operations.archive.guidance")
        or value.startswith("rules.")
        and value[6:].strip()
    ):
        raise ValueError(f"Unsupported attach: {value!r}")
    return value


def parse_trait(data, phase, origin, registry=None):
    registry = registry or builtins()
    try:
        if phase not in PHASES or not isinstance(data, dict):
            raise ValueError("Invalid trait declaration")
        required = {"name", "attach", "body"}
        allowed = required | {"details", "assert", "assert_or_grouping", "actions"}
        if not required <= data.keys() or data.keys() - allowed:
            raise ValueError("Missing required or unknown trait fields")
        name = nonblank(data["name"], "name")
        if not re.fullmatch(r"[a-z][a-z0-9-]*", name):
            raise ValueError(f"Invalid trait name: {name}")
        body = nonblank(data["body"], "body")
        if "<!-- over:" in body or "# over:" in body:
            raise ValueError("Body contains reserved source marker")
        details = data.get("details")
        if "details" in data and not isinstance(details, str):
            raise ValueError("details must be a string")
        details = details if details and details.strip() else None
        condition = parse_condition(data, registry)
        if not isinstance(data.get("actions", []), list):
            raise ValueError("actions must be a list")
        actions = tuple(registry.action(d) for d in data.get("actions", []))
        source = {**data}
        if details is None:
            source.pop("details", None)
        return Trait(
            name,
            phase,
            attachment(data["attach"]),
            body,
            details,
            origin,
            condition,
            actions,
            source,
        )
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{origin}: {exc}") from exc


def parse_document(text: str, origin: str, registry=None) -> list[Trait]:
    try:
        document = tomllib.loads(text)
        if document.keys() - set(PHASES):
            raise ValueError("Unknown declaration type")
        result = []
        for phase, declarations in document.items():
            if not isinstance(declarations, list):
                raise ValueError(f"{phase} must be an array of tables")
            result.extend(parse_trait(d, phase, origin, registry) for d in declarations)
        return result
    except ValueError as exc:
        raise ValueError(f"{origin}: {exc}") from exc


def compose(profile: list[Trait], local: list[Trait]):
    for layer in (profile, local):
        seen = {}
        for trait in layer:
            if trait.name in seen:
                raise ValueError(
                    f"Duplicate {trait.name}: {seen[trait.name]} and {trait.origin}"
                )
            seen[trait.name] = trait.origin
    effective = {t.name: t for t in profile}
    overridden = [effective[t.name] for t in local if t.name in effective]
    effective.update({t.name: t for t in local})
    return sorted(effective.values(), key=lambda t: PHASES.index(t.phase)), overridden
