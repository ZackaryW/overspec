"""Confined optional manifest reads; no installation or configuration execution."""

import json
from pathlib import Path
import tomllib

from ruamel.yaml import YAML
from zuu.case2 import FileSystemSnapshot
from zuu.case5 import ConfinedPath, TargetState


class Evidence:
    def __init__(self, project: Path):
        self.project = project

    def _plan(self, relative, kind):
        try:
            return ConfinedPath(relative).inspect(
                self.project, allowed=(TargetState.ABSENT, kind)
            )
        except (ValueError, OSError) as exc:
            raise ValueError(f"{relative}: {exc}") from exc

    def file(self, relative):
        plan = self._plan(relative, TargetState.FILE)
        plan.revalidate()
        return plan.state == TargetState.FILE

    def document(self, relative, format):
        plan = self._plan(relative, TargetState.FILE)
        if plan.state == TargetState.ABSENT:
            return None
        try:
            plan.revalidate()
            content = plan.target.read_text(encoding="utf-8")
            plan.revalidate()
            parsers = {"toml": tomllib.loads, "json": json.loads,
                       "yaml": YAML(typ="safe").load}
            document = parsers[format](content)
            if not isinstance(document, dict):
                raise ValueError("manifest must be a mapping")
            return document
        except Exception as exc:
            raise ValueError(f"{relative}: {exc}") from exc

    def dart_sources(self, relative):
        plan = self._plan(relative, TargetState.DIRECTORY)
        if plan.state == TargetState.ABSENT:
            return False
        try:
            plan.revalidate()
            snapshot = FileSystemSnapshot.capture([plan.target])
            plan.revalidate()
            return any(Path(entry.relative_path).suffix == ".dart"
                       for entry in snapshot.files)
        except (ValueError, OSError) as exc:
            raise ValueError(f"{relative}: {exc}") from exc
