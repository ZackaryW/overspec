import shutil

import pytest
from conftest import declaration, source

from overspec.core.trait_system.sources import parse_document


def test_runtime_group_boundaries_and_early_context_rejected():
    from overspec.core.trait_system.evaluator import validate_references

    for text in (
        declaration(
            "early",
            **{"assert": [{"type": "runtime-context-match", "kv": "flag=true"}]},
        ),
        declaration(
            "a",
            "runtime-trait",
            **{"actions": [{"type": "remove-trait", "trait": "b"}]},
        )
        + declaration("b"),
        declaration(
            "a", "runtime-trait", **{"assert": [{"type": "loaded-trait", "trait": "b"}]}
        )
        + declaration("b", "runtime-trait", attach="rules.proposal"),
    ):
        with pytest.raises(ValueError, match="runtime|Runtime"):
            validate_references(parse_document(text, "fixture"))


def test_evaluator_accepts_new_registered_assertion(tmp_path):
    from overspec.core.assertions.base import Assertion
    from overspec.core.trait_system.evaluator import evaluate
    from overspec.core.trait_system.models import MatchResult
    from overspec.core.trait_system.registry import builtins

    class Custom(Assertion):
        @classmethod
        def parse(cls, data):
            return cls()

        def evaluate(self, context):
            return MatchResult(True, "custom behavior")

    registry = builtins()
    registry.register_assertion("custom", Custom)
    traits = parse_document(
        declaration("custom", **{"assert": [{"type": "custom"}]}), "fixture", registry
    )
    assert evaluate(traits, tmp_path)["matched"] == ["custom"]


def test_runtime_bundle_rejects_copy_to_another_root(project, tmp_path):
    from overspec.core.resolution import resolve_runtime, show_details

    source(project, declaration("a", "runtime-trait", details="a"))
    project.initialize()
    identity = project.sync()["resolution"]
    other = tmp_path / "other"
    shutil.copytree(project.root, other)
    with pytest.raises(ValueError, match="root-mismatched"):
        resolve_runtime(other, identity, "context", ["a"], {})
    with pytest.raises(ValueError):
        show_details(other, "a")


def test_runtime_details_changes_refresh_reference_but_no_details_leak(project):
    path = source(project, declaration("a", "runtime-trait", details="first"))
    project.initialize()
    first = project.sync()
    path.write_text(declaration("a", "runtime-trait", details="second"))
    second = project.sync()
    assert second["changed"] and second["resolution"] != first["resolution"]
    assert "second" not in second["candidate"]


def test_detect_config_change_after_bundle_publication(project, monkeypatch):
    from overspec.core import storage

    source(project, declaration("a"))
    project.initialize()
    publish = storage.publish
    config = project.root / "openspec/config.yaml"

    def intervene(*args):
        result = publish(*args)
        config.write_text("schema: intervening\n")
        return result

    monkeypatch.setattr(storage, "publish", intervene)
    with pytest.raises(ValueError, match="changed"):
        project.sync()
    assert config.read_text() == "schema: intervening\n"


def test_explain_validates_context_size_like_static_resolve(project):
    from overspec.cli import main

    source(project, declaration("big", body="x" * (50 * 1024)))
    project.initialize()
    assert (
        main(
            [
                "trait",
                "resolve",
                "--explain",
                "--project",
                str(project.root),
                "--home",
                str(project.home),
            ]
        )
        != 0
    )


def test_compilation_rechecks_sources_after_generation_publish(project, monkeypatch):
    from overspec.core import storage

    path = source(project, declaration("a", "compiletime-trait"))
    project.initialize()
    pointer = (project.state / "compiled.json").read_bytes()
    path.write_text(declaration("a", "compiletime-trait", body="second"))
    publish = storage.publish

    def intervene(*args):
        result = publish(*args)
        path.write_text(declaration("a", "compiletime-trait", body="third"))
        return result

    monkeypatch.setattr(storage, "publish", intervene)
    with pytest.raises(ValueError, match="changed"):
        project.initialize(update=True)
    assert (project.state / "compiled.json").read_bytes() == pointer


def test_false_and_zero_owned_values_are_not_a_noop():
    from overspec.core.projection import project_yaml

    # Wrong scalar type is an owned edit, even where Python equality collapses it.
    # A string-list is the only valid generated guidance shape.
    text = "schema: spec-driven\noperations:\n  apply:\n    guidance: [false]\n"
    candidate, changed = project_yaml(
        text, [{"name": "a", "attach": "operations.apply.guidance", "body": "false"}]
    )
    assert changed and "# over:a" in candidate


def test_profile_activation_rejects_redirected_project_root(project, tmp_path):
    import os
    import subprocess

    from overspec.core.profiles import toggle_profiles, use_profile

    toggle_profiles(project.home)

    outside = tmp_path / "outside"
    (outside / "profile-default").mkdir(parents=True)
    project.over.rmdir()
    if os.name == "nt":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(project.over), str(outside)],
            check=True,
            capture_output=True,
        )
    else:
        project.over.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        use_profile(project.root, project.home, "default")
    assert not (outside / "config.toml").exists()


def test_hardlinked_sources_load_once(tmp_path):
    import os

    from overspec.core.profiles import trait_files

    original = tmp_path / "trait-a.toml"
    original.write_text(declaration("a"))
    os.link(original, tmp_path / "trait-b.toml")
    assert trait_files(tmp_path) == [original]


def test_suppressed_ordinary_does_not_mutate_compilation(project):
    from overspec.core.resolution import contributions, explain
    from overspec.core.storage import digest

    source(project, declaration("a", "compiletime-trait"))
    project.initialize()
    pointer = (project.state / "compiled.json").read_bytes()
    override = source(
        project,
        declaration("b", **{"actions": [{"type": "remove-trait", "trait": "a"}]}),
        "trait-hide.toml",
    )
    bundle = project.prepare()
    assert [x["name"] for x in contributions(bundle, digest(bundle))] == ["b"]
    assert {x["name"]: x["status"] for x in explain(bundle)} == {
        "a": "suppressed",
        "b": "matched",
    }
    override.unlink()
    bundle = project.prepare()
    assert [x["name"] for x in contributions(bundle, digest(bundle))] == ["a"]
    assert (project.state / "compiled.json").read_bytes() == pointer


def test_two_runtime_destinations_produce_separate_commands(project):
    from overspec.core.resolution import contributions
    from overspec.core.storage import digest

    source(
        project,
        declaration("a", "runtime-trait")
        + declaration("b", "runtime-trait", attach="operations.archive.guidance"),
    )
    project.initialize()
    bundle = project.prepare()
    groups = contributions(bundle, digest(bundle))
    assert len(groups) == 2
    assert "--trait a" in groups[0]["body"] and "--trait b" not in groups[0]["body"]
    assert "--trait b" in groups[1]["body"] and "--trait a " not in groups[1]["body"]


def test_shared_physical_source_is_not_loaded_in_both_layers(project):
    import os

    profile = source(project, declaration("a"), "profile-default/traits.toml")
    os.link(profile, project.over / "trait-local.toml")
    traits, overridden, _, _ = project.inventory()
    assert len(traits) == 1 and overridden == []
