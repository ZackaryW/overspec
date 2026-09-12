from contextlib import contextmanager

import pytest

from overspec.core import skill_assets
from overspec.core.skills import Skills


@pytest.fixture
def managed(tmp_path, monkeypatch):
    source = tmp_path / "source/reviewer"
    (source / "references").mkdir(parents=True)
    (source / "SKILL.md").write_text(
        "---\nname: reviewer\ndescription: Review code\n---\nVersion A\n"
    )
    (source / "references/checks.md").write_text("A support")
    catalog = [
        skill_assets.SkillAsset(
            "reviewer",
            "package:overspec/skills/reviewer",
            "1",
            ("SKILL.md", "references/checks.md"),
        )
    ]
    monkeypatch.setattr(skill_assets, "skill_catalog", lambda: tuple(catalog))

    @contextmanager
    def sources(names):
        yield tuple(
            skill_assets.SkillSource(n, source, f"package:overspec/skills/{n}")
            for n in names
        )

    monkeypatch.setattr(skill_assets, "materialize_skills", sources)
    return tmp_path, source, catalog


def call(manager, command, **kwargs):
    return manager.run(command, agents=["kimi"], names=["reviewer"], **kwargs)


def test_public_lifecycle_restart_restore_and_historical_removal(managed):
    root, source, catalog = managed
    manager = Skills(root / "state", root / "native")
    assert call(manager, "status")["results"][0]["classification"] == "absent"
    installed = call(manager, "install")
    assert installed["ok"], installed
    target = root / "native/.kimi-code/skills/reviewer"
    before = {
        p.relative_to(target).as_posix(): p.read_bytes()
        for p in target.rglob("*")
        if p.is_file()
    }
    assert call(manager, "update")["results"][0]["changed"] is False
    (source / "references/checks.md").write_text("B support")
    updated = call(manager, "update")
    assert updated["ok"], updated
    operation = updated["results"][0]["operation_id"]
    assert (target / "references/checks.md").read_text() == "B support"
    manager = Skills(root / "state", root / "native")
    catalog.clear()
    restored = call(manager, "restore", operation_id=operation)
    assert restored["ok"], restored
    assert {
        p.relative_to(target).as_posix(): p.read_bytes()
        for p in target.rglob("*")
        if p.is_file()
    } == before
    history = call(manager, "history")
    assert operation in {e["operation_id"] for e in history["history"]}
    assert call(manager, "remove")["ok"]
    assert not target.exists()


def test_conflict_force_restore_and_native_home_binding(managed):
    root, _source, _ = managed
    manager = Skills(root / "state", root / "native")
    target = root / "native/.kimi-code/skills/reviewer"
    target.mkdir(parents=True)
    document = target / "SKILL.md"
    document.write_text(
        "---\nname: reviewer\ndescription: Local\n---\nPrivate custom text\n"
    )
    before = document.read_bytes()
    assert not call(manager, "install")["ok"]
    assert not call(manager, "update")["ok"]
    assert document.read_bytes() == before
    updated = call(manager, "update", force=True)
    assert updated["ok"], updated
    document.write_text("---\nname: reviewer\ndescription: Local\n---\nLater edits\n")
    operation = updated["results"][0]["operation_id"]
    assert not call(manager, "restore", operation_id=operation)["ok"]
    assert call(manager, "restore", operation_id=operation, force=True)["ok"]
    assert document.read_bytes() == before
    assert call(manager, "status")["results"][0]["classification"] == "unowned"
    assert not call(manager, "remove")["ok"]
    assert document.read_bytes() == before
    with pytest.raises(ValueError, match="home"):
        call(
            Skills(root / "state", root / "other-native"),
            "restore",
            operation_id=operation,
        )


def test_partial_install_history_filter_and_undo_install(managed):
    root, _source, catalog = managed
    catalog.append(
        skill_assets.SkillAsset(
            "wrong-name", "package:overspec/skills/wrong-name", "1", ("SKILL.md",)
        )
    )
    manager = Skills(root / "state", root / "native")
    result = manager.run("install", agents=["kimi"], all_skills=True)
    assert not result["ok"]
    assert result["results"][0]["ok"] and not result["results"][1]["ok"]
    target = root / "native/.kimi-code/skills/reviewer"
    assert target.is_dir()
    operation = result["results"][0]["operation_id"]
    assert call(manager, "restore", operation_id=operation)["ok"]
    assert not target.exists()
    with pytest.raises(ValueError, match="Unknown"):
        call(manager, "restore", operation_id="op_unrelated")


def test_removal_keeps_prior_outcomes_on_native_exception(managed, monkeypatch):
    from zuat.pub import Zuat

    root, source, _ = managed
    manager = Skills(root / "state", root / "native")
    assert call(manager, "install")["ok"]
    # A second recorded identity need not remain in the current package catalog.
    source.joinpath("SKILL.md").write_text(
        "---\nname: second\ndescription: Second skill\n---\nSecond body\n"
    )
    from zuat.pub import AssetInput, ZuatRequest

    with Zuat(root=manager.registry, home=manager.agent_home) as service:
        assert service.install(
            ZuatRequest(
                agents=("kimi",),
                assets=(AssetInput("kimi", "skill", scope="user", source=str(source)),),
            )
        ).ok
    uninstall = Zuat.uninstall
    calls = 0

    def fail_second(self, request):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("Native removal interrupted")
        return uninstall(self, request)

    monkeypatch.setattr(Zuat, "uninstall", fail_second)
    result = manager.run("remove", agents=["kimi"], all_skills=True)
    assert not result["ok"]
    first, second = result["results"]
    assert first["ok"] and first["operation_id"]
    assert not second["ok"] and "interrupted" in second["diagnostics"][0]
    assert not (root / "native/.kimi-code/skills/reviewer").exists()
    assert (root / "native/.kimi-code/skills/second/SKILL.md").exists()
