"""Select a profile name, then compose contributors in source order."""

from dataclasses import dataclass

from zuu.case5 import ConfinedPath

from . import bundled
from .external.discovery import discover
from .profiles import profile_directories, selected_name, trait_files
from .source_documents import DocumentReader


def workspace_contributor(path):
    return {"kind": "workspace", "path": str(path), "origin": str(path)}


def profile_catalog(project, home, *, external=None, package=None):
    catalog = discover(home) if external is None else external
    package = bundled.default_profile() if package is None else package
    result = {"default": [package.contributor()]}
    for name, contributors in catalog.profile_origins.items():
        result.setdefault(name, []).extend(
            {"kind": "repository", **c} for c in contributors
        )
    if project.exists():
        ConfinedPath("openspec/.over").inspect(project)
    for name, path in profile_directories(project / "openspec/.over").items():
        result.setdefault(name, []).append(workspace_contributor(path))
    return result


@dataclass
class SourcePlan:
    selected: str
    layers: list
    contributors: list
    excluded: list
    evidence: tuple


def compose_plan(project, home):
    ConfinedPath("openspec/.over").inspect(project)
    catalog = discover(home)
    package = bundled.default_profile()
    profiles = profile_catalog(project, home, external=catalog, package=package)
    selected, _ = selected_name(home)
    if selected not in profiles:
        raise ValueError(f"Selected profile is missing: {selected}")
    reader = DocumentReader()
    layers = [package.documents(reader)] if selected == "default" else []

    def source_layers(profile, standalone, describe):
        paths = trait_files(profile) if profile else []
        identities = {(p.stat().st_dev, p.stat().st_ino) for p in paths}
        loose = [
            p
            for p in standalone
            if (p.stat().st_dev, p.stat().st_ino) not in identities
        ]
        layers.extend((reader.read(paths, describe), reader.read(loose, describe)))

    for names, standalone in zip(catalog.profile_layers, catalog.layers, strict=True):
        source_layers(names.get(selected), standalone, catalog.describe)
    over = project / "openspec/.over"
    source_layers(
        profile_directories(over).get(selected),
        trait_files(over, local=True),
        lambda p: (str(p), {"kind": "workspace", "path": str(p)}),
    )
    contributors = profiles[selected]
    return SourcePlan(
        selected,
        layers,
        contributors,
        catalog.excluded,
        (catalog.evidence, contributors, tuple(reader.evidence)),
    )
