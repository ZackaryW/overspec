"""Materialize complete packaged skill sources for native lifecycle calls."""

from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from importlib import metadata, resources
from pathlib import Path

from .package_assets import payload, resource_tree


@dataclass(frozen=True)
class SkillAsset:
    name: str
    origin: str
    version: str
    files: tuple[str, ...]


@dataclass(frozen=True)
class SkillSource:
    name: str
    path: Path
    origin: str


def skill_catalog():
    tree = resource_tree("skills", ".agents/skills")
    files = payload(tree)
    names = sorted(
        p.split("/")[0] for p in files if p.count("/") == 1 and p.endswith("/SKILL.md")
    )
    if not names:
        raise ValueError("Missing packaged skills")
    version = metadata.version("overspec")
    return tuple(
        SkillAsset(
            name,
            f"package:overspec/skills/{name}",
            version,
            tuple(p[len(name) + 1 :] for p in files if p.startswith(name + "/")),
        )
        for name in names
    )


@contextmanager
def materialize_skills(names):
    catalog = {s.name: s for s in skill_catalog()}
    if len(names) != len(set(names)) or set(names) - catalog.keys():
        raise ValueError("Unknown or duplicate packaged skill selection")
    tree = resource_tree("skills", ".agents/skills")
    with ExitStack() as stack:
        sources = []
        for name in names:
            path = stack.enter_context(resources.as_file(tree.joinpath(name)))
            # Confirm extraction/source completeness before handing it to ZuAT.
            if set(payload(path)) != set(catalog[name].files):
                raise ValueError(f"Incomplete skill payload: {name}")
            sources.append(SkillSource(name, path, catalog[name].origin))
        yield tuple(sources)
