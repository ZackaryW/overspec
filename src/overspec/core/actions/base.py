from abc import ABC, abstractmethod

from overspec.core.trait_system.models import EvaluationContext, Suppress


class Action(ABC):
    """A validated action returning effects, without mutating shared state."""

    @classmethod
    @abstractmethod
    def parse(cls, data: dict) -> "Action":
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, context: EvaluationContext) -> Suppress:
        raise NotImplementedError

    def references(self) -> tuple[str, ...]:
        return ()
