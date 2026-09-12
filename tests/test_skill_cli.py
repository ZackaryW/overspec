import json

from typer.testing import CliRunner

from overspec.cli import app

pytest_plugins = ("test_managed_skills",)


def test_skill_cli_outside_project_and_json_errors(managed, monkeypatch):
    root, _, _ = managed
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
    status = runner.invoke(app, [*args, "status", *options])
    assert json.loads(status.stdout)["results"][0]["classification"] == "current"
    history = runner.invoke(app, [*args, "history", *options])
    assert json.loads(history.stdout)["history"]
    restored = runner.invoke(app, [*args, "restore", operation, *options])
    assert restored.exit_code == 0, restored.output
    assert not (root / "native/.kimi-code/skills/reviewer").exists()
    assert not (root / "openspec").exists()


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
