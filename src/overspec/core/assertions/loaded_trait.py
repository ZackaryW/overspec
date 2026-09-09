from dataclasses import dataclass

from .base import Assertion
from overspec.core.trait_system.models import MatchResult, fields, nonblank


@dataclass(frozen=True)
class LoadedTraitAssertion(Assertion):
    trait: str

    @classmethod
    def parse(cls, data):
        fields(data, {"trait"})
        return cls(nonblank(data["trait"], "trait"))

    def references(self):
        return (self.trait,)

    def evaluate(self, context):
        matched = self.trait in context.matched
        return MatchResult(matched, f"{self.trait} previously matched: {matched}")
