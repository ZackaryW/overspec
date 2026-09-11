import sys

import pytest
import tomlkit

from overspec.core.profiles import settings, toggle_profiles


def configure(home, value):
    home.mkdir(parents=True, exist_ok=True)
    (home / "config.toml").write_text(tomlkit.dumps({"sources": {"saucepan": value}}))


def test_disconnected_settings_do_not_import_sdk(tmp_path, monkeypatch):
    from overspec.core.external.settings import connection

    monkeypatch.setitem(sys.modules, "saucepan_sdk", None)
    assert connection(tmp_path) is None


def test_connection_is_home_relative_and_independent_of_profile_mode(tmp_path):
    from overspec.core.external.settings import connection

    configure(
        tmp_path,
        {
            "marker": ".saucepanhash",
            "binary": "bin/saucepan",
            "order": ["b" * 64, "a" * 64],
        },
    )
    (tmp_path / ".saucepanhash").write_text("private token")
    original = settings(tmp_path)["sources"]
    before = connection(tmp_path)
    assert before.marker == tmp_path / ".saucepanhash"
    assert before.binary == tmp_path / "bin/saucepan"
    assert before.order == ("b" * 64, "a" * 64)
    toggle_profiles(tmp_path)
    assert connection(tmp_path) == before
    toggle_profiles(tmp_path)
    assert settings(tmp_path)["sources"] == original


@pytest.mark.parametrize(
    "value",
    [
        True,
        {},
        {"marker": ""},
        {"marker": 1},
        {"marker": "x", "extra": True},
        {"marker": "x", "order": "x"},
        {"marker": "x", "order": ["bad"]},
        {"marker": "x", "order": ["a" * 64] * 2},
        {"marker": "x", "binary": False},
    ],
)
def test_invalid_connection_is_an_error(tmp_path, value):
    from overspec.core.external.settings import connection

    configure(tmp_path, value)
    (tmp_path / "x").write_text("secret")
    with pytest.raises(ValueError, match="saucepan"):
        connection(tmp_path)


def test_missing_marker_is_not_an_empty_inventory(tmp_path):
    from overspec.core.external.settings import connection

    configure(tmp_path, {"marker": "missing"})
    with pytest.raises(ValueError):
        connection(tmp_path)
