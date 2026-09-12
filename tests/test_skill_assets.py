from pathlib import Path

import pytest

from overspec.core import skill_assets


def test_editable_catalog_is_anchored_and_materializes_support(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    catalog = skill_assets.skill_catalog()
    assert 'overspec-bootstrap' in {item.name for item in catalog}
    with skill_assets.materialize_skills(['overspec-bootstrap']) as sources:
        assert len(sources) == 1
        assert (sources[0].path / 'references/controls.md').is_file()
        assert sources[0].origin.startswith('package:overspec/')


def test_missing_payload_and_unknown_selection(monkeypatch, tmp_path):
    with pytest.raises(ValueError, match='Unknown'):
        with skill_assets.materialize_skills(['not-in-package']):
            pass
    monkeypatch.setattr(skill_assets, 'resource_tree', lambda *args: tmp_path)
    with pytest.raises(ValueError, match='Missing'):
        skill_assets.skill_catalog()
