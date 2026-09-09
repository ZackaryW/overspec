from abc import ABC, abstractmethod

from overspec.core.trait_system.models import EvaluationContext, MatchResult


class Assertion(ABC):
    """A validated predicate evaluated against invocation-owned inputs."""

    runtime_only = False

    @classmethod
    @abstractmethod
    def parse(cls, data: dict) -> "Assertion":
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, context: EvaluationContext) -> MatchResult:
        raise NotImplementedError

    def references(self) -> tuple[str, ...]:
        return ()
