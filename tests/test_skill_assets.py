import zipfile

import pytest

from overspec.core import skill_assets


def test_editable_catalog_is_anchored_and_materializes_support(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    catalog = skill_assets.skill_catalog()
    assert "overspec-bootstrap" in {item.name for item in catalog}
    with skill_assets.materialize_skills(["overspec-bootstrap"]) as sources:
        assert len(sources) == 1
        assert (sources[0].path / "references/controls.md").is_file()
        assert sources[0].origin.startswith("package:overspec/")


def test_missing_payload_and_unknown_selection(monkeypatch, tmp_path):
    with (
        pytest.raises(ValueError, match="Unknown"),
        skill_assets.materialize_skills(["not-in-package"]),
    ):
        pass
    monkeypatch.setattr(skill_assets, "resource_tree", lambda *args: tmp_path)
    with pytest.raises(ValueError, match="Missing"):
        skill_assets.skill_catalog()


def test_archive_resources_keep_support_alive_until_exit(monkeypatch, tmp_path):
    archive = tmp_path / "skills.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr(
            "skills/reviewer/SKILL.md",
            "---\nname: reviewer\ndescription: Review\n---\n",
        )
        output.writestr("skills/reviewer/references/check.md", "support")
    with zipfile.ZipFile(archive) as source:
        tree = zipfile.Path(source, "skills/")
        monkeypatch.setattr(skill_assets, "resource_tree", lambda *args: tree)
        with skill_assets.materialize_skills(["reviewer"]) as sources:
            extracted = sources[0].path
            assert (extracted / "references/check.md").read_text() == "support"
        assert not extracted.exists()
