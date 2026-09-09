"""Read active change roots from the companion CLI, keeping its store selection."""

import json
import re
import shutil
from pathlib import Path

from zuu.case3 import run_process

from .change_scope import change_root


def discover_changes(root, *, store=None, runner=run_process):
    executable = shutil.which("openspec")
    if not executable:
        raise ValueError(
            "OpenSpec CLI is required for change discovery; supply --change-root for exact targets"
        )
    suffix = ["--store", store] if store is not None else []

    def query(*args):
        result = runner([executable, *args, "--json", *suffix], root)
        try:
            if result.returncode:
                raise ValueError(result.stderr.strip() or f"exit {result.returncode}")
            value = json.loads(result.stdout)
            if not isinstance(value, dict):
                raise ValueError("expected an object")
            return value
        except ValueError as exc:
            raise ValueError(f"OpenSpec {args[0]} failed: {exc}") from exc

    items = query("list").get("changes")
    if not isinstance(items, list):
        raise ValueError("OpenSpec list omitted changes array")
    roots = []
    for item in items:
        name = item.get("name") if isinstance(item, dict) else None
        if not isinstance(name, str) or not re.fullmatch(
            r"[a-zA-Z0-9][a-zA-Z0-9_-]*", name
        ):
            raise ValueError("OpenSpec list returned an invalid change name")
        if item.get("status") == "archived":
            continue
        status = query("status", "--change", name)
        path = status.get("changeRoot")
        if (
            status.get("changeName") != name
            or not isinstance(path, str)
            or not Path(path).is_absolute()
        ):
            raise ValueError("OpenSpec status returned an invalid change root or name")
        roots.append(change_root(path))
    return list(dict.fromkeys(roots))
