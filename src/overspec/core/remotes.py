"""Public GitHub retrieval with independently validated profile publications."""

import os
import re
import tempfile
from pathlib import Path

from zuu.case2 import FileSystemSnapshot
from zuu.case5 import ConfinedPath, TargetState
from zuu.case12 import GitHubSubpath

from . import storage
from .trait_system.evaluator import validate_references
from .trait_system.sources import compose, parse_document


def profile_name(name):
    if not isinstance(name, str) or not name or "/" in name or "\\" in name:
        raise ValueError("Profile name must be one portable path segment")
    ConfinedPath("profile-" + name)
    ConfinedPath(name)
    return name


def source_api(source):
    allowed = {"kind", "owner", "repository", "path", "branch", "commit"}
    if (
        not isinstance(source, dict)
        or source.get("kind") != "github"
        or source.keys() - allowed
    ):
        raise ValueError(
            "Unsupported profile source; use a structured public GitHub directory"
        )
    if not {"owner", "repository", "path"} <= source.keys():
        raise ValueError("GitHub source requires owner, repository, and path")
    return GitHubSubpath(**{k: v for k, v in source.items() if k != "kind"})


def material(root):
    # Snapshot captures bytes and rejects nonregular/redirected descendants.
    snapshot = FileSystemSnapshot.capture([root])
    return {
        e.relative_path: e.content for e in snapshot.entries if e.content is not None
    }


def material_digest(files):
    return storage.digest({k: v.hex() for k, v in files.items()})


def pull_profile(home, name, source, *, client=None):
    from .profiles import profile_directories, require_profiles, trait_files

    require_profiles(home)

    profile_name(name)
    api = source_api(source)
    home.mkdir(parents=True, exist_ok=True)
    if name in profile_directories(home):
        raise ValueError(f"Local/remote profile name collision: {name}")
    base = f".state/remotes/{name}"
    previous = storage.read_bytes(home, base + "/source.json")
    if (
        previous is not None
        and storage.read_json(home, base + "/source.json") != source
    ):
        raise ValueError(
            "A registered remote source cannot change; choose another profile name"
        )
    storage.atomic_write(home, base + "/source.json", storage.encoded(source))
    download = (
        ConfinedPath(base + "/download")
        .inspect(home, allowed=(TargetState.DIRECTORY, TargetState.ABSENT))
        .target
    )
    result = api.sync(download, client=client)
    trait_files(download)  # Validate the source traversal before observation.
    files = material(download)
    paths = [
        download / relative
        for relative in sorted(files)
        if Path(relative).name.startswith("trait")
        and Path(relative).suffix == ".toml"
        and ".state" not in Path(relative).parts
    ]
    declarations = [
        t
        for p in paths
        for t in parse_document(
            files[p.relative_to(download).as_posix()].decode("utf-8"), str(p)
        )
    ]
    effective, _ = compose(declarations, [])
    validate_references(effective)
    revision = material_digest(files)
    destination = base + "/revisions/" + revision
    plan = ConfinedPath(destination).inspect(
        home, allowed=(TargetState.DIRECTORY, TargetState.ABSENT)
    )
    if plan.state == TargetState.DIRECTORY:
        if material_digest(material(plan.target)) != revision:
            raise ValueError(
                "Corrupt published remote revision; restore it before refresh"
            )
    else:
        plan.target.parent.mkdir(parents=True, exist_ok=True)
        plan = ConfinedPath(destination).inspect(home, allowed=(TargetState.ABSENT,))
        with tempfile.TemporaryDirectory(
            prefix=".staging-", dir=plan.target.parent
        ) as temporary:
            stage = Path(temporary)
            relative_stage = stage.relative_to(home).as_posix()
            ConfinedPath(relative_stage).inspect(home, allowed=(TargetState.DIRECTORY,))
            for relative, content in files.items():
                storage.atomic_write(home, relative_stage + "/" + relative, content)
            if material_digest(material(stage)) != revision:
                raise ValueError("Staged profile changed during publication")
            plan.revalidate()
            os.replace(stage, plan.target)
    if material_digest(material(download)) != revision:
        raise ValueError("Downloaded profile changed during validation")
    metadata = {"source": source, "commit": result.commit, "revision": revision}
    storage.atomic_write(home, base + "/current.json", storage.encoded(metadata))
    return metadata


def update_profile(home, name, *, client=None):
    from .profiles import require_profiles

    require_profiles(home)
    profile_name(name)
    source = storage.read_json(home, f".state/remotes/{name}/source.json")
    return pull_profile(home, name, source, client=client)


def remote_profile(home, name):
    profile_name(name)
    if not home.exists():
        return None
    relative = f".state/remotes/{name}/current.json"
    if storage.read_bytes(home, relative) is None:
        return None
    metadata = storage.read_json(home, relative)
    revision = metadata.get("revision")
    if not isinstance(revision, str) or not re.fullmatch("[0-9a-f]{64}", revision):
        raise ValueError(f"Invalid remote revision for {name}")
    target = (
        ConfinedPath(f".state/remotes/{name}/revisions/{revision}")
        .inspect(home, allowed=(TargetState.DIRECTORY,))
        .target
    )
    if material_digest(material(target)) != revision:
        raise ValueError(
            f"Corrupt remote profile {name}; refresh or restore its revision"
        )
    return target


def remote_profiles(home):
    from .profiles import require_profiles

    require_profiles(home)
    plan = ConfinedPath(".state/remotes").inspect(
        home, allowed=(TargetState.DIRECTORY, TargetState.ABSENT)
    )
    if plan.state == TargetState.ABSENT:
        return {}
    result = {}
    for entry in sorted(plan.target.iterdir()):
        target = remote_profile(home, entry.name)
        if target is not None:
            result[entry.name] = target
    return result
