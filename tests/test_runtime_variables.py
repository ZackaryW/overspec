import json

import pytest

from conftest import declaration, source
from overspec.core import storage
from overspec.core.resolution import contributions, resolve_runtime, show_details
from test_setup_cli import invoke
from test_variable_setup import change


def runtime(project, **extra):
    source(
        project,
        declaration(
            "r", "runtime-trait", body="${x}", details="Literal ${details}", **extra
        ),
    )
    project.initialize()
    return project.sync()["resolution"]


def body(project, identity, **kwargs):
    return resolve_runtime(project.root, identity, "context", ["r"], **kwargs)[0][
        "body"
    ]


def test_runtime_precedence_deletion_and_retained_defaults(project, tmp_path):
    project.home.mkdir()
    (project.home / "config.toml").write_text('[vars]\nx="user"')
    config = source(project, '[vars]\nx="config"', "config.toml")
    persistent = source(project, '[vars]\nx="project-persistent"', ".vars.toml")
    current = source(project, '[vars]\nx="project-current"', ".current.toml")
    identity = runtime(project)
    selected = change(tmp_path / "external/one")
    cp = selected / ".vars.toml"
    cc = selected / ".current.toml"
    cp.write_text('[vars]\nx="change-persistent"')
    cc.write_text('[vars]\nx="change-current"')
    assert (
        body(project, identity, change=selected, context={"x": "explicit"})
        == "explicit"
    )
    for path, expected in [
        (cc, "change-current"),
        (cp, "change-persistent"),
        (current, "project-current"),
        (persistent, "project-persistent"),
    ]:
        assert body(project, identity, change=selected) == expected
        path.unlink()
    config.write_text('[vars]\nx="changed-config"')
    assert body(project, identity, change=selected) == "config"
    new = project.sync(values={"x": "sync-explicit"})["resolution"]
    assert body(project, new) == "sync-explicit"
    source(project, '[vars]\nx="live"', ".current.toml")
    assert body(project, new) == "live"
    assert body(project, new, context={"x": None}) == "null"


def test_v2_format_namespace_and_root_validation(project, tmp_path):
    source(project, '[vars]\nx="ephemeral"', ".current.toml")
    identity = runtime(project)
    bundle = storage.load_bundle(project.root, "resolutions", identity)
    assert bundle["version"] == 2 and bundle["runtime_defaults"] == {}
    assert identity == storage.digest(project.prepare())
    assert "ephemeral" not in str(bundle["runtime_defaults"])
    state = storage.read_state(project.root)
    compiled = state["compilation"]
    state["compilation"] = storage.section(bundle)
    project.state.write_bytes(storage.encoded(state))
    with pytest.raises(ValueError, match="Corrupt"):
        storage.load_bundle(project.root, "compilations", identity)
    bundle["root"] = str(tmp_path)
    state["compilation"] = compiled
    state["root"] = str(tmp_path)
    state["resolution"] = storage.section(bundle)
    project.state.write_bytes(storage.encoded(state))
    with pytest.raises(ValueError, match="root"):
        storage.load_bundle(project.root, "resolutions", identity)


def test_matching_and_rendering_share_live_mapping(project, tmp_path):
    source(
        project,
        '[vars]\nx="project"\nflag=false\nitems=["a", "b"]\nwanted=["b"]',
        ".current.toml",
    )
    identity = runtime(
        project,
        **{
            "assert": [
                {"type": "runtime-context-match", "kv": "flag=true"},
                {
                    "type": "runtime-context-includes",
                    "k": "items",
                    "includes": "$wanted",
                },
            ]
        },
    )
    selected = change(tmp_path / "one")
    selected.joinpath(".vars.toml").write_text('[vars]\nx="change"\nflag=true')
    assert body(project, identity, change=selected) == "change"
    for context in [{"flag": 1}, {"flag": False}, {"items": ["c"]}, {"wanted": ["z"]}]:
        assert (
            resolve_runtime(
                project.root, identity, "context", ["r"], context, change=selected
            )
            == []
        )
    assert resolve_runtime(project.root, identity, "context", ["r"]) == []


def test_scope_isolation_invalid_moved_and_metadata(project, tmp_path):
    identity = runtime(project)
    one, two = change(tmp_path / "one"), change(tmp_path / "two")
    one.joinpath(".vars.toml").write_text('[vars]\nx="one"')
    two.joinpath(".vars.toml").write_text('[vars]\nx="two"')
    assert body(project, identity, change=one) == "one"
    assert body(project, identity, change=two) == "two"
    assert body(project, identity, context={"x": "project-only"}) == "project-only"
    moved = tmp_path / "moved"
    one.rename(moved)
    for invalid in [one, tmp_path, two / ".vars.toml"]:
        with pytest.raises(ValueError):
            body(project, identity, change=invalid)
    two.joinpath(".openspec.yaml").write_text("[]")
    with pytest.raises(ValueError, match="metadata"):
        body(project, identity, change=two)
    assert body(project, identity, change=moved) == "one"


def test_legacy_resolution_data_requires_regeneration(project):
    identity = runtime(project)
    state = storage.read_state(project.root)
    bundle = state["resolution"]["data"]
    bundle["version"] = 1
    bundle.pop("runtime_defaults")
    state["resolution"] = storage.section(bundle)
    project.state.write_bytes(storage.encoded(state))
    before = project.state.read_bytes()
    with pytest.raises(ValueError, match="Corrupt"):
        body(project, identity, context={"x": "explicit"})
    assert project.state.read_bytes() == before


def test_runtime_cli_projection_and_details_are_readonly(project, tmp_path):
    identity = runtime(project)
    selected = change(tmp_path / "one")
    selected.joinpath(".vars.toml").write_text('[vars]\nx="[bold]literal[/bold]"')
    guidance = contributions(project.prepare(), identity)[0]["body"]
    assert guidance.count("overspec trait resolve") == 1
    assert (
        "--change-root" in guidance and "OpenSpec" in guidance and "store" in guidance
    )
    assert str(selected) not in guidance
    command = [
        "trait",
        "resolve",
        "--resolution",
        identity,
        "--attach",
        "context",
        "--trait",
        "r",
        "--change-root",
        str(selected),
    ]
    before = {
        p: (p.read_bytes(), p.stat().st_mtime_ns)
        for root in [project.root, selected]
        for p in root.rglob("*")
        if p.is_file()
    }
    result = invoke(project, *command)
    assert (
        result.exit_code == 0
        and result.stdout == "[bold]literal[/bold]\n<!-- over:r -->\n"
    )
    assert before == {
        p: (p.read_bytes(), p.stat().st_mtime_ns)
        for root in [project.root, selected]
        for p in root.rglob("*")
        if p.is_file()
    }
    assert not (project.over / ".current.toml").exists()
    assert not (project.root / ".gitignore").exists()
    assert (
        invoke(project, "trait", "resolve", "--change-root", str(selected)).exit_code
        != 0
    )
    source(project, "invalid", ".current.toml")
    assert show_details(project.root, "r", identity)["details"] == "Literal ${details}"
    result = invoke(
        project, "trait", "show", "r", "--details", "--resolution", identity, "--json"
    )
    assert (
        result.exit_code == 0
        and json.loads(result.stdout)["details"] == "Literal ${details}"
    )


def test_redirected_scope_and_variable_targets_are_rejected(project, tmp_path):
    import os
    import subprocess
    from overspec.core.setup import setup_variables

    selected = change(tmp_path / "outside")
    selected.joinpath(".current.toml").write_text('[vars]\nx="outside"')
    alias = tmp_path / "alias"
    if os.name == "nt":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(alias), str(selected)],
            check=True,
            capture_output=True,
        )
    else:
        alias.symlink_to(selected, target_is_directory=True)
    identity = runtime(project)
    with pytest.raises(ValueError):
        body(project, identity, change=alias)
    with pytest.raises(ValueError):
        setup_variables(project.root, [alias])
    assert not (project.over / ".current.toml").exists()
    target = project.over / ".current.toml"
    target.mkdir()
    with pytest.raises(ValueError):
        body(project, identity)


def test_live_resolution_and_details_ignore_profile_changes(project):
    from overspec.core.profiles import toggle_profiles

    identity = runtime(project)
    toggle_profiles(project.home)
    # A now-invalid profile source cannot replace retained definitions or details.
    source(project, "invalid", "profile-default/traits.toml")
    source(project, '[vars]\nx="live"', ".current.toml")
    assert body(project, identity) == "live"
    assert show_details(project.root, "r", identity)["details"] == "Literal ${details}"
