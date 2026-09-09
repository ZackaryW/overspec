from dataclasses import dataclass
import shutil

from .base import Assertion
from overspec.core.trait_system.models import MatchResult, fields, nonblank


@dataclass(frozen=True)
class WhichAssertion(Assertion):
    app: str

    @classmethod
    def parse(cls, data):
        fields(data, {"app"})
        return cls(nonblank(data["app"], "app"))

    def evaluate(self, context):
        found = shutil.which(self.app)
        return MatchResult(found is not None, f"{self.app}: {found or 'not found'}")
