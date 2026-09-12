"""Release artifacts must work without a second source checkout."""

import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
AUTHORED = Path("openspec/.over/profile-default")
BUNDLED = "overspec/_bundled/profile-default/"


def run_build(root, output, *arguments):
    return subprocess.run(
        ["uv", "build", str(root), "--out-dir", str(output), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def build_tree(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    for name in ("pyproject.toml", "README.md", "uv.lock", "hatch_build.py"):
        if (REPO / name).exists():
            shutil.copyfile(REPO / name, root / name)
    shutil.copytree(
        REPO / "src", root / "src", ignore=shutil.ignore_patterns("__pycache__")
    )
    shutil.copytree(REPO / AUTHORED, root / AUTHORED)
    shutil.copytree(REPO / '.agents/skills', root / '.agents/skills')
    shutil.copytree(REPO / 'openspec/schemas/overspec', root / 'openspec/schemas/overspec')
    return root


def wheel_traits(path):
    with zipfile.ZipFile(path) as wheel:
        return {
            name[len(BUNDLED) :]: wheel.read(name)
            for name in wheel.namelist()
            if name.startswith(BUNDLED)
        }


def test_release_and_sdist_wheels_contain_only_authored_traits(build_tree, tmp_path):
    profile = build_tree / AUTHORED
    nested = profile / "nested/trait-example.toml"
    nested.parent.mkdir()
    nested.write_text('[[trait]]\nname="example"\nbody="example"\nattach="context"\n')
    for name in (
        "notes.toml",
        ".current.toml",
        ".vars.toml",
        ".state.json",
        ".state/trait-hidden.toml",
    ):
        path = profile / name
        path.parent.mkdir(exist_ok=True)
        path.write_text("not a trait")
    for name in (
        "openspec/config.yaml",
        "openspec/changes/example/trait-hidden.toml",
        "openspec/.over/profile-strict/trait-hidden.toml",
        ".agents/reports/example.md",
    ):
        path = build_tree / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not package content")
    expected = {
        p.relative_to(profile).as_posix(): p.read_bytes()
        for p in profile.rglob("trait*.toml")
        if ".state" not in p.parts
    }
    result = run_build(build_tree, tmp_path / "dist")
    assert result.returncode == 0, result.stderr
    wheel = next((tmp_path / "dist").glob("*.whl"))
    assert wheel_traits(wheel) == expected
    def assets(wheel_path):
        with zipfile.ZipFile(wheel_path) as archive:
            return {n: archive.read(n) for n in archive.namelist()
                    if n.startswith(('overspec/_bundled/skills/', 'overspec/_bundled/schemas/'))}
    expected_assets = {}
    for source, destination in [('.agents/skills', 'skills'), ('openspec/schemas/overspec', 'schemas/overspec')]:
        for path in (build_tree / source).rglob('*'):
            if destination == 'skills' and not (build_tree / source / path.relative_to(build_tree / source).parts[0] / 'SKILL.md').is_file():
                continue
            if path.is_file() and '__pycache__' not in path.parts:
                expected_assets[f'overspec/_bundled/{destination}/{path.relative_to(build_tree / source).as_posix()}'] = path.read_bytes()
    assert assets(wheel) == expected_assets
    extracted = tmp_path / "extracted"
    with tarfile.open(next((tmp_path / "dist").glob("*.tar.gz"))) as archive:
        archive.extractall(extracted, filter="data")
    result = run_build(next(extracted.iterdir()), tmp_path / "rebuilt", "--wheel")
    assert result.returncode == 0, result.stderr
    assert wheel_traits(next((tmp_path / "rebuilt").glob("*.whl"))) == expected
    assert assets(next((tmp_path / 'rebuilt').glob('*.whl'))) == expected_assets
    with zipfile.ZipFile(wheel) as archive:
        assert not any(
            n.startswith(("openspec/", ".agents/")) for n in archive.namelist()
        )


@pytest.mark.parametrize("failure", ["missing", "malformed"])
def test_bad_authored_default_fails_build(build_tree, tmp_path, failure):
    profile = build_tree / AUTHORED
    if failure == "missing":
        profile.rename(profile.with_name("unused"))
    else:
        (profile / "trait-invalid.toml").write_text("[[broken")
    result = run_build(build_tree, tmp_path / "dist", "--wheel")
    assert result.returncode != 0, "Build silently accepted invalid default content"


def test_unreadable_trait_fails_build(build_tree, tmp_path):
    # Inject a read failure at the filesystem boundary, portable across Windows ACLs.
    hook = build_tree / "hatch_build.py"
    with hook.open("a") as stream:
        stream.write("""
original_read = Path.read_text
def denied_read(path, *args, **kwargs):
    if path.name == "trait-tdd.toml":
        raise PermissionError("test unreadable trait")
    return original_read(path, *args, **kwargs)
Path.read_text = denied_read
""")
    result = run_build(build_tree, tmp_path / "dist", "--wheel")
    assert result.returncode != 0
    assert "test unreadable trait" in result.stderr


def test_redirected_trait_directory_fails_build(build_tree, tmp_path):
    import os

    target = tmp_path / "redirect-target"
    target.mkdir()
    (target / "trait-redirect.toml").write_text("[[trait]]")
    link = build_tree / AUTHORED / "redirect"
    if os.name == "nt":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
    else:
        link.symlink_to(target, target_is_directory=True)
    result = run_build(build_tree, tmp_path / "dist", "--wheel")
    assert result.returncode != 0
    assert "Redirected default profile path" in result.stderr


def test_missing_schema_template_fails_build(build_tree, tmp_path):
    (build_tree / 'openspec/schemas/overspec/templates/tasks.md').unlink()
    result = run_build(build_tree, tmp_path / 'dist', '--wheel')
    assert result.returncode != 0
    assert 'template' in result.stderr.lower()
