"""Confined trait discovery and explicit profile activation."""

import os
import tempfile
import tomllib
from pathlib import Path

import tomlkit
from zuu.case5 import ConfinedPath, TargetState


def profile_directories(root: Path) -> dict[str, Path]:
    if not root.exists():
        return {}
    result = {}
    for path in sorted(root.iterdir()):
        if path.name.startswith("profile-") and path.name[8:]:
            plan = ConfinedPath(path.name).inspect(root)
            if plan.state == TargetState.DIRECTORY:
                result[path.name[8:]] = path
    return result


def trait_files(root: Path, *, local: bool = False) -> list[Path]:
    if not root.exists():
        return []
    files = []
    seen = set()

    def visit(directory):
        for path in sorted(directory.iterdir()):
            if path.name in (".state", ".git") or (
                local and path.name.startswith("profile-")
            ):
                continue
            plan = ConfinedPath(path.relative_to(root).as_posix()).inspect(root)
            if plan.state == TargetState.DIRECTORY:
                visit(path)
            elif (
                plan.state == TargetState.FILE
                and path.name.startswith("trait")
                and path.suffix == ".toml"
            ):
                stat = path.stat()
                identity = (stat.st_dev, stat.st_ino)
                if identity not in seen:
                    files.append(path)
                    seen.add(identity)

    visit(root)
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())


def settings(root: Path) -> dict:
    if not root.exists():
        return {}
    plan = ConfinedPath("config.toml").inspect(
        root, allowed=(TargetState.FILE, TargetState.ABSENT)
    )
    if plan.state == TargetState.ABSENT:
        return {}
    data = tomllib.loads(plan.target.read_text(encoding="utf-8"))
    if not isinstance(data.get("vars", {}), dict):
        raise ValueError(f"{plan.target}: vars must be a mapping")
    return data


def profile_settings(home):
    data = settings(home).get("profiles", {})
    if not isinstance(data, dict):
        raise ValueError("profiles must be a table")
    if type(data.get("enabled", False)) is not bool:
        raise ValueError("profiles.enabled must be boolean")
    return data


def profiles_enabled(home):
    return profile_settings(home).get("enabled", False)


def require_profiles(home):
    if not profiles_enabled(home):
        raise ValueError("Profile mode is off; run overspec profile activate")


def selected_name(home):
    data = profile_settings(home)
    if not data.get("enabled", False):
        return "default", False
    name = os.environ.get("OVERSPEC_PROFILE", data.get("selected"))
    if name is None:
        return "default", False

    if not isinstance(name, str) or not name.strip():
        raise ValueError("Selected profile must be a nonblank name")
    return profile_name(name), True


def profile_directory(root, name):
    if not root.exists():
        return None
    plan = ConfinedPath("profile-" + name).inspect(
        root, allowed=(TargetState.DIRECTORY, TargetState.ABSENT)
    )
    return plan.target if plan.state == TargetState.DIRECTORY else None


def profile_name(name):
    if not isinstance(name, str) or not name or "/" in name or "\\" in name:
        raise ValueError("Profile name must be one portable path segment")
    ConfinedPath("profile-" + name)
    ConfinedPath(name)
    return name


def select_profile(project: Path, home: Path):
    from .source_plan import profile_catalog

    name, _ = selected_name(home)
    if name not in profile_catalog(project, home):
        raise ValueError(f"Selected profile is missing: {name}")
    return name


def toggle_profiles(home):
    enabled = not profiles_enabled(home)
    _write_profiles(home, {"enabled": enabled})
    return enabled


def use_profile(project: Path, home: Path, name: str):

    require_profiles(home)
    profile_name(name)
    from .source_plan import profile_catalog

    if name not in profile_catalog(project, home):
        raise ValueError(f"Selected profile is missing: {name}")
    _write_profiles(home, {"selected": name})


def _write_profiles(root, changes):
    root.mkdir(parents=True, exist_ok=True)
    plan = ConfinedPath("config.toml").inspect(
        root, allowed=(TargetState.FILE, TargetState.ABSENT)
    )
    doc = (
        tomlkit.parse(plan.target.read_text(encoding="utf-8"))
        if plan.state == TargetState.FILE
        else tomlkit.document()
    )
    table = doc.setdefault("profiles", tomlkit.table())
    table.update(changes)
    fd, temp = tempfile.mkstemp(prefix=".activation-", dir=root)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(tomlkit.dumps(doc))
        plan.revalidate()
        os.replace(temp, plan.target)
    finally:
        Path(temp).unlink(missing_ok=True)
