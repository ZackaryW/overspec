import pytest

from conftest import declaration, source


def test_compiletime_frozen_and_ordinary_fresh(project, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    compile_source = declaration(
        "tool", "compiletime-trait", **{"assert": [{"type": "which", "app": "tool"}]}
    )
    source(project, compile_source, "trait-compile.toml")
    ordinary = source(project, declaration("ordinary", body="first", details="long"))
    with pytest.raises(ValueError, match="init|update"):
        project.prepare()
    project.initialize()
    monkeypatch.setattr("shutil.which", lambda _: "/tool")
    first = project.prepare()
    assert first["static"]["matched"] == ["ordinary"]
    ordinary.write_text(declaration("ordinary", body="second", details="new details"))
    second = project.prepare()
    assert second["static"]["bodies"] == {"ordinary": "second"}
    assert second["traits"][1]["declaration"]["details"] == "new details"
    project.initialize(update=True)
    assert project.prepare()["static"]["matched"] == ["ordinary", "tool"]
    with pytest.raises(ValueError, match="update"):
        project.initialize()


def test_compilation_compatibility_tracks_relevant_inputs(project):
    path = source(
        project,
        declaration(
            "compiled", "compiletime-trait", body="Use ${language}", details="old"
        ),
    )
    settings = source(project, '[vars]\nlanguage="Python"\n', "config.toml")
    project.initialize()
    source(
        project,
        declaration("runtime", "runtime-trait", body="${later}"),
        "trait-runtime.toml",
    )
    assert project.prepare()["static"]["bodies"]["compiled"] == "Use Python"
    settings.write_text('[vars]\nlanguage="Python"\nunrelated=1\n')
    project.prepare()
    settings.write_text('[vars]\nlanguage="Rust"\n')
    with pytest.raises(ValueError, match="update"):
        project.prepare()
    project.initialize(update=True)
    path.write_text(
        declaration(
            "compiled", "compiletime-trait", body="Use ${language}", details="new"
        )
    )
    with pytest.raises(ValueError, match="update"):
        project.prepare()


def test_empty_compilation_and_readonly_preparation(project):
    project.initialize()

    def snapshot():
        return {
            p.relative_to(project.root): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in project.root.rglob("*")
            if p.is_file()
        }

    before = snapshot()
    assert project.prepare()["traits"] == []
    assert snapshot() == before


def test_compilation_publication_failure_preserves_previous(project, monkeypatch):
    import overspec.core.storage as storage

    source(project, declaration("a", "compiletime-trait"))
    project.initialize()
    before = (project.state / "compiled.json").read_bytes()

    def fail(*args):
        raise OSError("injected replace failure")

    monkeypatch.setattr(storage.os, "replace", fail)
    source(project, declaration("a", "compiletime-trait", body="changed"))
    with pytest.raises(OSError):
        project.initialize(update=True, values={"extra": "changed"})
    assert (project.state / "compiled.json").read_bytes() == before
