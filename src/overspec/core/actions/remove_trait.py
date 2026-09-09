from dataclasses import dataclass

from .base import Action
from overspec.core.trait_system.models import Suppress, fields, nonblank


@dataclass(frozen=True)
class RemoveTraitAction(Action):
    trait: str

    @classmethod
    def parse(cls, data):
        fields(data, {"trait"})
        return cls(nonblank(data["trait"], "trait"))

    def references(self):
        return (self.trait,)

    def evaluate(self, context):
        return Suppress(self.trait)
