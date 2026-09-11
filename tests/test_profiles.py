from pathlib import Path

import pytest


def write(root, name, text=""):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_discovery_separates_profiles_local_and_state(tmp_path):
    from overspec.core.profiles import profile_directories, trait_files

    for name in (
        "trait.toml",
        "team/traits.toml",
        "team/trait-testing.toml",
        "team/notes.toml",
        "profile-default/traits.toml",
        "profile-team.v2/nested/trait-x.toml",
        ".state/trait-cache.toml",
        "team/profile-hidden/trait-hidden.toml",
    ):
        write(tmp_path, name)
    assert set(profile_directories(tmp_path)) == {"default", "team.v2"}
    assert [
        p.relative_to(tmp_path).as_posix() for p in trait_files(tmp_path, local=True)
    ] == ["team/trait-testing.toml", "team/traits.toml", "trait.toml"]
    assert len(trait_files(tmp_path / "profile-team.v2")) == 1
    assert trait_files(tmp_path / "absent") == []


def test_repository_default_sources_discovered():
    from overspec.core.profiles import trait_files

    root = Path(__file__).resolve().parents[1] / "openspec/.over/profile-default"
    assert [p.name for p in trait_files(root)] == [
        "trait-bdd-behave.toml",
        "trait-bdd-cucumber.toml",
        "trait-bdd-flutter.toml",
        "trait-decision-explore.toml",
        "trait-decision-propose.toml",
        "trait-evidence-apply.toml",
        "trait-evidence-tasks.toml",
        "trait-integration-test-policies.toml",
        "trait-prototype-explore.toml",
        "trait-prototype-propose.toml",
        "trait-tdd.toml",
        "trait-utility-mature.toml",
        "trait-utility-plan.toml",
        "trait-zmem-commits.toml",
        "trait-zuu.toml",
        "traits.toml",
    ]


def test_redirected_directory_rejected(tmp_path):
    from overspec.core.profiles import trait_files

    outside = tmp_path / "outside"
    write(outside, "trait.toml")
    root = tmp_path / "root"
    root.mkdir()
    import os
    import subprocess

    if os.name == "nt":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(root / "redirect"), str(outside)],
            check=True,
            capture_output=True,
        )
    else:
        (root / "redirect").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="redirect|confined|symlink|reparse"):
        trait_files(root)


def test_selected_name_and_workspace_catalog(tmp_path):
    from overspec.core.profiles import select_profile, toggle_profiles, use_profile

    project, home = tmp_path / "project", tmp_path / "home"
    over = project / "openspec/.over"
    write(over, "profile-default/traits.toml")
    write(home, "profile-default/traits.toml")
    write(over, "profile-strict/traits.toml")
    config = write(project, "openspec/config.yaml", "schema: spec-driven\n")
    assert select_profile(project, home) == "default"
    toggle_profiles(home)
    use_profile(project, home, "strict")
    assert select_profile(project, home) == "strict"
    write(over, "config.toml", '[vars]\nlanguage = "Python"\n')
    use_profile(project, home, "default")
    assert select_profile(project, home) == "default"
    assert 'language = "Python"' in (over / "config.toml").read_text()
    assert config.read_text() == "schema: spec-driven\n"
    assert (over / "profile-default").exists()
    with pytest.raises(ValueError, match="missing"):
        use_profile(project, home, "missing")


def test_local_only_and_invalid_selection(tmp_path):
    from overspec.core.profiles import select_profile

    project, home = tmp_path / "project", tmp_path / "home"
    assert select_profile(project, home) == "default"
    write(home, "profile-strict/trait.toml")
    assert select_profile(project, home) == "default"
    write(home, "config.toml", '[profiles]\nenabled=true\nselected="missing"\n')
    with pytest.raises(ValueError, match="missing"):
        select_profile(project, home)


def test_default_user_home_is_overspec_and_ignores_other_apps(tmp_path, monkeypatch):
    from overspec.core.profiles import toggle_profiles, use_profile
    from overspec.core.project import Project

    user = tmp_path / "user"
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: user))
    monkeypatch.delenv("OVERSPEC_HOME", raising=False)
    foreign = write(user / ".over", "config.toml", 'profile = "another-app"\n')
    trait = write(
        user / ".overspec",
        "profile-default/traits.toml",
        '[[trait]]\nname="shared"\nattach="context"\nbody="Shared guidance"\n',
    )

    project = Project(root)
    effective, _, selection, _ = project.inventory()
    assert project.home == user / ".overspec"
    assert selection == "default"
    assert "shared" not in {t.name for t in effective}
    assert "tdd" in {t.name for t in effective}
    assert trait.read_text().startswith("[[trait]]")
    assert project.over == root / "openspec/.over"
    assert project.state == root / "openspec/.over/.state.json"
    toggle_profiles(project.home)
    use_profile(root, project.home, "default")
    import tomllib

    assert tomllib.loads((user / ".overspec/config.toml").read_text())["profiles"] == {
        "enabled": True,
        "selected": "default",
    }
    assert foreign.read_text() == 'profile = "another-app"\n'


def test_user_home_overrides_keep_their_precedence(tmp_path, monkeypatch):
    from overspec.core.project import Project

    monkeypatch.setenv("OVERSPEC_HOME", str(tmp_path / "environment"))
    assert Project(tmp_path).home == tmp_path / "environment"
    assert Project(tmp_path, home=tmp_path / "explicit").home == tmp_path / "explicit"
