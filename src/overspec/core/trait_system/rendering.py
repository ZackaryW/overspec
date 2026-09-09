import json
import math
import re

from zuu.case8 import LayeredMapping
from ..variables import validate_values


VARIABLE = re.compile(r"\$\$|\$\{([^{}]+)\}")


def variables(*layers):
    for layer in layers:
        validate_values(layer)
    return LayeredMapping(json_maps=[json.dumps(layer) for layer in layers]).to_dict()


def render(body, values):
    def replace(match):
        if match.group(0) == "$$":
            return "$"
        key = match.group(1)
        if key not in values:
            raise ValueError(f"Missing body variable: {key}")
        value = values[key]
        if type(value) not in (str, int, float, bool, type(None)):
            raise ValueError(f"Body variable must be scalar: {key}")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"Body variable must be finite: {key}")
        return value if isinstance(value, str) else json.dumps(value)

    result = VARIABLE.sub(replace, body)
    if "<!-- over:" in result or "# over:" in result:
        raise ValueError("Rendered body contains reserved source marker")
    return result
