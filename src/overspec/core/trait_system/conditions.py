"""Parse composition operators without knowing concrete assertion types."""

import re

from .models import ConditionGroup, Predicate


def parse_leaf(data, registry, path):
    try:
        handler, negated = registry.assertion(data)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{path}: {exc}") from exc
    return Predicate(handler, negated, path)


def parse_group(data, registry, path="assert"):
    if not isinstance(data, dict):
        raise ValueError(f"{path}: group must be a table")
    any_child = data.get("or", False)
    if type(any_child) is not bool:
        raise ValueError(f"{path}.or must be boolean")
    numbers = data.keys() - {"or", "assertion"}
    for number in sorted(numbers):
        if not isinstance(number, str) or not re.fullmatch(r"[1-9][0-9]*", number):
            raise ValueError(
                f"{path}.{number}: expected a positive canonical group number"
            )
    if "assertion" in data:
        if numbers:
            raise ValueError(f"{path}: cannot mix assertion leaves and numbered groups")
        leaves = data["assertion"]
        if not isinstance(leaves, list) or not leaves:
            raise ValueError(f"{path}.assertion must be a nonempty array")
        children = tuple(
            parse_leaf(leaf, registry, f"{path}.assertion.{i}")
            for i, leaf in enumerate(leaves, 1)
        )
    else:
        if not numbers:
            raise ValueError(f"{path}: empty condition group")
        children = tuple(
            parse_group(data[key], registry, f"{path}.{key}")
            for key in sorted(numbers, key=int)
        )
    return ConditionGroup(children, any_child, path)


def parse_condition(data, registry):
    assertions = data.get("assert", [])
    if isinstance(assertions, dict):
        if "assert_or_grouping" in data:
            raise ValueError(
                "assert: assert_or_grouping cannot accompany a group table; use or"
            )
        return parse_group(assertions, registry)
    if not isinstance(assertions, list):
        raise ValueError("assert must be a group table or legacy list")
    grouping = data.get("assert_or_grouping", False)
    if type(grouping) is not bool:
        raise ValueError("assert_or_grouping must be boolean")
    return ConditionGroup(
        tuple(
            parse_leaf(leaf, registry, f"assert.assertion.{i}")
            for i, leaf in enumerate(assertions, 1)
        ),
        grouping,
    )
