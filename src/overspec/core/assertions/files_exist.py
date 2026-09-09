from dataclasses import dataclass

from zuu.case5 import ConfinedPath, TargetState
from .base import Assertion
from overspec.core.trait_system.models import MatchResult, fields


@dataclass(frozen=True)
class FilesExistAssertion(Assertion):
    paths: tuple[ConfinedPath, ...]

    @classmethod
    def parse(cls, data):
        fields(data, {"paths"})
        paths = data["paths"]
        if (
            not isinstance(paths, list)
            or not paths
            or any(not isinstance(p, str) for p in paths)
        ):
            raise ValueError("paths must be a nonempty list of relative file paths")
        return cls(tuple(ConfinedPath(p) for p in paths))

    def evaluate(self, context):
        states = [p.inspect(context.project).state for p in self.paths]
        return MatchResult(
            all(s == TargetState.FILE for s in states), f"File states: {states}"
        )
