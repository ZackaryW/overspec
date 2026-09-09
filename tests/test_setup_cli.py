import json

from typer.testing import CliRunner

from overspec.cli import app
from test_variable_setup import change


def invoke(project, *args):
    return CliRunner().invoke(
        app, ["--project", str(project.root), "--home", str(project.home), *args]
    )


def test_cli_setup_only_preserves_state_and_normal_init_preflight(project, tmp_path):
    selected = change(tmp_path / "one")
    project.initialize()
    before = (project.state / "compiled.json").read_bytes()
    config = (project.root / "openspec/config.yaml").read_bytes()
    result = invoke(project, "init", "--change-root", str(selected))
    assert result.exit_code != 0 and "already exists" in result.output
    assert not (project.over / ".current.toml").exists()
    result = invoke(
        project, "init", "--setup-only", "--change-root", str(selected), "--json"
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["setup"]["success"]
    assert (project.state / "compiled.json").read_bytes() == before
    assert (project.root / "openspec/config.yaml").read_bytes() == config
    assert not project.home.exists()
    assert (selected / ".current.toml").is_file()


def test_cli_init_discovery_and_mutually_exclusive_scope(project, monkeypatch):
    from overspec.core import discovery

    calls = []

    def discover(root, *, store=None):
        calls.append((root, store))
        return []

    monkeypatch.setattr(discovery, "discover_changes", discover)
    result = invoke(project, "init", "--store", "team", "--json")
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["compilation"]
    assert calls == [(project.root, "team")]
    result = invoke(
        project,
        "init",
        "--setup-only",
        "--store",
        "team",
        "--change-root",
        str(project.root),
    )
    assert result.exit_code != 0 and "mutually exclusive" in result.output


def test_cli_discovery_error_does_not_write(project, monkeypatch):
    from overspec.core import discovery

    def fail(*args, **kwargs):
        raise ValueError("OpenSpec discovery unavailable")

    monkeypatch.setattr(discovery, "discover_changes", fail)
    result = invoke(project, "init", "--setup-only")
    assert result.exit_code == 1 and "OpenSpec" in result.output
    assert not (project.over / ".current.toml").exists()
    assert not project.state.exists()
