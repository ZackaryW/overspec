"""Shared immutable handler inputs and typed results; no concrete imports."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from overspec.core.assertions.base import Assertion


def freeze(value):
    if isinstance(value, Mapping):
        return MappingProxyType({k: freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(v) for v in value)
    return value


@dataclass(frozen=True)
class EvaluationContext:
    project: Path
    matched: frozenset[str] = frozenset()
    runtime: Mapping = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "matched", frozenset(self.matched))
        object.__setattr__(self, "runtime", freeze(self.runtime))


@dataclass(frozen=True)
class MatchResult:
    matched: bool
    reason: str


@dataclass(frozen=True)
class Suppress:
    name: str


def fields(data: dict, required: set[str]) -> None:
    if set(data) != required:
        raise ValueError(f"Expected fields {sorted(required)}, got {sorted(data)}")


def nonblank(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonblank string")
    return value


PHASES = ("compiletime-trait", "trait", "runtime-trait")


@dataclass(frozen=True)
class Predicate:
    handler: "Assertion"
    negated: bool
    path: str


@dataclass(frozen=True)
class ConditionGroup:
    children: tuple["Predicate | ConditionGroup", ...]
    any_child: bool = False
    path: str = "assert"

    def leaves(self):
        for child in self.children:
            if isinstance(child, ConditionGroup):
                yield from child.leaves()
            else:
                yield child


@dataclass(frozen=True)
class Trait:
    name: str
    phase: str
    attach: str
    body: str
    details: str | None
    origin: str
    condition: ConditionGroup
    actions: tuple
    source: dict = field(repr=False)

    @property
    def predicates(self):
        """Ordered leaf view for callers inspecting assertion payloads."""
        return tuple((leaf.handler, leaf.negated) for leaf in self.condition.leaves())

    def record(self):
        return {"phase": self.phase, "origin": self.origin, "declaration": self.source}
