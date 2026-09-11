"""Default availability and source-first overlays through project operations."""

import json

import pytest
from conftest import declaration, source
from test_profiles import write
from typer.testing import CliRunner

from overspec.core.profiles import toggle_profiles, use_profile
from overspec.core.project import Project


@pytest.fixture
def consumer(tmp_path, monkeypatch):
    monkeypatch.delenv("OVERSPEC_PROFILE", raising=False)
    root = tmp_path / "consumer"
    write(root, "openspec/config.yaml", "schema: spec-driven\n")
    return Project(root, tmp_path / "consumer-home")


def test_default_served_without_local_sources_or_acquisition(consumer, monkeypatch):
    monkeypatch.chdir(consumer.root)
    traits, _, selection, _ = consumer.inventory()
    tdd = next(t for t in traits if t.name == "tdd")
    assert selection == "default"
    assert tdd.origin == "package:overspec/profile-default/trait-tdd.toml"
    assert tdd.provenance["package"] == "overspec"
    assert tdd.provenance["version"]
    assert not consumer.over.exists() and not consumer.home.exists()


def test_workspace_partial_profile_retains_default_and_replaces_declaration(consumer):
    source(
        consumer,
        declaration("tdd", body="workspace", details="local"),
        "profile-default/trait.toml",
    )
    traits = {t.name: t for t in consumer.inventory()[0]}
    assert "zmem-archive" in traits
    assert traits["tdd"].body == "workspace"
    assert traits["tdd"].attach == "context" and traits["tdd"].details == "local"
    source(consumer, declaration("tdd", body="loose"))
    assert next(t for t in consumer.inventory()[0] if t.name == "tdd").details is None


def test_named_profile_does_not_inherit_default(consumer):
    toggle_profiles(consumer.home)
    use_profile(consumer.root, consumer.home, "default")
    source(consumer, declaration("strict"), "profile-strict/trait.toml")
    use_profile(consumer.root, consumer.home, "strict")
    assert [t.name for t in consumer.inventory()[0]] == ["strict"]
    (consumer.over / "profile-empty").mkdir()
    use_profile(consumer.root, consumer.home, "empty")
    assert consumer.inventory()[0] == []


def test_user_content_is_ignored_and_unchanged(consumer):
    paths = [
        write(consumer.home, name, "invalid TOML")
        for name in (
            "profile-default/trait.toml",
            "trait.toml",
            ".state/remotes/default/current.json",
        )
    ]
    before = [p.read_bytes() for p in paths]
    assert "tdd" in {t.name for t in consumer.inventory()[0]}
    assert [p.read_bytes() for p in paths] == before


def test_empty_higher_profile_does_not_erase_packaged_default(consumer):
    (consumer.over / "profile-default").mkdir(parents=True)
    assert "tdd" in {t.name for t in consumer.inventory()[0]}


def test_two_repository_extensions_and_source_before_layout(project, external):
    client, root = external
    write(
        root,
        "over-profiles/profile-default/trait.toml",
        declaration("alpha") + declaration("beta", details="old"),
    )
    write(root, "over-traits/trait.toml", declaration("beta", body="a-loose"))
    client.add(root, "a" * 64)
    second = root.parent / "second"
    write(
        second,
        "over-profiles/profile-default/trait.toml",
        declaration("beta", body="b-profile") + declaration("gamma"),
    )
    client.add(second, "b" * 64)
    traits = {t.name: t for t in project.inventory()[0]}
    assert traits["alpha"].body == "alpha"
    assert traits["gamma"].body == "gamma"
    assert traits["beta"].body == "b-profile" and traits["beta"].details is None
    source(
        project,
        declaration("beta", body="workspace") + declaration("delta"),
        "profile-default/trait.toml",
    )
    traits = {t.name: t for t in project.inventory()[0]}
    assert {"alpha", "beta", "gamma", "delta"} <= traits.keys()
    assert traits["beta"].body == "workspace"


@pytest.mark.parametrize("bad", ["invalid TOML", declaration("duplicate") * 2])
def test_selected_lower_profile_cannot_hide_errors(project, external, bad):
    client, root = external
    write(root, "over-profiles/profile-default/trait.toml", bad)
    client.add(root)
    source(project, declaration("duplicate"), "profile-default/trait.toml")
    with pytest.raises(ValueError):
        project.inventory()


def test_profile_catalog_lists_contributors_and_removes_legacy_commands(consumer):
    from overspec.cli import app

    source(consumer, declaration("local"), "profile-default/trait.toml")
    toggle_profiles(consumer.home)
    args = ["--project", str(consumer.root), "--home", str(consumer.home), "profile"]
    runner = CliRunner()
    result = runner.invoke(app, [*args, "list", "--json"])
    assert result.exit_code == 0, result.output
    row = next(r for r in json.loads(result.output) if r["name"] == "default")
    assert [c["kind"] for c in row["contributors"]] == ["package", "workspace"]
    for command in ("pull", "update"):
        result = runner.invoke(app, [*args, command, "--help"])
        assert result.exit_code != 0


@pytest.mark.parametrize("json_output", [False, True])
def test_preinit_explanation_discovers_without_evaluation_or_writes(
    consumer, json_output
):
    from overspec.cli import app

    args = [
        "--project",
        str(consumer.root),
        "--home",
        str(consumer.home),
        "trait",
        "resolve",
        "--explain",
    ]
    result = CliRunner().invoke(app, args + (["--json"] if json_output else []))
    assert result.exit_code == 0, result.output
    if json_output:
        rows = json.loads(result.output)
        tdd = next(r for r in rows if r["name"] == "tdd")
        assert tdd["status"] == "deferred"
        assert tdd["decision"] is None
    else:
        assert "tdd" in result.output and "unevaluated" in result.output
    assert not consumer.over.exists() and not consumer.home.exists()
