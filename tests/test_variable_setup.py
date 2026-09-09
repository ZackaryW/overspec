import json
from pathlib import Path
import subprocess

import pytest


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def change(root):
    root.mkdir(parents=True)
    (root / ".openspec.yaml").write_text("schema: spec-driven\n")
    return root


def test_setup_is_preserving_optional_and_idempotent(project, tmp_path):
    from overspec.core.setup import setup_variables

    selected = change(tmp_path / "external/change")
    selected.joinpath(".current.toml").write_bytes(b"# mine\r\n[vars]\r\nx=1\r\n")
    existing = selected / ".current.toml"
    before = existing.read_bytes(), existing.stat().st_mtime_ns
    result = setup_variables(project.root, [selected])
    assert result["success"]
    assert {r["status"] for r in result["targets"]} == {"created", "preserved"}
    assert all(r["ignore"] == "unavailable" for r in result["targets"])
    assert (existing.read_bytes(), existing.stat().st_mtime_ns) == before
    created = project.over / ".current.toml"
    timestamp = created.stat().st_mtime_ns
    assert "[vars]" in created.read_text()
    assert setup_variables(project.root, [selected])["success"]
    assert created.stat().st_mtime_ns == timestamp
    assert not list(tmp_path.rglob(".vars.toml"))


def test_setup_git_coverage_and_tracking_reports(project, tmp_path):
    from overspec.core.setup import setup_variables

    git(project.root, "init", "-q")
    external = tmp_path / "store"
    selected = change(external / "openspec/changes/one")
    git(external, "init", "-q")
    current = selected / ".current.toml"
    current.write_text("[vars]\nx=1")
    git(external, "add", ".")
    (external / ".gitignore").write_text(".vars.toml\n!.current.toml\n")
    (selected / ".vars.toml").write_text("[vars]\nx=2")
    result = setup_variables(project.root, [selected])
    assert result["success"] and len(result["worktrees"]) == 2
    item = next(r for r in result["targets"] if r["path"] == str(current))
    assert item["tracked"] and item["vars_ignored"]
    assert git(external, "ls-files", "--", str(current))
    for root in [project.root, external]:
        ignore = root / ".gitignore"
        before = ignore.read_bytes(), ignore.stat().st_mtime_ns
        assert setup_variables(project.root, [selected])["success"]
        assert (ignore.read_bytes(), ignore.stat().st_mtime_ns) == before
    assert ".vars.toml" not in (project.root / ".gitignore").read_text()


def test_setup_preflight_and_partial_retry(project, tmp_path, monkeypatch):
    from overspec.core import setup

    selected = change(tmp_path / "one")
    selected.joinpath(".current.toml").write_text("[bad]")
    with pytest.raises(ValueError, match="unknown"):
        setup.setup_variables(project.root, [selected])
    assert not (project.over / ".current.toml").exists()
    selected.joinpath(".current.toml").unlink()
    create = setup.create_current

    def fail(root, relative):
        if root == selected:
            raise OSError("injected failure")
        return create(root, relative)

    monkeypatch.setattr(setup, "create_current", fail)
    result = setup.setup_variables(project.root, [selected])
    assert not result["success"]
    assert {r["status"] for r in result["targets"]} == {"created", "failed"}
    monkeypatch.setattr(setup, "create_current", create)
    assert setup.setup_variables(project.root, [selected])["success"]


def test_exclusive_create_preserves_competing_creator(project, monkeypatch):
    from overspec.core.setup import create_current

    original = Path.open
    target = project.over / ".current.toml"

    def compete(self, mode="r", *args, **kwargs):
        if self == target and mode == "xb":
            with original(self, "wb") as stream:
                stream.write(b'[vars]\nx="winner"')
        return original(self, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", compete)
    assert create_current(project.root, "openspec/.over/.current.toml") == "preserved"
    assert "winner" in target.read_text()


def test_discovery_follows_status_and_store(project, tmp_path):
    from overspec.core.discovery import discover_changes
    from zuu.case3 import ProcessResult

    external = change(tmp_path / "store/one")
    calls = []

    def runner(argv, cwd):
        calls.append((argv, cwd))
        data = (
            {"changes": [{"name": "one", "status": "complete"}]}
            if "list" in argv
            else {"changeRoot": str(external), "changeName": "one"}
        )
        return ProcessResult(0, json.dumps(data), "")

    assert discover_changes(project.root, store="team", runner=runner) == [external]
    assert all(
        tuple(argv[-2:]) == ("--store", "team") and cwd == project.root
        for argv, cwd in calls
    )


@pytest.mark.parametrize(
    "payload",
    ["oops", "{}", '{"changes": [1]}', '{"changes": [{"name": "../archive"}]}'],
)
def test_discovery_rejects_malformed_results(project, payload):
    from overspec.core.discovery import discover_changes
    from zuu.case3 import ProcessResult

    with pytest.raises(ValueError, match="OpenSpec"):
        discover_changes(project.root, runner=lambda *_: ProcessResult(0, payload, ""))
    assert not (project.over / ".current.toml").exists()


def test_ignore_verification_rollback_and_stale_plan(project, monkeypatch):
    from overspec.core import setup

    git(project.root, "init", "-q")
    ignore = project.root / ".gitignore"
    ignore.write_text("# initial\n")
    # A nested negation cannot be defeated by appending a worktree-root pattern.
    (project.over / ".gitignore").write_text("!.current.toml\n")
    result = setup.setup_variables(project.root, [])
    assert not result["success"] and ignore.read_text() == "# initial\n"
    assert not (project.over / ".current.toml").exists()
    (project.over / ".gitignore").unlink()
    apply = setup.apply_gitignore

    def intervene(plan):
        ignore.write_text("# concurrent\n")
        return apply(plan)

    monkeypatch.setattr(setup, "apply_gitignore", intervene)
    result = setup.setup_variables(project.root, [])
    assert not result["success"] and ignore.read_text() == "# concurrent\n"
    assert not (project.over / ".current.toml").exists()
