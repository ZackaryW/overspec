import shutil
from pathlib import Path

from overspec.core.projection import parse_yaml


def test_zmem_skill_reference_tracks_availability_without_codegraph(
    project, monkeypatch
):
    repository = Path(__file__).resolve().parents[1]
    shutil.copytree(
        repository / "openspec/.over/profile-default", project.over / "profile-default"
    )
    monkeypatch.setattr(
        shutil, "which", lambda name: "/tools/zmem" if name == "zmem" else None
    )
    project.initialize()
    project.sync()
    config = project.root / "openspec/config.yaml"
    synced = parse_yaml(config.read_text())
    assert "zmem-author-commits" in synced["context"]
    archive = "\n".join(synced["operations"]["archive"]["guidance"])
    assert "zmem-author-commits" in archive
    assert "Ask the user" in archive
    assert (
        "discard, archive normally, dissolve into zmem, or only form specs" in archive
    )
    choice = next(
        item
        for item in synced["operations"]["archive"]["guidance"]
        if "Ask the user" in item
    )
    assert "archiving" not in synced["context"]
    monkeypatch.setattr(shutil, "which", lambda name: None)
    project.sync()
    synced = parse_yaml(config.read_text())
    assert "zmem-author-commits" not in synced["context"]
    # The lifecycle choice remains required even without the optional zmem tool.
    assert choice in synced["operations"]["archive"]["guidance"]
