"""Package failures, stable identities, and publication through project APIs."""

from importlib.metadata import PackagePath
from pathlib import Path

import pytest
from conftest import declaration, source
from test_profiles import write

from overspec.core import bundled, storage
from overspec.core.project import Project
from overspec.core.resolution import resolve_runtime, show_details


@pytest.fixture
def package_project(tmp_path, monkeypatch):
    root = tmp_path / "package"
    path = write(
        root,
        "traits.toml",
        declaration("compiled", "compiletime-trait")
        + declaration("ordinary")
        + declaration("runtime", "runtime-trait", details="saved"),
    )
    package = bundled.BundledProfile(root, "1.0", ("traits.toml",))
    monkeypatch.setattr(bundled, "default_profile", lambda: package)
    project = Project(tmp_path / "project", tmp_path / "home")
    write(project.root, "openspec/config.yaml", "schema: spec-driven\n")
    return project, package, path


@pytest.mark.parametrize("damage", ["missing", "extra", "malformed"])
def test_broken_resources_do_not_fall_back(package_project, damage):
    project, package, path = package_project
    source(project, declaration("compiled"), "profile-default/trait.toml")
    if damage == "missing":
        path.rename(path.with_suffix(".absent"))
    elif damage == "extra":
        write(package.root, "trait-unexpected.toml", declaration("unexpected"))
    else:
        path.write_text("invalid TOML")
    with pytest.raises(ValueError, match="package"):
        project.inventory()
    assert not project.state.exists()


def test_wheel_loader_uses_metadata_inventory_not_consumer(tmp_path, monkeypatch):
    module = tmp_path / "installed/overspec"
    write(module, "_bundled/profile-default/trait.toml", declaration("installed"))
    write(
        tmp_path, "openspec/.over/profile-default/trait.toml", declaration("borrowed")
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(bundled.resources, "files", lambda _: module)
    monkeypatch.setattr(
        bundled.metadata,
        "files",
        lambda _: [PackagePath(bundled.PREFIX + "trait-missing.toml")],
    )
    project = Project(tmp_path, tmp_path / "home")
    with pytest.raises(ValueError, match="package"):
        project.inventory()


def test_resource_read_failure_is_actionable(package_project, monkeypatch):
    project, _, path = package_project
    original = Path.open

    def denied(self, *args, **kwargs):
        if self == path:
            raise PermissionError("denied resource")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", denied)
    with pytest.raises(ValueError, match="package.*cannot be read"):
        project.inventory()


def test_effective_changes_and_package_relocation(package_project, tmp_path):
    project, package, path = package_project
    project.initialize()
    initial = project.sync()
    compilation = storage.read_state(project.root)["compilation"]["id"]
    package.version = "2.0"
    relocated = tmp_path / "relocated"
    path = write(relocated, "traits.toml", path.read_text())
    package.root = relocated
    project.sync()
    assert storage.read_state(project.root)["compilation"]["id"] == compilation
    path.write_text(
        path.read_text().replace('body = "ordinary"', 'body = "changed ordinary"')
    )
    project.sync()
    assert storage.read_state(project.root)["compilation"]["id"] == compilation
    path.write_text(
        path.read_text().replace('body = "compiled"', 'body = "changed compiled"')
    )
    with pytest.raises(ValueError, match="update"):
        project.sync()
    project.initialize(update=True)
    project.sync()
    assert storage.read_state(project.root)["compilation"]["id"] != compilation
    assert resolve_runtime(project, "context", ["runtime"])[0]["body"] == "runtime"


def test_overridden_base_changes_do_not_invalidate_compilation(package_project):
    project, _, path = package_project
    source(project, declaration("compiled", "compiletime-trait", body="workspace"))
    project.initialize()
    project.sync()
    compilation = storage.read_state(project.root)["compilation"]["id"]
    path.write_text(
        path.read_text().replace('body = "compiled"', 'body = "changed base"')
    )
    project.sync()
    assert storage.read_state(project.root)["compilation"]["id"] == compilation


@pytest.mark.parametrize("mutation", ["content", "inventory"])
def test_package_changes_during_sync_reject_publication(
    package_project, monkeypatch, mutation
):
    from overspec.core import projection

    project, package, path = package_project
    project.initialize()
    before = (project.root / "openspec/config.yaml").read_bytes()
    state = project.state.read_bytes()
    original = projection.project_yaml

    def changed(*args):
        result = original(*args)
        if mutation == "content":
            path.write_text(path.read_text() + "\n# changed\n")
        else:
            write(package.root, "trait-added.toml", declaration("added"))
            package.expected = ("traits.toml", "trait-added.toml")
        return result

    monkeypatch.setattr(projection, "project_yaml", changed)
    with pytest.raises(ValueError, match="changed.*retry"):
        project.sync()
    assert (project.root / "openspec/config.yaml").read_bytes() == before
    assert project.state.read_bytes() == state


def test_runtime_needs_live_package_but_saved_details_do_not(
    package_project, monkeypatch
):
    project, _, _ = package_project
    project.initialize()
    result = project.sync()
    paths = [project.root / "openspec/config.yaml", project.state]
    before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths]
    assert not project.sync()["changed"]
    assert [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths] == before

    def unavailable():
        raise AssertionError("live package loaded")

    monkeypatch.setattr(bundled, "default_profile", unavailable)
    with pytest.raises(AssertionError, match="live package loaded"):
        resolve_runtime(project, "context", ["runtime"])
    assert show_details(project.root, "runtime")["details"] == "saved"


def test_same_physical_documents_are_read_once_with_distinct_provenance(
    package_project, monkeypatch
):
    project, _, path = package_project
    import os

    local = project.over / "profile-default/traits.toml"
    local.parent.mkdir(parents=True)
    os.link(path, local)
    alias = local.parent / "trait-alias.toml"
    os.link(path, alias)
    original = Path.open
    reads = []

    def counted(self, *args, **kwargs):
        if self in (path, local, alias):
            reads.append(self)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", counted)
    effective, overridden, _, _ = project.inventory()
    assert len(reads) == 1
    assert all(t.provenance["kind"] == "workspace" for t in effective)
    assert all(t.provenance["kind"] == "package" for t in overridden)
