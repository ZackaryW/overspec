from dataclasses import dataclass
import json

from .base import Assertion
from overspec.core.trait_system.models import MatchResult, fields, nonblank


@dataclass(frozen=True)
class RuntimeContextMatchAssertion(Assertion):
    key: str
    value: object
    runtime_only = True

    @classmethod
    def parse(cls, data):
        fields(data, {"kv"})
        expression = nonblank(data["kv"], "kv")
        if "=" not in expression:
            raise ValueError("kv must contain key=value")
        key, value = expression.split("=", 1)
        nonblank(key, "kv key")
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = value
        if isinstance(parsed, (list, dict)):
            raise ValueError("kv value must be scalar")
        return cls(key, parsed)

    def evaluate(self, context):
        actual = context.runtime.get(self.key)
        matched = (
            self.key in context.runtime
            and type(actual) is type(self.value)
            and actual == self.value
        )
        return MatchResult(matched, f"Exact typed match for {self.key}: {matched}")
