from overspec.core import storage
import json
import re
import shlex
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

from conftest import declaration, source
from overspec.core.profiles import profiles_enabled, toggle_profiles
from test_setup_cli import invoke
from test_variable_setup import git


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("external", [False, True])
def test_bootstrap_with_real_openspec_and_two_changes(
    project, tmp_path, monkeypatch, enabled, external
):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("OPENSPEC_TELEMETRY", "0")
    executable = shutil.which("openspec")
    assert executable, "Companion OpenSpec is required"

    def openspec(*args):
        result = subprocess.run(
            [executable, *args], cwd=project.root, capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr
        return result.stdout

    git(project.root, "init", "-q")
    openspec("init", "--tools", "none", "--no-animation")
    suffix = []
    if external:
        store = tmp_path / "store"
        openspec(
            "store",
            "setup",
            "test-scoped",
            "--path",
            str(store),
            "--no-init-git",
            "--json",
        )
        git(store, "init", "-q")
        suffix = ["--store", "test-scoped"]
    if enabled:
        toggle_profiles(project.home)
    source(
        project,
        declaration("static", body="Shared ${language}")
        + declaration(
            "runtime",
            "runtime-trait",
            body="Review ${language}",
            attach="operations.apply.guidance",
            **{"assert": [{"type": "runtime-context-match", "kv": "strict=true"}]},
        ),
        "profile-default/traits.toml",
    )
    source(project, '[vars]\nlanguage="project"\nstrict=true', ".vars.toml")
    openspec("new", "change", "one", *suffix)
    first = invoke(project, "init", *suffix, "--json")
    assert first.exit_code == 0, first.output
    pointer = storage.read_state(project.root)["compilation"]
    one = Path(
        json.loads(openspec("status", "--change", "one", "--json", *suffix))[
            "changeRoot"
        ]
    )
    assert (one / ".current.toml").exists()
    # A later change needs setup, not recompilation.
    openspec("new", "change", "two", *suffix)
    two = Path(
        json.loads(openspec("status", "--change", "two", "--json", *suffix))[
            "changeRoot"
        ]
    )
    result = invoke(
        project, "init", "--setup-only", "--change-root", str(two), "--json"
    )
    assert result.exit_code == 0, result.output
    assert storage.read_state(project.root)["compilation"] == pointer
    assert profiles_enabled(project.home) is enabled
    for root, language in [(one, "one"), (two, "two")]:
        assert (root / ".current.toml").exists()
        assert not (root / ".vars.toml").exists()
        (root / ".vars.toml").write_text(f'[vars]\nlanguage="{language}"')
        (root / "tasks.md").write_text("## Work\n- [ ] 1.1 Review\n")
    preview = invoke(project, "sync", "--dry-run", "--json")
    assert preview.exit_code == 0, preview.output
    assert "Shared project" in json.loads(preview.stdout)["candidate"]
    result = invoke(project, "sync", "--json")
    assert result.exit_code == 0, result.output
    assert not json.loads(invoke(project, "sync", "--json").stdout)["changed"]
    # The owning project's generated command is read by OpenSpec. Store operations
    # own another config; obtain shared command from the owning project's config.
    from overspec.core.projection import parse_yaml

    guidance = parse_yaml((project.root / "openspec/config.yaml").read_text())[
        "operations"
    ]["apply"]["guidance"][0]
    command = shlex.split(
        next(
            line
            for line in guidance.splitlines()
            if line.startswith("overspec trait resolve")
        )
    )[1:]
    before = {
        p: (p.read_bytes(), p.stat().st_mtime_ns)
        for root in [one, two]
        for p in root.rglob("*")
        if p.is_file()
    }
    for root, language in [(one, "one"), (two, "two")]:
        result = invoke(project, *command, "--change-root", str(root))
        assert (
            result.exit_code == 0
            and result.stdout == f"Review {language}\n<!-- over:runtime -->\n"
        )
    assert invoke(project, *command).stdout == "Review project\n<!-- over:runtime -->\n"
    assert before == {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before}
    for root in [one, two]:
        assert git(root, "check-ignore", "--no-index", ".current.toml")
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "-q", ".vars.toml"], cwd=root
        )
        assert result.returncode == 1
    (project.over / ".vars.toml").write_text('[vars]\nlanguage="updated"\nstrict=true')
    # Ordinary values refresh at sync; update remains an explicit supported command.
    assert invoke(project, "update", "--json").exit_code == 0
    assert invoke(project, "trait", "resolve", "--explain").exit_code == 0


def test_documented_toml_and_help_are_executable():
    from typer.testing import CliRunner
    from overspec.cli import app
    from overspec.core.trait_system.sources import parse_document

    root = Path(__file__).resolve().parents[1]
    for relative in [
        "README.md",
        ".agents/skills/overspec-create-trait/references/trait-format.md",
        ".agents/skills/overspec-bootstrap/references/controls.md",
    ]:
        for text in re.findall(
            r"```toml\n(.*?)```", (root / relative).read_text(encoding="utf-8"), re.S
        ):
            data = tomllib.loads(text)
            if any(
                key in data for key in ["trait", "runtime-trait", "compiletime-trait"]
            ):
                parse_document(text, relative)
    for args, options in [
        (["init", "--help"], ["--setup-only", "--change-root", "--store"]),
        (["trait", "resolve", "--help"], ["--change-root", "--context-file"]),
        (["trait", "show", "--help"], ["--details", "--resolution"]),
    ]:
        result = CliRunner().invoke(app, args, terminal_width=160)
        assert result.exit_code == 0
        assert all(option in result.stdout for option in options)
