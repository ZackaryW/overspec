"""Project composition lifecycle; configuration projection is a separate boundary."""

import difflib
import os
from dataclasses import replace
from pathlib import Path

from zuu.case2 import FileSystemSnapshot
from zuu.case5 import ConfinedPath

from . import storage
from .profiles import select_profile, settings, trait_files
from .trait_system.evaluator import evaluate, validate_references
from .trait_system.rendering import VARIABLE, variables
from .trait_system.sources import compose, parse_document
from .variables import file_layers


class Project:
    def __init__(self, root=None, home=None):
        self.root = Path(root or Path.cwd()).resolve()
        self.home = Path(
            home or os.environ.get("OVERSPEC_HOME", Path.home() / ".overspec")
        ).resolve()
        self.over = self.root / "openspec/.over"
        self.state = self.root / storage.STATE_PATH

    def source_inputs(self):
        from .external.discovery import discover

        ConfinedPath("openspec/.over").inspect(self.root)
        catalog = discover(self.home)
        selected, directory = select_profile(
            self.root, self.home, external=catalog.profiles
        )
        profile_files = trait_files(directory) if directory else []
        local_files = trait_files(self.over, local=True)
        profile_identities = {(p.stat().st_dev, p.stat().st_ino) for p in profile_files}
        local_files = [
            p
            for p in local_files
            if (p.stat().st_dev, p.stat().st_ino) not in profile_identities
        ]
        layers = [
            profile_files,
            *catalog.layers,
            trait_files(self.home, local=True),
            local_files,
        ]
        return catalog, selected, directory, layers

    def source_evidence(self, inputs=None):
        catalog, selected, directory, layers = inputs or self.source_inputs()
        paths = list(dict.fromkeys(p for layer in layers for p in layer))
        for root in (self.home, self.over):
            if root.exists() and storage.read_bytes(root, "config.toml") is not None:
                paths.append(root / "config.toml")
        return (
            selected,
            str(directory),
            catalog.evidence,
            FileSystemSnapshot.capture(paths) if paths else None,
        )

    def inventory(self, *, inputs=None):
        catalog, selected, directory, layers = inputs or self.source_inputs()
        files = list(dict.fromkeys(p for layer in layers for p in layer))
        observed = FileSystemSnapshot.capture(files) if files else None
        contents = (
            {observed.roots[e.root_index]: e.content for e in observed.entries}
            if observed
            else {}
        )

        def parse(paths):
            return [
                replace(t, provenance=catalog.describe(p)[1])
                for p in paths
                for t in parse_document(
                    contents[p].decode("utf-8"), catalog.describe(p)[0]
                )
            ]

        effective, overridden = compose(*(parse(paths) for paths in layers))
        validate_references(effective)
        base = variables(
            self.configured_variables(), *file_layers(self.root, "openspec/.over/")
        )
        return (
            effective,
            overridden,
            [selected, catalog.describe(directory)[0] if directory else None],
            base,
        )

    def configured_variables(self):
        return variables(
            settings(self.home).get("vars", {}), settings(self.over).get("vars", {})
        )

    def variable_evidence(self):
        names = ("openspec/.over/.vars.toml", "openspec/.over/.current.toml")
        present = tuple(
            name for name in names if storage.read_bytes(self.root, name) is not None
        )
        return present, FileSystemSnapshot.capture(
            [self.root / name for name in present]
        ) if present else None

    @staticmethod
    def compatibility(traits, selection, base):
        compiled = [t for t in traits if t.phase == "compiletime-trait"]
        keys = {
            m.group(1)
            for t in compiled
            for m in VARIABLE.finditer(t.body)
            if m.group(1)
        }
        return storage.digest(
            {
                "traits": [
                    {k: v for k, v in t.record().items() if k != "provenance"}
                    for t in compiled
                ],
                "profile": selection,
                "vars": {k: base[k] for k in sorted(keys) if k in base},
            }
        )

    def initialize(self, *, update=False, values=None):
        if not update and storage.has_compilation(self.root):
            raise ValueError("Compilation already exists; use update")
        observed_state = storage.read_bytes(self.root, storage.STATE_PATH)
        state = storage.read_state(self.root, missing_ok=True)
        variable_evidence = self.variable_evidence()
        sources = self.source_inputs()
        source_evidence = self.source_evidence(sources)
        traits, _, selection, base = self.inventory(inputs=sources)
        inputs = variables(base, values or {})
        signature = self.compatibility(traits, selection, base)
        result = evaluate(
            [t for t in traits if t.phase == "compiletime-trait"],
            self.root,
            values=inputs,
        )
        snapshot = {
            "version": 1,
            "root": str(self.root),
            "compatibility": signature,
            "traits": [t.record() for t in traits if t.phase == "compiletime-trait"],
            "inputs": inputs,
            "static": result,
        }

        def recheck():
            if self.source_evidence() != source_evidence:
                raise ValueError("Sources changed during compilation; retry update")
            if self.variable_evidence() != variable_evidence:
                raise ValueError(
                    "Variable files changed during compilation; retry update"
                )
            current = self.inventory()
            if self.compatibility(current[0], current[2], current[3]) != signature:
                raise ValueError("Sources changed during compilation; retry update")

        recheck()
        state["compilation"] = storage.section(snapshot)
        storage.save_state(self.root, state, expected=observed_state, recheck=recheck)
        return state["compilation"]["id"]

    def prepare(self, *, values=None, inputs=None):
        sources = inputs or self.source_inputs()
        traits, overridden, selection, base = self.inventory(inputs=sources)
        saved = storage.read_state(self.root)["compilation"]
        if saved is None:
            raise ValueError("Missing compilation; run init/update")
        compiled = saved["data"]
        if compiled.get("compatibility") != self.compatibility(traits, selection, base):
            raise ValueError(
                "Compile-time sources, inputs, or profile changed; run update"
            )
        inputs = variables(base, values or {})
        result = evaluate(
            [t for t in traits if t.phase == "trait"],
            self.root,
            prior=compiled["static"],
            values=inputs,
        )
        return {
            "version": 2,
            "root": str(self.root),
            "profile": selection,
            "compilation": saved["id"],
            "traits": [t.record() for t in traits],
            "overridden": [
                {
                    "name": t.name,
                    "origin": t.origin,
                    "phase": t.phase,
                    "attach": t.attach,
                    **({"provenance": t.provenance} if t.provenance else {}),
                }
                for t in overridden
            ],
            "variables": inputs,
            "runtime_defaults": variables(self.configured_variables(), values or {}),
            "static": result,
            "sources": sources[0].excluded,
        }

    def evidence(self, *, config=True, inputs=None):
        """Observe inventory and publication inputs without reevaluating assertions."""
        sources = self.source_evidence(inputs)
        paths = []
        for root, relative in (
            (self.root, "openspec/.over/config.toml"),
            (self.root, storage.STATE_PATH),
            *(
                (
                    [
                        (self.root, "openspec/config.yaml"),
                        (self.root, "openspec/config.yml"),
                    ]
                )
                if config
                else []
            ),
        ):
            if storage.read_bytes(root, relative) is not None:
                paths.append(root / relative)
        if (
            self.home.exists()
            and storage.read_bytes(self.home, "config.toml") is not None
        ):
            paths.append(self.home / "config.toml")
        storage.read_state(self.root)
        return (
            sources,
            FileSystemSnapshot.capture(paths),
            self.variable_evidence(),
        )

    def sync(self, *, dry_run=False, values=None):
        from .projection import config_target, owned_fingerprint, project_yaml
        from .resolution import contributions

        path = config_target(self.root)
        inputs = self.source_inputs()
        before = self.evidence(inputs=inputs)
        sources_before = self.evidence(config=False, inputs=inputs)
        observed_state = storage.read_bytes(self.root, storage.STATE_PATH)
        state = storage.read_state(self.root)
        original = path.read_bytes().decode("utf-8")
        bundle = self.prepare(values=values, inputs=inputs)
        identity = storage.digest(bundle)
        candidate, changed = project_yaml(original, contributions(bundle, identity))
        result = {
            "path": str(path),
            "resolution": identity,
            "changed": changed,
            "candidate": candidate,
            "diff": "".join(
                difflib.unified_diff(
                    original.splitlines(keepends=True),
                    candidate.splitlines(keepends=True),
                    fromfile=str(path),
                    tofile=str(path),
                )
            ),
            "ownership": "Sync replaces manual edits in context, rules, and apply/archive guidance.",
        }

        def recheck():
            if self.evidence() != before:
                raise ValueError(
                    "Source, activation, compilation, or configuration changed during sync; retry"
                )

        recheck()
        if dry_run:
            return result
        if changed:
            storage.atomic_write(
                self.root,
                path.relative_to(self.root).as_posix(),
                candidate.encode("utf-8"),
                recheck=recheck,
            )
        else:
            recheck()
        receipt = {
            "resolution": identity,
            "fingerprint": owned_fingerprint(candidate),
        }
        state["resolution"] = storage.section(bundle)
        state["sync"] = receipt

        def recheck_saved():
            if self.evidence(
                config=False
            ) != sources_before or path.read_bytes() != candidate.encode("utf-8"):
                raise ValueError("Source or configuration changed during sync; retry")

        try:
            storage.save_state(
                self.root, state, expected=observed_state, recheck=recheck_saved
            )
        except (OSError, ValueError) as exc:
            raise ValueError(
                f"Sync state publication failed; configuration may already have changed. Retry sync. {exc}"
            ) from exc
        return result
