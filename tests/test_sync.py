import pytest

from conftest import declaration, source


def snapshot(root):
    return {
        p.relative_to(root): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file()
    }


def test_sync_preview_noop_and_details_history(project):
    from overspec.core.resolution import show_details

    path = source(
        project,
        declaration(
            "tdd",
            body="Small body",
            attach="operations.apply.guidance",
            details="Long ${literal} details",
        ),
    )
    project.initialize()
    before = snapshot(project.root)
    preview = project.sync(dry_run=True)
    assert preview["changed"] and "Small body" in preview["candidate"]
    assert "Long" not in preview["candidate"] and preview["diff"]
    assert snapshot(project.root) == before
    result = project.sync()
    before = snapshot(project.root)
    assert not project.sync()["changed"]
    assert snapshot(project.root) == before
    assert show_details(project.root, "tdd")["details"] == "Long ${literal} details"
    path.write_text(
        declaration(
            "tdd", body="Small body", attach="operations.apply.guidance", details="New"
        )
    )
    assert show_details(project.root, "tdd")["details"] == "Long ${literal} details"
    config = project.root / "openspec/config.yaml"
    mtime = config.stat().st_mtime_ns
    changed = project.sync()
    assert not changed["changed"] and config.stat().st_mtime_ns == mtime
    assert show_details(project.root, "tdd")["details"] == "New"
    assert (
        show_details(project.root, "tdd", result["resolution"])["details"]
        == "Long ${literal} details"
    )
    config.write_text(config.read_text() + "custom: preserved\n")
    assert show_details(project.root, "tdd")["details"] == "New"
    config.write_text(config.read_text().replace("# over:tdd", "# over:wrong"))
    with pytest.raises(ValueError, match="stale|resync"):
        show_details(project.root, "tdd")
    assert show_details(project.root, "tdd", changed["resolution"])["details"] == "New"


def test_details_absent_unknown_and_missing_state(project):
    from overspec.core.resolution import show_details

    with pytest.raises(ValueError):
        show_details(project.root, "a")
    source(project, declaration("a"))
    project.initialize()
    project.sync()
    assert show_details(project.root, "a")["details"] is None
    with pytest.raises(ValueError, match="Unknown"):
        show_details(project.root, "missing")


def test_yaml_fallback_and_precedence(project):
    root = project.root / "openspec"
    (root / "config.yaml").rename(root / "config.yml")
    project.initialize()
    assert project.sync()["path"] == str(root / "config.yml")
    (root / "config.yaml").write_text("schema: spec-driven\n")
    assert project.sync()["path"] == str(root / "config.yaml")
    (root / "config.yaml").unlink()
    (root / "config.yml").unlink()
    with pytest.raises(ValueError, match="Missing"):
        project.sync()


def test_failed_replace_keeps_config_and_cleans_temporary_file(project, monkeypatch):
    import overspec.core.storage as storage

    source(project, declaration("a", "runtime-trait"))
    project.initialize()
    before = (project.root / "openspec/config.yaml").read_bytes()
    replace = storage.os.replace

    def fail_config(src, dst):
        if str(dst).endswith("config.yaml"):
            raise OSError("injected config failure")
        return replace(src, dst)

    monkeypatch.setattr(storage.os, "replace", fail_config)
    with pytest.raises(OSError):
        project.sync()
    assert (project.root / "openspec/config.yaml").read_bytes() == before
    assert list((project.state / "resolutions").glob("*.json"))
    assert not list((project.root / "openspec").glob(".over-*"))


def test_receipt_failure_reports_partial_outcome_and_retry(project, monkeypatch):
    import overspec.core.storage as storage

    source(project, declaration("a"))
    project.initialize()
    replace = storage.os.replace

    def fail_receipt(src, dst):
        if str(dst).endswith("last-sync.json"):
            raise OSError("injected receipt failure")
        return replace(src, dst)

    monkeypatch.setattr(storage.os, "replace", fail_receipt)
    with pytest.raises(ValueError, match="configuration may already"):
        project.sync()
    monkeypatch.setattr(storage.os, "replace", replace)
    assert not project.sync()["changed"]


def test_intervening_source_or_config_edit_aborts(project, monkeypatch):
    import overspec.core.storage as storage

    path = source(project, declaration("a"))
    project.initialize()
    publish = storage.publish

    def intervene(*args):
        result = publish(*args)
        path.write_text(declaration("a", body="intervening"))
        return result

    monkeypatch.setattr(storage, "publish", intervene)
    before = (project.root / "openspec/config.yaml").read_bytes()
    with pytest.raises(ValueError, match="changed"):
        project.sync()
    assert (project.root / "openspec/config.yaml").read_bytes() == before
