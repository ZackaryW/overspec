"""Package the single authored default without importing runtime dependencies."""

import stat
import tomllib
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

AUTHORED = Path("openspec/.over/profile-default")


def regular_path(path):
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or (
        getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    ):
        raise ValueError(f"Redirected default profile path: {path}")
    return info


def documents(root):
    profile = root / AUTHORED
    for parent in (root / "openspec", root / "openspec/.over", profile):
        if not stat.S_ISDIR(regular_path(parent).st_mode):
            raise ValueError(f"Default profile directory required: {parent}")

    def visit(directory):
        for path in sorted(directory.iterdir()):
            if path.name in (".state", ".git", "__pycache__"):
                continue
            info = regular_path(path)
            if stat.S_ISDIR(info.st_mode):
                yield from visit(path)
            elif path.name.startswith("trait") and path.suffix == ".toml":
                if not stat.S_ISREG(info.st_mode):
                    raise ValueError(f"Regular trait document required: {path}")
                tomllib.loads(path.read_text(encoding="utf-8"))
                yield path

    result = list(visit(profile))
    if not result:
        raise ValueError(f"Default profile has no trait documents: {profile}")
    return result


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        root = Path(self.root)
        for path in documents(root):
            relative = path.relative_to(root / AUTHORED)
            destination = (
                Path("overspec/_bundled/profile-default") / relative
                if self.target_name == "wheel"
                else AUTHORED / relative
            )
            build_data["force_include"][str(path)] = destination.as_posix()
