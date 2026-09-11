import pytest
from conftest import declaration
from test_profiles import write
from test_saucepan_adapter import Client
from test_saucepan_settings import configure


def discover(home, client):
    from overspec.core.external.discovery import discover as load

    configure(home, {"marker": "marker"})
    (home / "marker").write_text("private")
    return load(home, client_factory=lambda _: client)


def test_categories_fall_back_independently(tmp_path):
    root = tmp_path / "repo"
    write(root, "over-traits/team/trait-x.toml", declaration("top"))
    write(root, "openspec/.over/trait-ignore.toml", "not valid toml!")
    write(root, "openspec/.over/profile-default/trait.toml", declaration("default"))
    write(root, "openspec/.over/profile-inactive/trait.toml", "not valid toml!")
    client = Client()
    client.add(root)
    catalog = discover(tmp_path / "home", client)
    assert [[p.name for p in layer] for layer in catalog.layers] == [["trait-x.toml"]]
    assert catalog.profiles["default"] == [root / "openspec/.over/profile-default"]
    assert "inactive" in catalog.profiles
    (root / "over-profiles").mkdir()
    client.add(root)
    assert discover(tmp_path / "home", client).profiles == {}


def test_empty_top_level_traits_ignore_fallback(tmp_path):
    root = tmp_path / "repo"
    write(root, "openspec/.over/trait.toml", declaration("fallback"))
    (root / "over-traits").mkdir()
    client = Client()
    client.add(root)
    assert discover(tmp_path / "home", client).layers == [[]]


def test_fallback_excludes_profiles_state_and_git(tmp_path):
    root = tmp_path / "repo"
    for name in (
        "trait.toml",
        "team/traits.toml",
        "profile-inactive/trait.toml",
        ".state/trait.toml",
        ".git/trait.toml",
    ):
        write(root, "openspec/.over/" + name, declaration("x"))
    client = Client()
    client.add(root)
    catalog = discover(tmp_path / "home", client)
    assert len(catalog.layers[0]) == 2


def test_invalid_selected_layout_does_not_fall_back(tmp_path):
    root = tmp_path / "repo"
    write(root, "over-traits", "file")
    write(root, "openspec/.over/trait.toml", declaration("fallback"))
    client = Client()
    client.add(root)
    with pytest.raises(ValueError):
        discover(tmp_path / "home", client)


def test_priority_retains_profile_contributors_and_reports_inactive_ids(tmp_path):
    from overspec.core.external.discovery import discover as load

    client = Client()
    for label in ("b", "a"):
        root = tmp_path / label
        write(root, "over-profiles/profile-default/trait.toml", declaration(label))
        write(root, "over-traits/trait.toml", declaration(label))
        client.add(root, label * 64)
    home = tmp_path / "home"
    assert (
        discover(home, client).profiles["default"]
        == [tmp_path / "a/over-profiles/profile-default", tmp_path / "b/over-profiles/profile-default"]
    )
    configure(home, {"marker": "marker", "order": ["b" * 64, "a" * 64, "c" * 64]})
    catalog = load(home, client_factory=lambda _: client)
    assert catalog.profiles["default"] == [tmp_path / "b/over-profiles/profile-default", tmp_path / "a/over-profiles/profile-default"]
    assert [x[0].parts[-3] for x in catalog.layers] == ["b", "a"]
    assert catalog.excluded[-1]["source_id"] == "c" * 64
    assert len(catalog.profile_origins["default"]) == 2
    client.document["entries"] = dict(
        reversed(list(client.document["entries"].items()))
    )
    assert load(home, client_factory=lambda _: client).evidence == catalog.evidence


def test_multiple_layers_replace_whole_traits_but_not_within_layer():
    from overspec.core.trait_system.sources import compose, parse_document

    def layer(text, origin):
        return parse_document(text, origin)

    first = layer(declaration("same", details="old") + declaration("other"), "profile")
    second = layer(
        declaration("same", phase="runtime-trait", attach="operations.apply.guidance"),
        "remote",
    )
    third = layer(declaration("same", body="local"), "local")
    effective, overridden = compose(first, second, [], third)
    same = next(t for t in effective if t.name == "same")
    assert same.body == "local" and same.details is None and same.phase == "trait"
    assert [t.origin for t in overridden] == ["profile", "remote"]
    assert [t.name for t in effective] == ["same", "other"]
    with pytest.raises(ValueError, match="Duplicate same"):
        compose(first, second + second, third)
