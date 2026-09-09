import json

from conftest import declaration, source
from typer.testing import CliRunner

from overspec.cli import app


def test_explain_displays_group_paths_operators_and_skipped_branches(
    project, monkeypatch
):
    monkeypatch.setattr("shutil.which", lambda app: app if app == "available" else None)
    source(
        project,
        declaration(
            "grouped",
            **{
                "assert": {
                    "or": True,
                    "1": {"assertion": [{"type": "which", "app": "available"}]},
                    "2": {"assertion": [{"type": "~which", "app": "missing"}]},
                }
            },
        ),
    )
    project.initialize()
    args = [
        "--project",
        str(project.root),
        "--home",
        str(project.home),
        "trait",
        "resolve",
        "--explain",
    ]
    runner = CliRunner()
    result = runner.invoke(app, args, terminal_width=180)
    assert result.exit_code == 0, result.output
    assert "OR" in result.output and "AND" in result.output
    assert "assert.1.assertion.1" in result.output
    assert "assert.2" in result.output and "skipped" in result.output
    structured = runner.invoke(app, args + ["--json"])
    decision = json.loads(structured.stdout)[0]["decision"]
    assert decision["condition"]["children"][1]["skipped"]
    assert len(decision["assertions"]) == 1

    # Old compiled decisions lack tree traces; still show their evaluated reasons.
    bundle = project.prepare()
    del bundle["static"]["decisions"]["grouped"]["condition"]
    monkeypatch.setattr(type(project), "prepare", lambda *a, **kw: bundle)
    old = runner.invoke(app, args, terminal_width=180)
    assert old.exit_code == 0 and "available" in old.output
