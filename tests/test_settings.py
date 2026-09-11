import pytest

from conftest import declaration, source
from overspec.core import storage
from overspec.core.resolution import explain


def test_setting_toggles_publication_without_recompiling(project, monkeypatch):
    source(project, declaration("policy", "compiletime-trait", setting="policy",
        **{"assert": [{"type": "which", "app": "tool"}]}))
    monkeypatch.setattr("shutil.which", lambda _: "/tool")
    project.initialize()
    compiled = storage.read_state(project.root)["compilation"]
    assert "policy" in project.sync()["candidate"]

    def unexpected_check(_):
        raise AssertionError("compile-time assertion reran during sync")

    monkeypatch.setattr("shutil.which", unexpected_check)
    settings = source(project, '[vars]\npolicy=false', ".vars.toml")
    assert "over:policy" not in project.sync()["candidate"]
    bundle = project.prepare()
    assert "policy" in bundle["static"]["matched"]
    assert explain(bundle)[0]["decision"]["setting"] == {"key": "policy", "enabled": False}
    settings.write_text('[vars]\npolicy=true\nunrelated="unchecked"')
    assert "over:policy" in project.sync()["candidate"]
    assert storage.read_state(project.root)["compilation"] == compiled
    assert not project.sync()["changed"]


def test_setting_does_not_enable_failed_compilation(project, monkeypatch):
    source(project, declaration("policy", "compiletime-trait", setting="policy",
        **{"assert": [{"type": "which", "app": "tool"}]}))
    monkeypatch.setattr("shutil.which", lambda _: None)
    project.initialize()
    monkeypatch.setattr("shutil.which", lambda _: "/tool")
    assert "over:policy" not in project.sync(values={"policy": True})["candidate"]
    project.initialize(update=True)
    assert "over:policy" in project.sync(values={"policy": True})["candidate"]


@pytest.mark.parametrize("value", ["false", 1])
def test_nonboolean_setting_fails_before_publication(project, value):
    source(project, declaration("policy", "compiletime-trait", setting="policy"))
    project.initialize()
    before = (project.root / "openspec/config.yaml").read_bytes()
    with pytest.raises(ValueError, match="policy.*boolean"):
        project.sync(values={"policy": value})
    assert (project.root / "openspec/config.yaml").read_bytes() == before


@pytest.mark.parametrize("phase,setting", [("trait", "policy"), ("compiletime-trait", " ")])
def test_invalid_setting_declaration_is_rejected(project, phase, setting):
    source(project, declaration("policy", phase, setting=setting))
    with pytest.raises(ValueError, match="setting (is|must)"):
        project.inventory()
