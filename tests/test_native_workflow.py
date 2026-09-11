"""Real companion instruction inputs in isolated projects and stores."""

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from overspec.cli import app
from overspec.core.project import Project

REPO = Path(__file__).resolve().parents[1]
COMPANION = Path(
    os.environ.get(
        "OVERSPEC_TEST_OPENSPEC_CLI", REPO.parent / "OpenSpec/bin/openspec.js"
    )
)


@pytest.fixture
def native(tmp_path):
    if not COMPANION.is_file() or not shutil.which("node"):
        pytest.skip(
            "Native companion prerequisite unavailable: set OVERSPEC_TEST_OPENSPEC_CLI"
        )
    env = {
        **os.environ,
        "XDG_CONFIG_HOME": str(tmp_path / "config-home"),
        "XDG_DATA_HOME": str(tmp_path / "data-home"),
        "OPENSPEC_TELEMETRY": "0",
    }

    def run(root, *args):
        result = subprocess.run(
            ["node", str(COMPANION), *args, "--json"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout)

    return run


def runtime(project, text, change=None):
    command = next(
        line for line in text.splitlines() if line.startswith("overspec trait resolve ")
    )
    args = shlex.split(command)[1:] + [
        "--project",
        str(project.root),
        "--home",
        str(project.home),
        "--json",
    ]
    if change:
        args += ["--change-root", str(change)]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def test_native_prechange_and_selected_store(tmp_path, native):
    workspace, store = tmp_path / "workspace", tmp_path / "store"
    workspace.mkdir()
    (store / "openspec/changes").mkdir(parents=True)
    (store / "openspec/specs").mkdir()
    (store / "openspec/config.yaml").write_text("schema: spec-driven\n")
    project = Project(store, tmp_path / "home")
    project.initialize()
    project.sync()
    native(workspace, "store", "register", str(store), "--id", "consult", "--yes")
    for operation, trait in [
        ("explore", "decision-explore"),
        ("propose", "decision-propose"),
    ]:
        inputs = native(workspace, "instructions", operation, "--store", "consult")
        assert inputs.get("operation") == operation, (
            "Companion lacks consultation operation support"
        )
        assert Path(inputs["root"]["path"]).resolve() == store.resolve()
        assert "changeRoot" not in inputs
        assert trait in {
            row["name"] for row in runtime(project, inputs["operationGuidance"][0])
        }
    native(workspace, "new", "change", "chosen", "--store", "consult")
    inputs = native(
        workspace, "instructions", "propose", "--change", "chosen", "--store", "consult"
    )
    change = Path(inputs["changeRoot"])
    (change / ".current.toml").write_text("[vars]\ndecision-choice=false\n")
    assert "decision-propose" not in {
        row["name"] for row in runtime(project, inputs["operationGuidance"][0], change)
    }
    assert not (workspace / "openspec").exists()


def test_native_schema_and_runtime_stage_controls(tmp_path, native):
    root = tmp_path / "consumer"
    (root / "openspec").mkdir(parents=True)
    shutil.copytree(
        REPO / "openspec/schemas/overspec", root / "openspec/schemas/overspec"
    )
    (root / "openspec/config.yaml").write_text("schema: overspec\n")
    project = Project(root, tmp_path / "home")
    project.initialize()
    project.sync()
    native(root, "new", "change", "sample")
    status = native(root, "status", "--change", "sample")
    assert {a["id"] for a in status["artifacts"]} == {
        "proposal",
        "specs",
        "design",
        "tasks",
    }
    change = Path(status["changeRoot"])
    (change / "proposal.md").write_text("Accepted behavior\n")
    for stage, trait in [("design", "utility-plan"), ("tasks", "utility-mature")]:
        instructions = native(root, "instructions", stage, "--change", "sample")
        assert "overspec-utilities" in instructions["instruction"]
        assert trait in {
            row["name"] for row in runtime(project, instructions["rules"][0], change)
        }
        (change / ".current.toml").write_text(f"[vars]\n{trait}=false\n")
        assert trait not in {
            row["name"] for row in runtime(project, instructions["rules"][0], change)
        }
        (change / ".current.toml").write_text("[vars]\n")
    assert not (root / ".agents").exists()  # sync did not install skills
