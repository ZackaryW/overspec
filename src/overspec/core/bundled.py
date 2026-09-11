"""Read the installed default, or its single authored editable source."""

import tomllib
from dataclasses import dataclass
from importlib import metadata, resources
from pathlib import Path

from zuu.case5 import ConfinedPath, TargetState

from .profiles import trait_files
from .source_documents import Document

PREFIX = "overspec/_bundled/profile-default/"
ORIGIN = "package:overspec/profile-default"


@dataclass
class BundledProfile:
    root: object
    version: str
    expected: tuple[str, ...] | None = None

    def contributor(self):
        return {
            "kind": "package",
            "package": "overspec",
            "version": self.version,
            "profile": "default",
            "origin": ORIGIN,
            "path": ORIGIN,
        }

    def describe(self, relative):
        return f"{ORIGIN}/{relative}", {**self.contributor(), "path": relative}

    def documents(self, reader):
        try:
            if isinstance(self.root, Path):
                paths = trait_files(self.root)
                relative = tuple(p.relative_to(self.root).as_posix() for p in paths)
                self.check_inventory(relative)
                return reader.read(
                    paths, lambda p: self.describe(p.relative_to(self.root).as_posix())
                )
            paths = []

            def visit(root, prefix=""):
                for item in sorted(root.iterdir(), key=lambda p: p.name):
                    if item.name in (".state", ".git"):
                        continue
                    name = prefix + item.name
                    if item.is_dir():
                        visit(item, name + "/")
                    elif item.name.startswith("trait") and item.name.endswith(".toml"):
                        paths.append((name, item))

            visit(self.root)
            self.check_inventory(tuple(name for name, _ in paths))
            result = [
                Document(
                    self.describe(name)[0], item.read_bytes(), self.describe(name)[1]
                )
                for name, item in paths
            ]
            reader.evidence.append(tuple((d.origin, d.content) for d in result))
            return result
        except (OSError, ValueError) as exc:
            raise ValueError(f"Overspec package default is unavailable: {exc}") from exc

    def check_inventory(self, paths):
        if not paths or (
            self.expected is not None and set(paths) != set(self.expected)
        ):
            raise ValueError("Missing or unexpected packaged default trait documents")


def default_profile():
    module = resources.files("overspec")
    version = metadata.version("overspec")
    # Editable development is identified from the imported module, never the cwd.
    if (
        isinstance(module, Path)
        and module.name == "overspec"
        and module.parent.name == "src"
    ):
        checkout = module.parent.parent
        plan = ConfinedPath("pyproject.toml").inspect(
            checkout, allowed=(TargetState.FILE,)
        )
        project = tomllib.loads(plan.target.read_text(encoding="utf-8"))
        if project.get("project", {}).get("name") != "overspec":
            raise ValueError("Invalid Overspec editable project metadata")
        root = (
            ConfinedPath("openspec/.over/profile-default")
            .inspect(checkout, allowed=(TargetState.DIRECTORY,))
            .target
        )
        return BundledProfile(root, version)
    expected = tuple(
        str(p)[len(PREFIX) :]
        for p in (metadata.files("overspec") or ())
        if str(p).startswith(PREFIX)
    )
    return BundledProfile(
        module.joinpath("_bundled", "profile-default"), version, expected
    )
