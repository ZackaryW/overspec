from overspec.core import storage
import pytest
from conftest import declaration, source

from overspec.core.resolution import resolve_runtime


def group(*assertions, any_=False):
    return {"or": any_, "assertion": list(assertions)}


def test_groups_keep_phase_lifetimes_and_live_runtime_sources(project, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    compiled = source(
        project,
        declaration(
            "compiled",
            "compiletime-trait",
            **{"assert": {"1": group({"type": "which", "app": "compiler"})}},
        ),
        "trait-compile.toml",
    )
    ordinary = source(
        project,
        declaration(
            "ordinary",
            **{
                "assert": {
                    "or": True,
                    "1": group({"type": "loaded-trait", "trait": "compiled"}),
                    "2": group({"type": "files-exist", "paths": ["ready"]}),
                },
                "actions": [{"type": "remove-trait", "trait": "compiled"}],
            },
        ),
    )
    runtime = source(
        project,
        declaration(
            "runtime",
            "runtime-trait",
            **{
                "assert": {
                    "1": group({"type": "loaded-trait", "trait": "ordinary"}),
                    "2": group(
                        {"type": "runtime-context-match", "kv": "flag=true"},
                        {"type": "runtime-context-match", "kv": "override=true"},
                        any_=True,
                    ),
                }
            },
        ),
        "trait-runtime.toml",
    )
    project.initialize()
    monkeypatch.setattr("shutil.which", lambda _: "/compiler")
    assert project.prepare()["static"]["matched"] == []
    (project.root / "ready").touch()
    result = project.sync()
    first = result["resolution"]
    assert result["candidate"].count("overspec trait resolve") == 1
    assert "compiled" not in project.prepare()["static"]["matched"]
    assert [
        item["name"]
        for item in resolve_runtime(
            project, "context", ["runtime"], {"override": True}
        )
    ] == ["runtime"]
    assert resolve_runtime(project, "context", ["runtime"], {}) == []

    pointer = storage.read_state(project.root)["compilation"]
    ordinary.write_text(
        declaration(
            "ordinary",
            **{"assert": {"1": group({"type": "loaded-trait", "trait": "compiled"})}},
        )
    )
    second = project.sync()["resolution"]
    assert (
        resolve_runtime(project, "context", ["runtime"], {"flag": True})
        == []
    )
    assert storage.read_state(project.root)["compilation"] == pointer
    project.initialize(update=True)
    assert project.prepare()["static"]["matched"] == ["compiled", "ordinary"]
    # A compile-time condition edit requires deliberate recompilation.
    compiled.write_text(
        compiled.read_text().replace('app = "compiler"', 'app = "different"')
    )
    with pytest.raises(ValueError, match="update"):
        project.prepare()
    runtime.write_text(declaration("runtime", "runtime-trait", body="Changed"))
    before = {
        p: (p.read_bytes(), p.stat().st_mtime_ns)
        for p in project.root.rglob("*")
        if p.is_file()
    }
    assert (
        resolve_runtime(project, "context", ["runtime"], {"flag": True})[0]["body"]
        == "Changed"
    )
    assert before == {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before}


def test_flat_conditions_change_to_groups_without_sync(project):
    legacy = [
        {"type": "runtime-context-match", "kv": "flag=true"},
        {"type": "~runtime-context-match", "kv": "blocked=true"},
    ]
    path = source(
        project,
        declaration(
            "runtime", "runtime-trait", **{"assert": legacy, "assert_or_grouping": True}
        ),
    )
    project.initialize()
    old = project.sync()["resolution"]
    assert resolve_runtime(
        project, "context", ["runtime"], {"flag": True, "blocked": True}
    )
    path.write_text(
        declaration("runtime", "runtime-trait", **{"assert": {"1": group(*legacy)}})
    )
    assert not resolve_runtime(
        project, "context", ["runtime"], {"flag": True, "blocked": True}
    )
    assert storage.read_state(project.root)["resolution"]["id"] == old
