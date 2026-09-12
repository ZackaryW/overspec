"""Exercise an installed wheel with no checkout, SDK, or acquired default."""

import json
import os
import subprocess
import sys

import pytest
from conftest import declaration
from test_distribution import REPO, run_build
from test_profiles import write


@pytest.fixture(scope="module")
def installed(tmp_path_factory):
    root = tmp_path_factory.mktemp("installed")
    result = run_build(REPO, root / "dist", "--wheel")
    assert result.returncode == 0, result.stderr
    environment = root / "venv"
    result = subprocess.run(
        ["uv", "venv", str(environment), "--python", sys.executable],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    result = subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--python",
            str(python),
            str(next((root / "dist").glob("*.whl"))),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("PYTHONPATH", "OVERSPEC_HOME", "OVERSPEC_PROFILE", "VIRTUAL_ENV")
    }
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [
            str(python),
            "-I",
            "-c",
            "import importlib.util, overspec; assert importlib.util.find_spec('saucepan_sdk') is None; print(overspec.__file__)",
        ],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert str(environment).lower() in result.stdout.lower()
    return python, env


def invoke(installed, project, home, *args):
    python, env = installed
    result = subprocess.run(
        [
            str(python),
            "-I",
            "-m",
            "overspec",
            "--project",
            str(project),
            "--home",
            str(home),
            *args,
        ],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    return json.loads(result.stdout)


def test_installed_default_lifecycle_and_overrides(installed, tmp_path):
    project, home = tmp_path / "consumer", tmp_path / "home"
    config = write(project, "openspec/config.yaml", "schema: spec-driven\n")
    # Explicit exact change root avoids depending on an OpenSpec executable for setup discovery.
    change = project / "openspec/changes/example"
    change.mkdir(parents=True)
    write(change, ".openspec.yaml", "schema: spec-driven\n")
    rows = invoke(installed, project, home, "trait", "resolve", "--explain", "--json")
    tdd = next(r for r in rows if r["name"] == "tdd")
    assert (
        tdd["origin"].startswith("package:overspec/") and tdd["status"] == "unevaluated"
    )
    assert not (project / "openspec/.over").exists() and not home.exists()
    result = invoke(
        installed, project, home, "init", "--change-root", str(change), "--json"
    )
    assert result["setup"]["success"] and result["compilation"]
    assert (project / 'openspec/schemas/overspec/schema.yaml').is_file()
    schema_check = subprocess.run(['openspec', 'schema', 'validate', 'overspec'], cwd=project,
                                  env=installed[1], capture_output=True, text=True, shell=os.name == 'nt')
    assert schema_check.returncode == 0, schema_check.stdout + schema_check.stderr
    result = invoke(installed, project, home, "sync", "--json")
    assert "over:tdd" in config.read_text()
    assert "over:zuu" not in config.read_text()  # This is not a Python/uv project.
    state = project / "openspec/.over/.state.json"
    before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in (config, state)]
    assert not invoke(installed, project, home, "sync", "--json")["changed"]
    assert [(p.read_bytes(), p.stat().st_mtime_ns) for p in (config, state)] == before
    details = invoke(
        installed, project, home, "trait", "show", "tdd", "--details", "--json"
    )
    assert details["details"]
    assert (
        not (home / "profile-default").exists()
        and not (home / ".state/remotes").exists()
    )
    assert not (project / "openspec/.over/profile-default").exists()
    write(
        project,
        "openspec/.over/profile-default/trait-tdd.toml",
        declaration("tdd", body="Workspace override"),
    )
    invoke(installed, project, home, "update", "--json")
    invoke(installed, project, home, "sync", "--json")
    assert "Workspace override" in config.read_text()
    invoke(installed, project, home, "profile", "activate", "--json")
    invoke(installed, project, home, "profile", "use", "default", "--json")
    rows = invoke(installed, project, home, "profile", "list", "--json")
    assert [r["kind"] for r in rows[0]["contributors"]] == ["package", "workspace"]
    write(project, "openspec/.over/profile-strict/trait.toml", declaration("strict"))
    invoke(installed, project, home, "profile", "use", "strict", "--json")
    invoke(installed, project, home, "update", "--json")
    invoke(installed, project, home, "sync", "--json")
    assert "over:strict" in config.read_text() and "over:tdd" not in config.read_text()


def test_installed_resources_are_unchanged(installed, tmp_path):
    python, env = installed
    script = """
import hashlib
from importlib.resources import files
from overspec.core.project import Project
from pathlib import Path
root = files('overspec').joinpath('_bundled', 'profile-default')
def snapshot():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
before = snapshot()
from overspec.core.skill_assets import skill_catalog, materialize_skills
assert 'overspec-bootstrap' in {s.name for s in skill_catalog()}
with materialize_skills(['overspec-bootstrap']) as sources:
    assert (sources[0].path / 'references/controls.md').is_file()
    assert 'site-packages' in str(sources[0].path)
p = Project(Path.cwd(), Path.cwd() / 'home')
p.initialize()
result = p.sync()
from overspec.core.resolution import resolve_runtime, show_details
rows = resolve_runtime(p, 'operations.archive.guidance', ['do-not-archive-openspec-change'], {'do-not-archive': True})
assert rows and rows[0]['name'] == 'do-not-archive-openspec-change'
assert show_details(p.root, 'tdd')['details']
assert snapshot() == before
"""
    write(tmp_path, "openspec/config.yaml", "schema: spec-driven\n")
    result = subprocess.run(
        [str(python), "-I", "-c", script],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_installed_python_conditions_and_absent_optional_tools(installed, tmp_path):
    python, environment = installed
    environment = {**environment, "PATH": ""}
    isolated = python, environment
    project, home = tmp_path / "python-project", tmp_path / "home"
    write(project, "openspec/config.yaml", "schema: spec-driven\n")
    write(project, ".python-version", "3.12\n")
    write(project, "uv.lock", "version = 1\n")
    write(
        project, "pyproject.toml", '[project]\nname="consumer"\ndependencies=["zuu"]\n'
    )
    invoke(isolated, project, home, "update", "--json")
    result = invoke(isolated, project, home, "sync", "--json")
    assert "over:zuu" in result["candidate"]
    rows = invoke(isolated, project, home, "trait", "resolve", "--explain", "--json")
    assert (
        next(r for r in rows if r["name"] == "require-codegraph")["status"]
        == "unmatched"
    )
    assert next(r for r in rows if r["name"] == "require-zmem")["status"] == "unmatched"
