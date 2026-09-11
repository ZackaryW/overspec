"""Top-level-first repository layouts and stable external source priority."""

from dataclasses import dataclass, field

from zuu.case2 import FileSystemSnapshot
from zuu.case5 import ConfinedPath, TargetState

from ..profiles import profile_directories, trait_files
from ..storage import digest
from . import adapter
from .settings import connection


@dataclass
class Catalog:
    layers: list = field(default_factory=list)
    profiles: dict = field(default_factory=dict)
    profile_layers: list = field(default_factory=list)
    profile_origins: dict = field(default_factory=dict)
    repositories: list = field(default_factory=list)
    excluded: list = field(default_factory=list)
    evidence: object = None

    def describe(self, path):
        for repo in self.repositories:
            if path.is_relative_to(repo.root):
                relative = path.relative_to(repo.root)
                layout = (
                    relative.parts[0]
                    if relative.parts[0].startswith("over-")
                    else "openspec/.over"
                )
                return repo.origin(path), repo.provenance(path, layout)
        return str(path), None


def category(root, name):
    top = ConfinedPath(name).inspect(
        root, allowed=(TargetState.DIRECTORY, TargetState.ABSENT)
    )
    selected = (
        top
        if top.state != TargetState.ABSENT
        else ConfinedPath("openspec/.over").inspect(
            root, allowed=(TargetState.DIRECTORY, TargetState.ABSENT)
        )
    )
    return selected.target if selected.state == TargetState.DIRECTORY else None


def discover(home, *, client_factory=None):
    configured = connection(home)
    if configured is None:
        return Catalog()
    client = (client_factory or adapter.create_client)(configured)
    repositories, excluded, observed = adapter.repositories(client)
    order = {key: i for i, key in enumerate(configured.order)}
    repositories.sort(
        key=lambda repo: (
            repo.artifact["source_id"] in order,
            order.get(repo.artifact["source_id"], -1),
            repo.artifact["source_id"],
        )
    )
    result = Catalog(repositories=repositories, excluded=excluded)
    eligible = {repo.artifact["source_id"] for repo in repositories}
    for key in configured.order:
        if key not in eligible and not any(
            item["source_id"] == key for item in excluded
        ):
            result.excluded.append(
                {
                    "source_id": key,
                    "reason": "Configured priority is inactive; source is absent or filtered out of the overspec view",
                }
            )
    layouts = []
    for repo in repositories:
        standalone = category(repo.root, "over-traits")
        profiles = category(repo.root, "over-profiles")
        files = trait_files(standalone, local=True) if standalone else []
        result.layers.append(files)
        candidates = profile_directories(profiles) if profiles else {}
        result.profile_layers.append(candidates)
        for name, path in candidates.items():
            result.profiles.setdefault(name, []).append(path)
            origin, metadata = result.describe(path)
            result.profile_origins.setdefault(name, []).append(
                {"origin": origin, **metadata}
            )
        layouts.append([str(repo.root), str(standalone), str(profiles)])
    # Secrets stay inside transient evidence, never serialized into resolutions.
    result.evidence = (
        observed,
        digest(layouts),
        configured,
        FileSystemSnapshot.capture([configured.marker]),
    )
    return result
