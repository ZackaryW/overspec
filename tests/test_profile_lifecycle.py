from overspec.core import storage
import pytest
from conftest import declaration, source

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
    before = {project.state: project.state.read_bytes()}
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
    pointer = storage.read_state(project.root)["compilation"]
    config = (project.root / "openspec/config.yaml").read_bytes()
    publish = storage.atomic_write

    def intervene(*args, **kwargs):
        if change == "environment":
            monkeypatch.setenv("OVERSPEC_PROFILE", "strict")
        elif change == "toggle":
            toggle_profiles(project.home)
        else:
            use_profile(project.root, project.home, "strict")
        return publish(*args, **kwargs)

    monkeypatch.setattr(storage, "atomic_write", intervene)
    with pytest.raises(ValueError, match="changed"):
        project.initialize(update=True) if operation == "compile" else project.sync()
    assert storage.read_state(project.root)["compilation"] == pointer
    assert (project.root / "openspec/config.yaml").read_bytes() == config
