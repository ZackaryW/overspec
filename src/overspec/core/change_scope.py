"""Validation of explicitly selected local or external OpenSpec change roots."""

from pathlib import Path

from ruamel.yaml import YAML
from zuu.case5 import ConfinedPath, TargetState

from .storage import read_bytes


def change_root(path):
    # Inspect before resolving: resolving first would hide redirected components.
    candidate = Path(path).absolute()
    plan = ConfinedPath(candidate.relative_to(candidate.anchor).as_posix()).inspect(
        Path(candidate.anchor), allowed=(TargetState.DIRECTORY,)
    )
    raw = read_bytes(plan.target, ".openspec.yaml")
    try:
        metadata = (
            YAML(typ="safe").load(raw.decode("utf-8")) if raw is not None else None
        )
        if (
            not isinstance(metadata, dict)
            or not isinstance(metadata.get("schema"), str)
            or not metadata["schema"].strip()
        ):
            raise ValueError("expected a schema mapping")
    except Exception as exc:
        raise ValueError(
            f"{candidate}: invalid or missing OpenSpec .openspec.yaml metadata: {exc}"
        ) from exc
    return plan.target
