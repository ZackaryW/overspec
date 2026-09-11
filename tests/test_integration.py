import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest
from conftest import declaration, source

from overspec.core.projection import parse_yaml
from overspec.core.resolution import show_details


@pytest.mark.parametrize("enabled", [False, True])
def test_companion_openspec_consumes_guidance_without_lifecycle_changes(
    project, tmp_path, enabled
):
    if enabled:
        from overspec.core.profiles import toggle_profiles

        toggle_profiles(project.home)
    executable = shutil.which("openspec")
    assert executable, "Companion OpenSpec CLI is required for this integration check"
    env = {
        **os.environ,
        "OPENSPEC_TELEMETRY": "0",
        "XDG_CONFIG_HOME": str(tmp_path / "xdg"),
    }

    def openspec(*args):
        completed = subprocess.run(
            [executable, *args],
            cwd=project.root,
            env=env,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stderr
        return completed.stdout

    openspec("init", "--tools", "none", "--no-animation")
    openspec("new", "change", "integration-case")
    change = project.root / "openspec/changes/integration-case"
    (change / "proposal.md").write_text("## Why\nIntegration fixture\n")
    (change / "design.md").write_text("## Context\nIntegration fixture\n")
    (change / "tasks.md").write_text("## 1. Work\n- [ ] 1.1 Integration fixture\n")
    (change / "specs/fixture").mkdir(parents=True)
    (change / "specs/fixture/spec.md").write_text(
        "## ADDED Requirements\n### Requirement: Example\nThe system SHALL return guidance.\n#### Scenario: Read\n- **WHEN** requested\n- **THEN** return guidance\n"
    )
    source(
        project,
        declaration("context", body="Context from overspec")
        + declaration(
            "proposal", attach="rules.proposal", body="Proposal from overspec"
        )
        + declaration(
            "apply", attach="operations.apply.guidance", body="Apply from overspec"
        )
        + declaration(
            "archive-a",
            "runtime-trait",
            attach="operations.archive.guidance",
            body="Archive A",
            **{"assert": [{"type": "runtime-context-match", "kv": "flag=true"}]},
        )
        + declaration(
            "archive-b",
            "runtime-trait",
            attach="operations.archive.guidance",
            body="Archive B",
        ),
    )
    before = {
        p.relative_to(change): p.read_bytes() for p in change.rglob("*") if p.is_file()
    }
    project.initialize()
    project.sync()
    proposal = json.loads(
        openspec("instructions", "proposal", "--change", "integration-case", "--json")
    )
    apply = json.loads(
        openspec("instructions", "apply", "--change", "integration-case", "--json")
    )
    archive = json.loads(
        openspec("instructions", "archive", "--change", "integration-case", "--json")
    )
    assert "Context from overspec" in json.dumps(proposal)
    assert "Proposal from overspec" in json.dumps(proposal)
    assert "Apply from overspec" in apply["operationGuidance"]
    instructions = archive["operationGuidance"]
    assert (
        len(instructions) == 1 and instructions[0].count("overspec trait resolve") == 1
    )
    command = next(
        line
        for line in instructions[0].splitlines()
        if line.startswith("overspec trait resolve")
    )
    context = project.root / "runtime.json"
    context.write_text('{"flag":true}')
    runtime = subprocess.run(
        [
            shutil.which("overspec"),
            *shlex.split(command)[1:],
            "--context-file",
            str(context),
        ],
        cwd=project.root,
        capture_output=True,
        text=True,
    )
    assert runtime.returncode == 0, runtime.stderr
    assert "Archive A" in runtime.stdout and "Archive B" in runtime.stdout
    assert {
        p.relative_to(change): p.read_bytes() for p in change.rglob("*") if p.is_file()
    } == before


def test_default_profile_eligibility_and_seeded_guidance(project):
    repository = Path(__file__).resolve().parents[1]
    shutil.copytree(
        repository / "openspec/.over/profile-default", project.over / "profile-default"
    )
    python = project.root / ".python-version"
    python.write_text("3.12")
    lock = project.root / "uv.lock"
    lock.write_text("version = 1")
    pyproject = project.root / "pyproject.toml"
    pyproject.write_text('[project]\ndependencies=["zuu"]')
    project.initialize()
    project.sync()
    config = project.root / "openspec/config.yaml"
    eligible = parse_yaml(config.read_text())["operations"]["apply"]["guidance"]
    seeded = parse_yaml((repository / "openspec/config.yaml").read_text())[
        "operations"
    ]["apply"]["guidance"]
    assert eligible == seeded
    assert len(eligible) == 2
    assert "observe the failure" in show_details(project.root, "tdd")["details"]
    assert "observe the failure" not in config.read_text()
    for file in (python, lock, pyproject):
        original = file.read_bytes()
        file.unlink()
        project.sync()
        assert parse_yaml(config.read_text())["operations"]["apply"]["guidance"] == [
            eligible[0]
        ]
        file.write_bytes(original)
        project.sync()
        assert (
            parse_yaml(config.read_text())["operations"]["apply"]["guidance"]
            == eligible
        )
    pyproject.write_text('[project]\ndependencies=[]\n[tool.uv.sources]\nzuu="local"')
    project.sync()
    assert parse_yaml(config.read_text())["operations"]["apply"]["guidance"] == [
        eligible[0]
    ]
