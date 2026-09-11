from dataclasses import dataclass

from overspec.core.frameworks import behave, cucumber, flutter
from overspec.core.frameworks.evidence import Evidence
from overspec.core.trait_system.models import MatchResult, fields

from .base import Assertion

DETECTORS = {
    "behave": behave.detect,
    "cucumber": cucumber.detect,
    "flutter": flutter.detect,
}


@dataclass(frozen=True)
class BddFrameworkAssertion(Assertion):
    name: str
    runtime_only = True

    @classmethod
    def parse(cls, data):
        fields(data, {"name"})
        name = data["name"]
        if not isinstance(name, str) or name not in DETECTORS:
            raise ValueError("bdd-framework name must be behave, cucumber, or flutter")
        return cls(name)

    def evaluate(self, context):
        if "bdd" in context.runtime:
            selection = context.runtime["bdd"]
            if not isinstance(selection, tuple) or any(
                not isinstance(v, str) or v not in DETECTORS for v in selection
            ):
                raise ValueError(
                    "bdd must be a list of behave, cucumber, or flutter identifiers (or [])"
                )
            matched = self.name in selection
            return MatchResult(
                matched, f"Explicit bdd selection for {self.name}: {matched}"
            )
        matched = DETECTORS[self.name](Evidence(context.project))
        return MatchResult(matched, f"Repository evidence for {self.name}: {matched}")
