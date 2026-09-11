import json

import pytest
from conftest import declaration, source
from test_profiles import write
from typer.testing import CliRunner

from overspec.core import storage
from overspec.core.profiles import toggle_profiles, use_profile
from overspec.core.resolution import explain, resolve_runtime, show_details


def test_external_default_layers_and_provenance(project, external):
    client, root = external
    write(
        root,
        "openspec/.over/profile-default/trait.toml",
        declaration("shared", details="profile") + declaration("profile"),
    )
    write(root, "openspec/.over/profile-other/trait.toml", "invalid TOML")
    write(root, "openspec/.over/trait.toml", declaration("shared", body="external"))
    client.add(root)
    write(project.home, "team/trait.toml", declaration("shared", body="user"))
    source(project, declaration("shared", body="project"))
    project.initialize()
    bundle = project.prepare()
    assert bundle["static"]["bodies"] == {"profile": "profile", "shared": "project"}
    assert [
        t["declaration"]["body"]
        for t in bundle["traits"]
        if t["declaration"]["name"] == "shared"
    ] == ["project"]
    assert len(bundle["overridden"]) == 2
    external_rows = [row for row in explain(bundle) if row.get("provenance", {}).get("source_id")]
    assert external_rows and all(
        row["provenance"]["source_id"] == "a" * 64 for row in external_rows
    )
    assert not (project.home / "profile-default").exists()
    assert not (project.over / "profile-default").exists()
    assert "secret-marker" not in json.dumps(bundle)


def test_project_profile_cannot_hide_malformed_external(project, external):
    client, root = external
    write(root, "over-profiles/profile-default/trait.toml", "bad TOML")
    write(root, "over-traits/trait.toml", declaration("external"))
    client.add(root)
    source(project, declaration("local"), "profile-default/trait.toml")
    with pytest.raises(ValueError):
        project.inventory()


def test_external_named_profile_and_cli_catalog(project, external, monkeypatch):
    from overspec.cli import app

    client, root = external
    write(root, "over-profiles/profile-team/nested/trait.toml", declaration("team"))
    client.add(root)
    monkeypatch.setenv("OVERSPEC_PROFILE", "team")
    assert project.inventory()[0] == []
    toggle_profiles(project.home)
    use_profile(project.root, project.home, "team")
    assert [t.name for t in project.inventory()[0]] == ["team"]
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "--project",
            str(project.root),
            "--home",
            str(project.home),
            "profile",
            "list",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    row = next(r for r in json.loads(result.stdout) if r["name"] == "team")
    contributor = row["contributors"][0]
    assert contributor["kind"] == "repository" and contributor["source_id"] == "a" * 64 and row["active"]
    assert contributor["path"] == "over-profiles/profile-team"


def test_runtime_refresh_stable_compilation_and_saved_offline(
    project, external, monkeypatch
):
    client, root = external
    text = declaration("compiled", "compiletime-trait") + declaration(
        "runtime", "runtime-trait", body="old ${value}", details="saved details"
    )
    write(root, "over-profiles/profile-default/trait.toml", text)
    write(root, "openspec/.over/.vars.toml", 'value="foreign"')
    client.add(root)
    project.initialize()
    saved = project.sync(values={"value": "consumer"})
    compilation = storage.read_state(project.root)["compilation"]["id"]
    newer = root.parent / "newer"
    write(
        newer,
        "over-profiles/profile-default/trait.toml",
        text.replace("old ${value}", "new ${value}"),
    )
    client.add(newer, snapshot="2" * 64)
    assert (
        resolve_runtime(project.root, saved["resolution"], "context", ["runtime"])[0][
            "body"
        ]
        == "old consumer"
    )
    current = project.sync(values={"value": "consumer"})
    assert storage.read_state(project.root)["compilation"]["id"] == compilation
    assert (
        resolve_runtime(project.root, current["resolution"], "context", ["runtime"])[0][
            "body"
        ]
        == "new consumer"
    )
    with pytest.raises(ValueError):
        resolve_runtime(project.root, saved["resolution"], "context", ["runtime"])
    monkeypatch.setattr(
        "overspec.core.external.adapter.create_client",
        lambda _: (_ for _ in ()).throw(AssertionError("live lookup")),
    )
    assert show_details(project.root, "runtime")["details"] == "saved details"
    write(project.over, ".current.toml", '[vars]\nvalue="live"')
    assert (
        resolve_runtime(project.root, current["resolution"], "context", ["runtime"])[0][
            "body"
        ]
        == "new live"
    )


def test_effective_compiletime_change_requires_update(project, external):
    client, root = external
    path = write(
        root, "over-traits/trait.toml", declaration("compiled", "compiletime-trait")
    )
    client.add(root)
    project.initialize()
    path.write_text(declaration("compiled", "compiletime-trait", body="changed"))
    client.add(root, snapshot="2" * 64)
    with pytest.raises(ValueError, match="update"):
        project.sync()
    project.initialize(update=True)
    project.sync()


def test_invalid_standalone_and_duplicate_layer_fail(project, external):
    client, root = external
    path = write(root, "over-traits/trait.toml", "invalid TOML")
    client.add(root)
    with pytest.raises(ValueError):
        project.inventory()
    path.write_text(declaration("same") + declaration("same"))
    client.add(root)
    with pytest.raises(ValueError, match="Duplicate same"):
        project.inventory()


def test_external_noop_preserves_config_and_state_mtime(project, external):
    client, root = external
    write(root, "over-traits/trait.toml", declaration("external"))
    client.add(root)
    project.initialize()
    project.sync()
    paths = [project.root / "openspec/config.yaml", project.state]
    before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths]
    assert not project.sync()["changed"]
    assert [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths] == before


def test_human_explanation_shows_exclusion_guidance(project, external):
    from overspec.cli import app

    client, root = external
    write(root, "over-traits/trait.toml", declaration("external"))
    client.add(root)
    project.initialize()
    client.states["a" * 64]["current"]["id"] = "9" * 64
    result = CliRunner().invoke(
        app,
        [
            "--project",
            str(project.root),
            "--home",
            str(project.home),
            "trait",
            "resolve",
            "--explain",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Acquire the whole current root" in result.output
