"""Optional user-home Saucepan connection, independent of profile activation."""

import re
from dataclasses import dataclass
from pathlib import Path

from zuu.case5 import ConfinedPath, TargetState

from ..profiles import settings


@dataclass(frozen=True)
class Connection:
    marker: Path
    binary: Path | None
    order: tuple[str, ...]


def connection(home: Path) -> Connection | None:
    sources = settings(home).get("sources", {})
    if not isinstance(sources, dict):
        raise ValueError("sources.saucepan must belong to a sources table")
    if "saucepan" not in sources:
        return None
    data = sources["saucepan"]
    if not isinstance(data, dict) or set(data) - {"marker", "binary", "order"}:
        raise ValueError("sources.saucepan: invalid connection fields")

    def path(name, required=False):
        value = data.get(name)
        if value is None and not required and name not in data:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"sources.saucepan.{name} must be a nonblank path")
        result = Path(value)
        return result if result.is_absolute() else home / result

    marker, binary = path("marker", True), path("binary")
    order = data.get("order", [])
    if (
        not isinstance(order, list)
        or any(
            not isinstance(item, str) or not re.fullmatch(r"[0-9a-f]{64}", item)
            for item in order
        )
        or len(set(order)) != len(order)
    ):
        raise ValueError(
            "sources.saucepan.order must contain unique canonical source IDs"
        )
    # Inspect from the filesystem anchor to reject redirected ancestors as well.
    absolute = marker.absolute()
    ConfinedPath(absolute.relative_to(absolute.anchor).as_posix()).inspect(
        Path(absolute.anchor), allowed=(TargetState.FILE,)
    )
    return Connection(marker, binary, tuple(order))
