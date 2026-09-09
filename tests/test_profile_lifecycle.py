import pytest
from conftest import declaration, source

from overspec.core import storage
from overspec.core.profiles import toggle_profiles, use_profile
from overspec.core.resolution import resolve_runtime, show_details


def test_toggle_same_default_and_named_profile_lifetimes(project, monkeypatch):
    source(project, declaration("default"), "profile-default/traits.toml")
    source(
        project,
        declaration("team", "runtime-trait", details="Saved team"),
        "profile-team/traits.toml",
    )
    first = project.initialize()
    toggle_profiles(project.home)
    assert project.prepare()["compilation"] == first
    use_profile(project.root, project.home, "team")
    with pytest.raises(ValueError, match="update"):
        project.sync()
    project.initialize(update=True)
    saved = project.sync()["resolution"]
    toggle_profiles(project.home)
    monkeypatch.setenv("OVERSPEC_PROFILE", "missing")
    before = {p: p.read_bytes() for p in project.state.rglob("*") if p.is_file()}
    assert (
        resolve_runtime(project.root, saved, "context", ["team"])[0]["name"] == "team"
    )
    assert show_details(project.root, "team")["details"] == "Saved team"
    assert before == {p: p.read_bytes() for p in before}
    with pytest.raises(ValueError, match="update"):
        project.prepare()


@pytest.mark.parametrize("operation", ["compile", "sync"])
@pytest.mark.parametrize("change", ["environment", "toggle", "selection"])
def test_effective_selection_races_abort_publication(
    project, monkeypatch, operation, change
):
    for name in ("default", "team", "strict"):
        source(project, declaration(name), f"profile-{name}/traits.toml")
    toggle_profiles(project.home)
    use_profile(project.root, project.home, "team")
    project.initialize()
    project.sync()
    pointer = (project.state / "compiled.json").read_bytes()
    config = (project.root / "openspec/config.yaml").read_bytes()
    publish = storage.publish

    def intervene(root, namespace, value):
        result = publish(root, namespace, value)
        if change == "environment":
            monkeypatch.setenv("OVERSPEC_PROFILE", "strict")
        elif change == "toggle":
            toggle_profiles(project.home)
        else:
            use_profile(project.root, project.home, "strict")
        return result

    monkeypatch.setattr(storage, "publish", intervene)
    with pytest.raises(ValueError, match="changed"):
        project.initialize(update=True) if operation == "compile" else project.sync()
    assert (project.state / "compiled.json").read_bytes() == pointer
    assert (project.root / "openspec/config.yaml").read_bytes() == config
