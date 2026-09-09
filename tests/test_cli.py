import json
import shutil
import subprocess

import pytest
from conftest import declaration, source


def run(project, *arguments):
    return subprocess.run(
        [
            shutil.which("overspec"),
            "--home",
            str(project.home),
            *arguments,
            "--project",
            str(project.root),
        ],
        capture_output=True,
        text=True,
    )


def test_installed_console_init_sync_resolve_details(project):
    source(
        project,
        declaration("a", body="Static", details="Long details")
        + declaration(
            "r",
            "runtime-trait",
            body="Runtime",
            **{"assert": [{"type": "runtime-context-match", "kv": "flag=true"}]},
        ),
    )
    result = run(project, "init")
    assert result.returncode == 0, result.stderr
    result = run(project, "sync", "--dry-run", "--json")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["changed"]
    result = run(project, "sync", "--json")
    assert result.returncode == 0, result.stderr
    identity = json.loads(result.stdout)["resolution"]
    assert "Long details" in run(project, "trait", "show", "a", "--details").stdout
    assert "Long details" not in run(project, "trait", "resolve", "--explain").stdout
    context = project.root / "context.json"
    context.write_text('{"flag":true}')
    result = run(
        project,
        "trait",
        "resolve",
        "--resolution",
        identity,
        "--attach",
        "context",
        "--trait",
        "r",
        "--context-file",
        str(context),
    )
    assert result.returncode == 0 and "Runtime\n<!-- over:r -->" in result.stdout
    assert (
        run(
            project,
            "trait",
            "resolve",
            "--resolution",
            identity,
            "--attach",
            "context",
            "--trait",
            "r",
        ).stdout
        == ""
    )
    assert run(project, "update").returncode == 0


def test_cli_help_errors_and_profile_activation(project):
    assert run(project, "profile", "activate").returncode == 0
    source(project, declaration("a"), "profile-default/traits.toml")
    result = run(project, "profile", "list", "--json")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)[0]["name"] == "default"
    assert run(project, "profile", "use", "default").returncode == 0
    result = run(project, "sync")
    assert result.returncode != 0 and "init" in result.stderr
    result = subprocess.run(
        [shutil.which("overspec"), "--help"], capture_output=True, text=True
    )
    assert "sync" in result.stdout and "trait" in result.stdout
    assert run(project, "profile", "use", "missing").returncode != 0


def test_no_command_shows_welcoming_help():
    result = subprocess.run([shutil.which("overspec")], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Project workflow" in result.stdout
    assert "Profiles and traits" in result.stdout
    assert "Preview or synchronize" in result.stdout


def test_sync_help_groups_options():
    result = subprocess.run(
        [shutil.which("overspec"), "sync", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    for text in ("Project", "Inputs", "Output", "--dry-run", "--vars-file", "--json"):
        assert text in result.stdout
    assert "~/.overspec" in result.stdout


def test_profile_table_and_empty_state(project):
    assert run(project, "profile", "activate").returncode == 0
    empty = run(project, "profile", "list")
    assert "No profiles found" in empty.stdout
    source(project, declaration("a"), "profile-default/traits.toml")
    result = run(project, "profile", "list")
    for text in ("Profile", "Scope", "Active", "Location", "default", "project"):
        assert text in result.stdout


def test_typer_runner_and_clean_json(project):
    assert run(project, "profile", "activate").returncode == 0
    from typer.testing import CliRunner

    from overspec.cli import app

    runner = CliRunner()
    source(project, declaration("a"), "profile-default/traits.toml")
    result = runner.invoke(
        app,
        [
            "--home",
            str(project.home),
            "profile",
            "--json",
            "list",
            "--project",
            str(project.root),
        ],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)[0]["name"] == "default"
    assert "\x1b[" not in result.stdout


def test_preview_has_distinct_summary_candidate_and_diff(project):
    source(project, declaration("a", body="Use [literal] markup."))
    assert run(project, "init").returncode == 0
    preview = run(project, "sync", "--dry-run")
    assert preview.returncode == 0
    for text in ("Sync preview", "Candidate YAML", "Changes", "Use [literal] markup."):
        assert text in preview.stdout


@pytest.mark.parametrize(
    "args",
    [
        [
            "profile",
            "pull",
            "x",
            "--owner",
            "o",
            "--repo",
            "r",
            "--path",
            "p",
            "--branch",
            "main",
            "--commit",
            "a" * 40,
        ],
        ["trait", "show", "x"],
        ["sync", "--unknown"],
    ],
)
def test_usage_errors_do_not_show_tracebacks(project, args):
    result = run(project, *args)
    assert result.returncode != 0
    assert "Traceback" not in result.stderr


def test_redirected_preview_preserves_complete_long_lines(project):
    body = "Keep " + "long-guidance-" * 30 + "the-end"
    source(project, declaration("a", body=body))
    assert run(project, "init").returncode == 0
    preview = run(project, "sync", "--dry-run")
    structured = json.loads(run(project, "sync", "--dry-run", "--json").stdout)
    assert structured["candidate"] in preview.stdout
    # subprocess text mode normalizes the original Windows CRLF diff lines.
    assert structured["diff"].replace("\r\n", "\n") in preview.stdout
