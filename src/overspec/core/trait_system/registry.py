from overspec.core.assertions.base import Assertion
from overspec.core.actions.base import Action


class Registry:
    def __init__(self):
        self.assertions: dict[str, type[Assertion]] = {}
        self.actions: dict[str, type[Action]] = {}

    def register_assertion(self, name, handler):
        self._register(self.assertions, name, handler, Assertion)

    def register_action(self, name, handler):
        self._register(self.actions, name, handler, Action)

    @staticmethod
    def _register(target, name, handler, base):
        if name in target:
            raise ValueError(f"duplicate registration: {name}")
        if not issubclass(handler, base):
            raise TypeError(f"{handler} must implement {base.__name__}")
        target[name] = handler

    def assertion(self, data):
        kind, payload = self._payload(data)
        negate = kind.startswith("~")
        name = kind[1:] if negate else kind
        if name not in self.assertions:
            raise ValueError(f"Unknown assertion: {kind}")
        return self.assertions[name].parse(payload), negate

    def action(self, data):
        kind, payload = self._payload(data)
        if kind not in self.actions:
            raise ValueError(f"Unknown action: {kind}")
        return self.actions[kind].parse(payload)

    @staticmethod
    def _payload(data):
        if not isinstance(data, dict) or not isinstance(data.get("type"), str):
            raise ValueError("Handler requires a string type")
        return data["type"], {k: v for k, v in data.items() if k != "type"}


def builtins() -> Registry:
    from overspec.core.assertions.bdd_framework import BddFrameworkAssertion
    from overspec.core.assertions.which import WhichAssertion
    from overspec.core.assertions.files_exist import FilesExistAssertion
    from overspec.core.assertions.python_dependency import PythonDependencyAssertion
    from overspec.core.assertions.require_trait import RequireTraitAssertion
    from overspec.core.assertions.loaded_trait import LoadedTraitAssertion
    from overspec.core.assertions.runtime_context_match import (
        RuntimeContextMatchAssertion,
    )
    from overspec.core.assertions.runtime_context_includes import (
        RuntimeContextIncludesAssertion,
    )
    from overspec.core.actions.remove_trait import RemoveTraitAction

    registry = Registry()
    for name, handler in (
        ("bdd-framework", BddFrameworkAssertion),
        ("which", WhichAssertion),
        ("files-exist", FilesExistAssertion),
        ("python-dependency", PythonDependencyAssertion),
        ("require-trait", RequireTraitAssertion),
        ("loaded-trait", LoadedTraitAssertion),
        ("runtime-context-match", RuntimeContextMatchAssertion),
        ("runtime-context-includes", RuntimeContextIncludesAssertion),
    ):
        registry.register_assertion(name, handler)
    registry.register_action("remove-trait", RemoveTraitAction)
    return registry
