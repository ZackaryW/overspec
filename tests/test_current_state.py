import json

import pytest

from conftest import declaration, source
from overspec.core import storage
from overspec.core.resolution import resolve_runtime, show_details


def test_single_file_bounded_growth_and_noop(project):
    path = source(
        project,
        declaration("c", "compiletime-trait")
        + declaration("r", "runtime-trait", details="first"),
    )
    project.initialize()
    state = project.over / ".state.json"
    assert state.is_file() and not (project.over / ".state").exists()
    compiled = json.loads(state.read_text())["compilation"]
    old = project.sync()["resolution"]
    for i in range(8):
        path.write_text(
            declaration("c", "compiletime-trait")
            + declaration(
                "r", "runtime-trait", body=f"body-{i}", details=f"details-{i}"
            )
        )
        identity = project.sync()["resolution"]
        data = json.loads(state.read_text())
        assert data["compilation"] == compiled
        assert data["resolution"]["id"] == identity
        assert data["sync"]["resolution"] == identity
    assert not (project.over / ".state").exists()
    assert show_details(project.root, "r")["details"] == "details-7"
    with pytest.raises(ValueError, match="[Ss]tale|superseded"):
        resolve_runtime(project.root, old, "context", ["r"])
    with pytest.raises(ValueError, match="[Ss]tale|superseded"):
        show_details(project.root, "r", old)
    before = state.read_bytes(), state.stat().st_mtime_ns
    assert not project.sync()["changed"]
    project.initialize(update=True)
    assert (state.read_bytes(), state.stat().st_mtime_ns) == before


def test_update_keeps_current_resolution_until_sync(project):
    path = source(
        project,
        declaration("c", "compiletime-trait", body="old")
        + declaration("r", "runtime-trait", details="saved"),
    )
    project.initialize()
    identity = project.sync()["resolution"]
    path.write_text(
        declaration("c", "compiletime-trait", body="new")
        + declaration("r", "runtime-trait", details="new")
    )
    project.initialize(update=True)
    assert (
        json.loads((project.over / ".state.json").read_text())["resolution"]["id"]
        == identity
    )
    assert show_details(project.root, "r", identity)["details"] == "saved"
    project.sync()
    with pytest.raises(ValueError, match="[Ss]tale"):
        show_details(project.root, "r", identity)


@pytest.mark.parametrize(
    "damage", ["root", "version", "shape", "hash", "receipt", "missing-receipt"]
)
def test_current_state_validation(project, damage):
    project.initialize()
    project.sync()
    path = project.over / ".state.json"
    state = json.loads(path.read_text())
    if damage == "root":
        state["root"] = "wrong"
    if damage == "version":
        state["version"] = True
    if damage == "shape":
        state["compilation"] = []
    if damage == "hash":
        state["compilation"]["id"] = "0" * 64
    if damage == "receipt":
        state["sync"]["resolution"] = "0" * 64
    if damage == "missing-receipt":
        state["sync"] = None
    path.write_text(json.dumps(state))
    before = path.read_bytes()
    with pytest.raises(ValueError, match="[Cc]orrupt|[Ii]nvalid"):
        project.prepare()
    assert path.read_bytes() == before


def test_state_failure_after_config_preserves_old_state_and_retries(
    project, monkeypatch
):
    path = source(project, declaration("r", "runtime-trait"))
    project.initialize()
    project.sync()
    state = project.over / ".state.json"
    before = state.read_bytes()
    path.write_text(declaration("r", "runtime-trait", body="new"))
    replace = storage.os.replace

    def fail(src, dst):
        if str(dst).endswith(".state.json"):
            raise OSError("injected state failure")
        return replace(src, dst)

    monkeypatch.setattr(storage.os, "replace", fail)
    with pytest.raises(ValueError, match="configuration may already"):
        project.sync()
    assert state.read_bytes() == before
    with pytest.raises(ValueError, match="stale"):
        show_details(project.root, "r")
    monkeypatch.setattr(storage.os, "replace", replace)
    assert not project.sync()["changed"]
    assert show_details(project.root, "r")["details"] is None


def test_legacy_requires_regeneration_without_read_migration(project):
    from test_setup_cli import invoke

    legacy = project.over / ".state"
    legacy.mkdir()
    (legacy / "compiled.json").write_text('{"id":"old"}')
    assert invoke(project, "init").exit_code == 1
    assert not (project.over / ".current.toml").exists()
    with pytest.raises(ValueError, match="update"):
        project.prepare()
    assert not (project.over / ".state.json").exists()
    project.initialize(update=True)
    project.sync()
    assert (project.over / ".state.json").is_file()


@pytest.mark.parametrize("operation", ["compile", "sync"])
def test_intervening_state_edit_is_preserved(project, monkeypatch, operation):
    project.initialize()
    project.sync()
    before = project.state.read_bytes()
    original = storage.atomic_write

    def intervene(root, relative, data, **kwargs):
        project.state.write_bytes(before + b"\n")
        return original(root, relative, data, **kwargs)

    monkeypatch.setattr(storage, "atomic_write", intervene)
    with pytest.raises(ValueError, match="changed"):
        project.initialize(update=True) if operation == "compile" else project.sync()
    assert project.state.read_bytes() == before + b"\n"


def test_state_redirect_is_rejected_without_writes(project, tmp_path):
    import os
    import subprocess

    outside = tmp_path / "outside"
    outside.mkdir()
    target = project.over / ".state.json"
    if os.name == "nt":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(target), str(outside)],
            check=True,
            capture_output=True,
        )
    else:
        target.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        project.initialize()
    assert list(outside.iterdir()) == []


def test_cli_init_ignores_single_state_in_a_new_worktree(project):
    from test_setup_cli import invoke
    from test_variable_setup import git

    git(project.root, "init", "-q")
    result = invoke(project, "init", "--json")
    assert result.exit_code == 0, result.output
    assert git(project.root, "check-ignore", "--no-index", "openspec/.over/.state.json")
    assert not git(project.root, "ls-files", "--", "openspec/.over/.state.json")
