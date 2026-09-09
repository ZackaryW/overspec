"""Typed, optional variable documents; reads never initialize local state."""

import math
import tomllib
from collections.abc import Mapping

from .storage import read_bytes


def validate_values(values, *, origin="Variables", allow_null=True):
    if not isinstance(values, Mapping):
        raise ValueError(f"{origin}: vars must be a mapping")

    def scalar(value):
        return (
            type(value) in (str, int, bool)
            or type(value) is float
            and math.isfinite(value)
            or value is None
            and allow_null
        )

    for key, value in values.items():
        if not isinstance(key, str) or not (
            scalar(value)
            or isinstance(value, list)
            and all(scalar(item) for item in value)
        ):
            raise ValueError(
                f"{origin}: vars.{key} must be a finite scalar or scalar list"
            )


def load_variables(root, relative):
    origin = str(root / relative)
    raw = read_bytes(root, relative)
    if raw is None:
        return {}
    try:
        document = tomllib.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError(f"{origin}: invalid TOML: {exc}") from exc
    if document.keys() - {"vars"}:
        raise ValueError(
            f"{origin}: unknown fields {sorted(document.keys() - {'vars'})}"
        )
    values = document.get("vars", {})
    validate_values(values, origin=origin, allow_null=False)
    return values


def file_layers(root, prefix=""):
    return [
        load_variables(root, prefix + name) for name in (".vars.toml", ".current.toml")
    ]
