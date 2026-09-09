from dataclasses import dataclass

import pytest


def test_registry_dispatches_through_abstract_contracts(tmp_path):
    from overspec.core.assertions.base import Assertion
    from overspec.core.actions.base import Action
    from overspec.core.trait_system.models import (
        EvaluationContext,
        MatchResult,
        Suppress,
    )
    from overspec.core.trait_system.registry import Registry

    @dataclass(frozen=True)
    class Custom(Assertion):
        value: bool

        @classmethod
        def parse(cls, data):
            return cls(data["value"])

        def evaluate(self, context):
            with pytest.raises(TypeError):
                context.runtime["new"] = True
            return MatchResult(self.value, "custom result")

    @dataclass(frozen=True)
    class Hide(Action):
        @classmethod
        def parse(cls, data):
            return cls()

        def evaluate(self, context):
            return Suppress("hidden")

    registry = Registry()
    registry.register_assertion("custom", Custom)
    registry.register_action("hide", Hide)
    context = EvaluationContext(tmp_path)
    handler, negated = registry.assertion({"type": "~custom", "value": True})
    assert negated and handler.evaluate(context) == MatchResult(True, "custom result")
    assert registry.action({"type": "hide"}).evaluate(context) == Suppress("hidden")
    with pytest.raises(ValueError, match="duplicate"):
        registry.register_assertion("custom", Custom)
    with pytest.raises(ValueError, match="Unknown"):
        registry.assertion({"type": "unknown"})
    with pytest.raises(TypeError):
        Assertion()
    with pytest.raises(TypeError):
        Action()
