"""Read release assets or the imported distribution's authored editable tree."""

import tomllib
from importlib import metadata, resources
from pathlib import Path

from zuu.case5 import ConfinedPath, TargetState

EXCLUDED = {
    ".git",
    "__pycache__",
    ".state",
    ".pytest_cache",
    ".current.toml",
    ".state.json",
    ".DS_Store",
}


def resource_tree(category, authored):
    module = resources.files("overspec")
    if (
        isinstance(module, Path)
        and module.name == "overspec"
        and module.parent.name == "src"
    ):
        root = module.parent.parent
        project = tomllib.loads(
            ConfinedPath("pyproject.toml")
            .inspect(root, allowed=(TargetState.FILE,))
            .target.read_text(encoding="utf-8")
        )
        if project.get("project", {}).get("name") != "overspec":
            raise ValueError("Invalid Overspec editable metadata")
        return (
            ConfinedPath(authored)
            .inspect(root, allowed=(TargetState.DIRECTORY,))
            .target
        )
    tree = module.joinpath("_bundled", *category.split("/"))
    prefix = f"overspec/_bundled/{category}/"
    expected = {
        str(p)[len(prefix) :]
        for p in metadata.files("overspec") or ()
        if str(p).startswith(prefix)
    }
    if not expected or set(payload(tree)) != expected:
        raise ValueError(f"Missing or unexpected packaged {category} resources")
    return tree


def payload(tree):
    result = {}

    def visit(directory, prefix=""):
        for item in sorted(directory.iterdir(), key=lambda p: p.name):
            if item.name in EXCLUDED:
                continue
            relative = prefix + item.name
            if isinstance(tree, Path):
                ConfinedPath(relative).inspect(
                    tree, allowed=(TargetState.FILE, TargetState.DIRECTORY)
                )
            if item.is_dir():
                visit(item, relative + "/")
            elif item.is_file():
                result[relative] = item.read_bytes()
            else:
                raise ValueError(f"Nonregular package payload: {relative}")

    visit(tree)
    return result
