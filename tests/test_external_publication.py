import pytest
from conftest import declaration, source
from test_profiles import write

from overspec.core import storage


@pytest.mark.parametrize(
    "change", ["view", "current", "file", "layout", "order", "marker", "profile"]
)
@pytest.mark.parametrize("operation", ["sync", "compile"])
def test_changed_external_inputs_reject_publication(
    project, external, monkeypatch, change, operation
):
    import overspec.core.project as module

    client, root = external
    path = write(root, "openspec/.over/trait.toml", declaration("external"))
    client.add(root)
    project.initialize()
    project.sync()
    original = module.evaluate
    before = (
        project.state.read_bytes(),
        (project.root / "openspec/config.yaml").read_bytes(),
    )

    def evaluate(*args, **kwargs):
        result = original(*args, **kwargs)
        if change == "view":
            client.document["filters"] = {"providers": ["git"]}
        elif change == "current":
            client.states["a" * 64]["current"]["id"] = "9" * 64
        elif change == "file":
            path.write_text(declaration("external", body="changed"))
        elif change == "layout":
            (root / "over-traits").mkdir(exist_ok=True)
            client.add(root)
        elif change == "order":
            (project.home / "config.toml").write_text(
                '[sources.saucepan]\nmarker="marker"\norder=["' + "b" * 64 + '"]\n'
            )
        elif change == "marker":
            (project.home / "marker").write_text("different secret")
        elif change == "profile":
            write(root, "openspec/.over/profile-default/trait.toml", declaration("contributor"))
            client.add(root)
        return result

    monkeypatch.setattr(module, "evaluate", evaluate)
    with pytest.raises(ValueError, match="changed|verification"):
        project.sync() if operation == "sync" else project.initialize(update=True)
    assert before == (
        project.state.read_bytes(),
        (project.root / "openspec/config.yaml").read_bytes(),
    )


def test_failure_after_config_publication_reports_partial_sync(
    project, external, monkeypatch
):
    client, root = external
    write(root, "over-traits/trait.toml", declaration("external"))
    client.add(root)
    project.initialize()
    project.sync()
    previous = project.state.read_bytes()
    source(project, declaration("changed"))
    original = storage.atomic_write

    def publish(root, relative, data, **kwargs):
        result = original(root, relative, data, **kwargs)
        if relative == "openspec/config.yaml":
            client.document["filters"] = {"providers": ["git"]}
        return result

    monkeypatch.setattr(storage, "atomic_write", publish)
    with pytest.raises(ValueError, match="configuration may already have changed"):
        project.sync()
    assert project.state.read_bytes() == previous
    assert "changed" in (project.root / "openspec/config.yaml").read_text()


def test_overridden_compilation_and_unrelated_refresh_do_not_require_update(
    project, external
):
    client, root = external
    path = write(
        root, "over-traits/trait.toml", declaration("same", "compiletime-trait")
    )
    client.add(root)
    source(project, declaration("same", body="local"))
    project.initialize()
    compilation = storage.read_state(project.root)["compilation"]["id"]
    path.write_text(declaration("same", "compiletime-trait", body="changed"))
    write(root, "README.md", "unrelated content")
    client.add(root, snapshot="3" * 64)
    project.sync()
    assert storage.read_state(project.root)["compilation"]["id"] == compilation


def test_ordinary_profile_contributor_change_keeps_compilation(project, external):
    client, root = external
    write(root, "over-profiles/profile-default/trait.toml", declaration("same"))
    client.add(root)
    project.initialize()
    compilation = storage.read_state(project.root)["compilation"]["id"]
    source(project, declaration("same"), "profile-default/trait.toml")
    project.sync()
    assert storage.read_state(project.root)["compilation"]["id"] == compilation
