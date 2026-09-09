from dataclasses import dataclass
import tomllib

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from zuu.case5 import ConfinedPath, TargetState
from zuu.case13 import deep_get
from .base import Assertion
from overspec.core.trait_system.models import MatchResult, fields, nonblank


@dataclass(frozen=True)
class PythonDependencyAssertion(Assertion):
    name: str

    @classmethod
    def parse(cls, data):
        fields(data, {"name"})
        return cls(canonicalize_name(nonblank(data["name"], "name"), validate=True))

    def evaluate(self, context):
        plan = ConfinedPath("pyproject.toml").inspect(
            context.project, allowed=(TargetState.ABSENT, TargetState.FILE)
        )
        if plan.state == TargetState.ABSENT:
            return MatchResult(False, "pyproject.toml is absent")
        document = tomllib.loads(plan.target.read_text(encoding="utf-8"))
        if not isinstance(document.get("project", {}), dict):
            raise ValueError("pyproject.toml: project must be a table")
        dependencies = deep_get(document, ["project", "dependencies"], default=[])
        if not isinstance(dependencies, list) or any(
            not isinstance(d, str) for d in dependencies
        ):
            raise ValueError(
                "pyproject.toml: project.dependencies must be a list of requirements"
            )
        names = {canonicalize_name(Requirement(d).name) for d in dependencies}
        return MatchResult(
            self.name in names,
            f"{self.name} in declared project.dependencies: {sorted(names)}",
        )
