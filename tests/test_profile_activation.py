import tomllib

import pytest
from conftest import declaration, source

from overspec.core import profiles


def test_toggle_preserves_selection_variables_and_generated_state(project):
    project.home.mkdir()
    path = project.home / "config.toml"
    path.write_text('# keep\n[profiles]\nselected="team"\n[vars]\nx=1\n')
    original = (project.root / "openspec/config.yaml").read_bytes()
    assert not profiles.profiles_enabled(project.home)
    assert profiles.toggle_profiles(project.home) is True
    assert profiles.toggle_profiles(project.home) is False
    assert tomllib.loads(path.read_text()) == {
        "profiles": {"enabled": False, "selected": "team"},
        "vars": {"x": 1},
    }
    assert "# keep" in path.read_text()
    assert (project.root / "openspec/config.yaml").read_bytes() == original
    assert not project.state.exists()


def test_default_ignores_dormant_selection_and_unrelated_sources(project, monkeypatch):
    source(project, declaration("local"))
    source(project, declaration("default"), "profile-default/traits.toml")
    source(project, "bad toml", "profile-team/traits.toml")
    project.home.mkdir()
    (project.home / "config.toml").write_text('[profiles]\nselected="missing"\n')
    source(project, 'profile="missing"\n', "config.toml")
    monkeypatch.setenv("OVERSPEC_PROFILE", "missing")
    assert [t.name for t in project.inventory()[0]] == ["default", "local"]
    (project.over / "profile-default/traits.toml").rename(
        project.over / "profile-team/trait-old.toml"
    )
    (project.over / "profile-default").rmdir()
    assert [t.name for t in project.inventory()[0]] == ["local"]


def test_enabled_environment_user_precedence_and_local_override(project, monkeypatch):
    project.home.mkdir()
    for name in ("default", "team", "strict"):
        directory = project.over / f"profile-{name}"
        directory.mkdir()
        (directory / "traits.toml").write_text(declaration(name))
    source(project, declaration("local-team"), "profile-team/traits.toml")
    profiles.toggle_profiles(project.home)
    profiles.use_profile(project.root, project.home, "strict")
    assert profiles.select_profile(project.root, project.home) == "strict"
    monkeypatch.setenv("OVERSPEC_PROFILE", "team")
    assert [t.name for t in project.inventory()[0]] == ["local-team"]
    profiles.toggle_profiles(project.home)
    assert [t.name for t in project.inventory()[0]] == ["default"]
    profiles.toggle_profiles(project.home)
    monkeypatch.delenv("OVERSPEC_PROFILE")
    assert [t.name for t in project.inventory()[0]] == ["strict"]
    for invalid in ("", "missing", "../team"):
        monkeypatch.setenv("OVERSPEC_PROFILE", invalid)
        with pytest.raises(ValueError):
            project.inventory()


def test_management_requires_mode_before_side_effects(project):
    for operation in (
        lambda: profiles.use_profile(project.root, project.home, "default"),
    ):
        with pytest.raises(ValueError, match="profile activate"):
            operation()
    assert not project.home.exists()


@pytest.mark.parametrize("value", ['"yes"', "1", "[]"])
def test_invalid_mode_does_not_get_coerced(project, value):
    project.home.mkdir()
    (project.home / "config.toml").write_text(f"[profiles]\nenabled={value}\n")
    with pytest.raises(ValueError, match="boolean"):
        profiles.toggle_profiles(project.home)
