"""Removed acquisition interfaces stay unavailable without mutating legacy files."""

import importlib.util

import pytest
from test_profiles import write
from typer.testing import CliRunner

from overspec.cli import app
from overspec.core.profiles import toggle_profiles


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("command", ["pull", "update"])
def test_legacy_commands_are_removed_in_both_modes(project, enabled, command):
    path = write(project.home, ".state/remotes/default/current.json", "legacy sentinel")
    if enabled:
        toggle_profiles(project.home)
    before = {p: p.read_bytes() for p in project.home.rglob("*") if p.is_file()}
    result = CliRunner().invoke(app, ["--project", str(project.root), "--home", str(project.home),
                                     "profile", command, "--help"])
    assert result.exit_code != 0
    assert "No such command" in result.output
    assert {p: p.read_bytes() for p in project.home.rglob("*") if p.is_file()} == before
    assert path.read_text() == "legacy sentinel"


def test_legacy_remote_module_is_removed():
    assert importlib.util.find_spec("overspec.core.remotes") is None
