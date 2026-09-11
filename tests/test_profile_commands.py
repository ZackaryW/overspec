import json

import pytest
from conftest import declaration, source
from typer.main import get_command
from typer.testing import CliRunner

from overspec.cli import app
from overspec.core.profiles import toggle_profiles


def test_command_surface_and_completion_refresh_after_toggling(project, monkeypatch):
    monkeypatch.setenv("OVERSPEC_HOME", str(project.home))
    runner = CliRunner()
    source(project, declaration("default"), "profile-default/traits.toml")
    args = ["--project", str(project.root), "profile"]

    def commands():
        command = get_command(app)
        with command.make_context(
            "overspec", ["profile"], resilient_parsing=True
        ) as root:
            profile = command.get_command(root, "profile")
            with profile.make_context(
                "profile", [], parent=root, resilient_parsing=True
            ) as ctx:
                return {
                    x.value
                    for x in profile.shell_complete(ctx, "")
                    if not x.value.startswith("-")
                }

    for enabled in (False, True, False):
        expected = (
            {"activate", "use", "list"} if enabled else {"activate"}
        )
        assert commands() == expected
        help_result = runner.invoke(app, args + ["--help"])
        assert help_result.exit_code == 0
        assert "activate" in help_result.output
        if not enabled:
            for name in ("list", "use", "pull", "update"):
                result = runner.invoke(app, args + [name])
                assert result.exit_code != 0 and "No such command" in result.output
                assert "Did you mean" not in result.output
            assert "List available" not in help_result.output
        else:
            selected = runner.invoke(app, args + ["use", "default", "--json"])
            assert selected.exit_code == 0, selected.output
            assert json.loads(selected.stdout)["profile"] == "default"
        changed = runner.invoke(app, args + ["activate", "--json"])
        assert changed.exit_code == 0, changed.output
        assert json.loads(changed.stdout)["enabled"] is not enabled
    assert runner.invoke(app, args + ["activate", "default"]).exit_code != 0
    assert runner.invoke(app, args + ["use", "default", "--user"]).exit_code != 0
    assert runner.invoke(app, ["init", "--profile", "default"]).exit_code != 0


@pytest.mark.parametrize("position", ["root", "group", "command"])
def test_explicit_home_controls_dispatch_and_writes(project, monkeypatch, position):
    alternate = project.root / "other-home"
    toggle_profiles(alternate)
    monkeypatch.setenv("OVERSPEC_HOME", str(alternate))
    runner = CliRunner()
    prefix = ["--home", str(project.home)]
    args = {
        "root": prefix + ["profile", "list"],
        "group": ["profile"] + prefix + ["list"],
        "command": ["profile", "list"] + prefix,
    }[position]
    assert runner.invoke(app, args).exit_code != 0
    on = ["activate" if a == "list" else a for a in args]
    result = runner.invoke(app, on + ["--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == {"enabled": True}
    assert runner.invoke(app, args).exit_code == 0


def test_profile_list_reports_saved_and_environment_choice(project, monkeypatch):
    monkeypatch.setenv("OVERSPEC_HOME", str(project.home))
    monkeypatch.setenv("OVERSPEC_PROFILE", "team")
    for name in ("default", "team"):
        source(project, declaration(name), f"profile-{name}/traits.toml")
    toggle_profiles(project.home)
    runner = CliRunner()
    args = ["--project", str(project.root), "profile"]
    selected = runner.invoke(app, args + ["use", "default", "--json"])
    assert selected.exit_code == 0, selected.output
    assert json.loads(selected.stdout)["environment"] == "team"
    rows = json.loads(runner.invoke(app, args + ["list", "--json"]).stdout)
    assert [x["name"] for x in rows if x["active"]] == ["team"]
    assert [x["name"] for x in rows if x["selected"]] == ["default"]
