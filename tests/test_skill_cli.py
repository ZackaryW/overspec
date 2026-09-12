import json
import sys
from importlib import import_module

import pytest
from typer.testing import CliRunner

from overspec.cli import app

pytest_plugins = ("test_managed_skills",)


def test_skill_cli_outside_project_and_json_errors(managed, monkeypatch):
    root, source, _ = managed
    monkeypatch.chdir(root)
    args = ["--home", str(root / "state"), "skill"]
    runner = CliRunner()
    listed = runner.invoke(app, [*args, "list", "--json"])
    assert listed.exit_code == 0, listed.output
    assert json.loads(listed.stdout)["skills"][0]["name"] == "reviewer"
    assert not (root / "state").exists()
    missing = runner.invoke(app, [*args, "install", "--all", "--json"])
    assert missing.exit_code != 0
    assert json.loads(missing.stdout)["ok"] is False
    missing_plain = runner.invoke(app, [*args, "install", "--agent", "kimi"])
    assert missing_plain.exit_code == 1
    assert "without an interactive terminal" in missing_plain.stdout
    assert not (root / "state").exists()
    options = [
        "--agent",
        "kimi",
        "--agent-home",
        str(root / "native"),
        "--all",
        "--json",
    ]
    installed = runner.invoke(app, [*args, "install", *options])
    assert installed.exit_code == 0, installed.output
    operation = json.loads(installed.stdout)["results"][0]["operation_id"]
    repeated = runner.invoke(app, [*args, "install", *options])
    assert repeated.exit_code == 0, repeated.output
    assert json.loads(repeated.stdout)["results"][0]["changed"] is False
    support = root / "native/.kimi-code/skills/reviewer/references/checks.md"
    (source / "references/checks.md").write_text("CLI refresh")
    refreshed = runner.invoke(app, [*args, "install", *options])
    assert refreshed.exit_code == 0, refreshed.output
    assert support.read_text() == "CLI refresh"
    refresh_id = json.loads(refreshed.stdout)["results"][0]["operation_id"]
    status = runner.invoke(app, [*args, "status", *options])
    assert json.loads(status.stdout)["results"][0]["classification"] == "current"
    history = runner.invoke(app, [*args, "history", *options])
    assert json.loads(history.stdout)["history"]
    assert runner.invoke(app, [*args, "restore", refresh_id, *options]).exit_code == 0
    restored = runner.invoke(app, [*args, "restore", operation, *options])
    assert restored.exit_code == 0, restored.output
    assert not (root / "native/.kimi-code/skills/reviewer").exists()
    assert not (root / "openspec").exists()


def test_force_option_only_for_restore_and_remove():
    runner = CliRunner()
    for operation in ("install", "update"):
        assert (
            "--force" not in runner.invoke(app, ["skill", operation, "--help"]).stdout
        )
    for operation in ("restore", "remove"):
        assert "--force" in runner.invoke(app, ["skill", operation, "--help"]).stdout


def test_native_failure_is_structured(monkeypatch, tmp_path):
    from overspec.core.skills import Skills

    def unavailable(self):
        raise RuntimeError("Git unavailable for registry")

    monkeypatch.setattr(Skills, "bind_home", unavailable)
    result = CliRunner().invoke(
        app, ["skill", "status", "--agent", "kimi", "--all", "--json"]
    )
    assert result.exit_code == 1
    assert json.loads(result.stdout)["diagnostics"] == ["Git unavailable for registry"]


@pytest.mark.parametrize("cancel", [False, True])
def test_zuu_interactive_selection_and_cancellation(managed, monkeypatch, cancel):
    from zuu.case11 import terminal
    from zuu.case11.state import Action

    root, _, catalog = managed
    cli = import_module("overspec.cli.skills")
    real_execute = cli.execute

    def terminal_execute(*args, **kwargs):
        # Keep the real ZuU selector, state transitions, and renderer; supply
        # deterministic terminal actions instead of platform keyboard input.
        monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        return real_execute(*args, **kwargs)

    class Session:
        def __init__(self, actions):
            self.actions = iter(actions)

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read_action(self):
            return next(self.actions)

    sessions = iter(
        [
            Session([Action.DOWN, Action.DOWN, Action.TOGGLE, Action.SUBMIT]),
            Session([Action.CANCEL] if cancel else [Action.TOGGLE, Action.SUBMIT]),
            Session([Action.TOGGLE, Action.SUBMIT]),
        ]
    )
    monkeypatch.setattr(terminal, "_make_session", lambda *_: next(sessions))
    monkeypatch.setattr(cli, "execute", terminal_execute)
    args = ["--home", str(root / "state"), "skill"]
    native = ["--agent-home", str(root / "native")]
    # JSON must bypass prompting even when both streams report an interactive TTY.
    missing_json = CliRunner().invoke(app, [*args, "install", *native, "--json"])
    assert missing_json.exit_code == 1
    assert json.loads(missing_json.stdout)["ok"] is False
    assert not (root / "state").exists()
    result = CliRunner().invoke(app, [*args, "install", *native])
    target = root / "native/.kimi-code/skills/reviewer/SKILL.md"
    if cancel:
        assert result.exit_code == 130, result.output
        assert not target.exists()
        assert not (root / "state").exists()
    else:
        assert result.exit_code == 0, result.output
        assert target.is_file()
        assert not (root / "native/.codex").exists()
        catalog.clear()
        removed = CliRunner().invoke(app, [*args, "remove", "--agent", "kimi", *native])
        assert removed.exit_code == 0, removed.output
        assert not target.exists()
