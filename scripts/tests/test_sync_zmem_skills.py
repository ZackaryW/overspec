"""Exercise maintenance against real local Git and an isolated Saucepan store."""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from saucepan_sdk import Saucepan, shared_executable_path

import sync_zmem_skills as sync

NAMES = ("zmem-author-commits", "zmem-query-memory", "zmem-design-extensions")


def git(repo, *args):
    return subprocess.run(["git", "-c", "user.name=Maintenance tests",
        "-c", "user.email=tests@example.invalid", "-c", "core.hooksPath=/dev/null", *args],
        cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def setup():
    binary = Path(os.environ.get("SAUCEPAN_TEST_BINARY", shared_executable_path()))
    if not binary.is_file():
        pytest.fail("Set SAUCEPAN_TEST_BINARY to a built CLI with unscoped acquisition")
    with tempfile.TemporaryDirectory(prefix="zmem-sync-") as temporary:
        root = Path(temporary)
        source = root / "source"
        source.mkdir()
        git(source, "init", "-b", "main")
        for name in NAMES:
            tree = source / "skills" / name
            (tree / "references").mkdir(parents=True)
            (tree / "SKILL.md").write_text(f"---\nname: {name}\n---\nSee references/rules.md\n")
            (tree / "references/rules.md").write_text("initial rules\n")
        git(source, "add", ".")
        git(source, "commit", "-m", "initial skills")
        dest = root / "destination"
        unrelated = dest / ".agents/skills/own/SKILL.md"
        unrelated.parent.mkdir(parents=True)
        unrelated.write_text("local skill")
        client = Saucepan(binary=binary, test_root=root / "store", test_key="19" * 32)
        client.init()
        yield dest, source, client


def inventory(root):
    return {str(path.relative_to(root)): (path.read_bytes(), path.stat().st_mtime_ns)
            for path in root.rglob("*") if path.is_file()}


def test_refresh_update_removal_provenance_and_noop_without_overspec(setup, capsys):
    dest, source, client = setup
    assert importlib.util.find_spec("overspec") is None
    assert sync.main(["--root", str(dest)], client=client, origin=source.as_uri()) == 2
    assert "review" in capsys.readouterr().out.lower()
    provenance = json.loads((dest / ".agents/zmem-skills.json").read_text())
    assert provenance["source"] == source.as_uri()
    assert provenance["revision"] == git(source, "rev-parse", "HEAD")
    assert provenance["skills"] == list(NAMES)
    for name in NAMES:
        for rel in ("SKILL.md", "references/rules.md"):
            # Compare acquired Git bytes, independent of checkout newline conversion.
            payload = git(source, "show", f"HEAD:skills/{name}/{rel}").encode() + b"\n"
            assert (dest / ".agents/skills" / name / rel).read_bytes() == payload
            assert provenance["files"][f"{name}/{rel}"] == hashlib.sha256(payload).hexdigest()
    before = inventory(dest)
    assert sync.main(["--root", str(dest)], client=client, origin=source.as_uri()) == 0
    assert inventory(dest) == before
    tree = source / "skills" / NAMES[0]
    (tree / "references/rules.md").unlink()
    (tree / "agents").mkdir()
    (tree / "agents/openai.yaml").write_text("display_name: refreshed\n")
    (tree / "SKILL.md").write_text("Updated skill\n")
    git(source, "add", ".")
    git(source, "commit", "-m", "replace support")
    assert sync.main(["--root", str(dest)], client=client, origin=source.as_uri()) == 2
    assert not (dest / ".agents/skills" / NAMES[0] / "references/rules.md").exists()
    assert (dest / ".agents/skills" / NAMES[0] / "agents/openai.yaml").read_text() == "display_name: refreshed\n"
    assert inventory(dest)[str(Path(".agents/skills/own/SKILL.md"))] == before[str(Path(".agents/skills/own/SKILL.md"))]


def test_incomplete_source_preserves_all_destinations(setup):
    dest, source, client = setup
    assert sync.main(["--root", str(dest)], client=client, origin=source.as_uri()) == 2
    before = inventory(dest)
    (source / "skills" / NAMES[-1] / "SKILL.md").unlink()
    git(source, "add", ".")
    git(source, "commit", "-m", "incomplete skill")
    assert sync.main(["--root", str(dest)], client=client, origin=source.as_uri()) == 1
    assert inventory(dest) == before


def test_subprocess_reports_missing_executable_without_application(tmp_path):
    result = subprocess.run([sys.executable, str(Path(sync.__file__)), "--root", str(tmp_path),
        "--binary", str(tmp_path / "missing")], capture_output=True, text=True)
    assert result.returncode == 1
    assert "Saucepan" in result.stderr
    assert not (tmp_path / ".agents").exists()


@pytest.mark.parametrize("fail_restore", [False, True])
def test_failed_publication_restores_or_reports_retained_backups(setup, monkeypatch, capsys, fail_restore):
    dest, source, client = setup
    assert sync.main(["--root", str(dest)], client=client, origin=source.as_uri()) == 2
    before = inventory(dest / ".agents/skills")
    provenance = (dest / ".agents/zmem-skills.json").read_bytes()
    for name in NAMES:
        (source / "skills" / name / "SKILL.md").write_text("new content\n")
    git(source, "add", ".")
    git(source, "commit", "-m", "change all skills")
    real_replace = os.replace

    def replace(src, dst):
        src, dst = Path(src), Path(dst)
        if "incoming" in src.parts and dst.name == NAMES[1]:
            raise OSError("injected publication failure")
        if fail_restore and "backup" in src.parts and dst.name == NAMES[0]:
            raise OSError("injected recovery failure")
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", replace)
    assert sync.main(["--root", str(dest)], client=client, origin=source.as_uri()) == 1
    diagnostic = capsys.readouterr().err
    assert "recovery" in diagnostic
    stages = list((dest / ".agents").glob(".zmem-sync-*"))
    assert len(stages) == 1
    assert str(stages[0]) in diagnostic
    assert (dest / ".agents/zmem-skills.json").read_bytes() == provenance
    if fail_restore:
        assert "incomplete" in diagnostic
        assert (stages[0] / "backup/.agents/skills" / NAMES[0] / "SKILL.md").read_bytes() == before[str(Path(NAMES[0]) / "SKILL.md")][0]
    else:
        assert inventory(dest / ".agents/skills") == before
