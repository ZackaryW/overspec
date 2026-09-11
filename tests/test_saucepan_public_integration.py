"""Opt-in real executable checks; every operation uses an isolated test store."""

import json
import os
import tempfile
from pathlib import Path

import pytest
from conftest import declaration
from test_profiles import write
from test_saucepan_settings import configure


@pytest.fixture
def central_root():
    # Saucepan's own SDK fixtures use a short temporary store root on Windows.
    with tempfile.TemporaryDirectory(prefix="osp-") as directory:
        yield Path(directory) / "store"


def test_public_sdk_scoped_discovery(project, tmp_path, monkeypatch, central_root):
    sdk = pytest.importorskip("saucepan_sdk")
    binary = os.environ.get("OVERSPEC_TEST_SAUCEPAN_BINARY")
    if not binary:
        pytest.skip("Set OVERSPEC_TEST_SAUCEPAN_BINARY for isolated public integration")
    assert Path(binary).is_file()
    options = {"binary": binary, "test_root": central_root, "test_key": "17" * 32}
    admin = sdk.Saucepan(**options)
    admin.init()
    token = admin.register("overspec")
    other_token = admin.register("other")
    configure(project.home, {"marker": "marker"})
    marker = project.home / "marker"
    marker.write_text(json.dumps(token))
    client = sdk.Saucepan(**options, app="overspec", marker=marker)
    other = sdk.Saucepan(**options, token=other_token)
    monkeypatch.setattr(
        "overspec.core.external.adapter.create_client",
        lambda config: sdk.Saucepan(**options, app="overspec", marker=config.marker),
    )
    roots = [tmp_path / name for name in ("top", "fallback", "foreign")]
    write(roots[0], "over-profiles/profile-default/trait.toml", declaration("default"))
    write(roots[0], "over-traits/trait.toml", declaration("top"))
    write(roots[0], "openspec/.over/trait.toml", "invalid ignored TOML")
    write(roots[1], "openspec/.over/trait.toml", declaration("fallback"))
    write(roots[2], "over-traits/trait.toml", declaration("foreign"))
    acquired = []
    for root in roots[:2]:
        acquired.append(
            client.acquire({"source": {"provider": "local", "path": str(root)}})
        )
    other.acquire({"source": {"provider": "local", "path": str(roots[2])}})
    before = client.view()
    assert client.verify(before) == {"verified": True}
    assert client.path(acquired[0]["artifact"]["id"]) == acquired[0]["directory"]
    project.initialize()
    synced = project.sync()
    assert synced["changed"]
    assert set(project.prepare()["static"]["bodies"]) == {"default", "top", "fallback"}
    assert client.view() == before
    assert not project.sync()["changed"]
    assert not (project.home / "profile-default").exists()
    # Other-app refresh must not introduce an unseen current snapshot.
    write(roots[1], "openspec/.over/trait.toml", declaration("foreign-refresh"))
    other.acquire({"source": {"provider": "local", "path": str(roots[1])}})
    assert set(project.prepare()["static"]["bodies"]) == {"default", "top"}
    client.acquire({"source": {"provider": "local", "path": str(roots[1])}})
    assert "foreign-refresh" in project.prepare()["static"]["bodies"]
    client.configure(
        filters={"source_ids": [acquired[0]["artifact"]["source_id"]], "providers": []}
    )
    assert set(project.prepare()["static"]["bodies"]) == {"default", "top"}
