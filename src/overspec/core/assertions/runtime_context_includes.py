from dataclasses import dataclass

from .base import Assertion
from overspec.core.trait_system.models import MatchResult, fields, nonblank


@dataclass(frozen=True)
class RuntimeContextIncludesAssertion(Assertion):
    key: str
    includes: object
    runtime_only = True

    @classmethod
    def parse(cls, data):
        fields(data, {"k", "includes"})
        if not isinstance(data["includes"], (str, int, float, bool, type(None))):
            raise ValueError("includes must be a scalar or variable reference")
        if data["includes"] == "$":
            raise ValueError("includes variable needs a name")
        return cls(nonblank(data["k"], "k"), data["includes"])

    def evaluate(self, context):
        target = context.runtime.get(self.key)
        if not isinstance(target, tuple):
            return MatchResult(False, f"{self.key} is not a list")
        values = (self.includes,)
        if isinstance(self.includes, str) and self.includes.startswith("$"):
            key = self.includes[1:]
            values = context.runtime.get(key)
            if not isinstance(values, tuple):
                raise ValueError(f"{key} must be supplied as a list")
        matched = any(type(a) is type(b) and a == b for a in target for b in values)
        return MatchResult(matched, f"Exact membership for {self.key}: {matched}")
