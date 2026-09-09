from zipfile import ZipFile

import pytest
from conftest import declaration


@pytest.fixture(autouse=True)
def enabled_profile_mode(project):
    from overspec.core.profiles import toggle_profiles

    toggle_profiles(project.home)


class Client:
    def __init__(self, text):
        self.text = text
        self.commit = "a" * 40
        self.branches = []
        self.downloads = 0

    def resolve_commit(self, owner, repository, branch):
        self.branches.append(branch)
        return self.commit

    def download_archive(self, owner, repository, commit, destination):
        self.downloads += 1
        if self.text is None:
            raise OSError("download failed")
        with ZipFile(destination, "w") as archive:
            archive.writestr("repo-sha/default/traits.toml", self.text)


def test_remote_public_api_fetch_and_offline_selection(project):
    from overspec.core.profiles import select_profile, use_profile
    from overspec.core.remotes import pull_profile, remote_profiles

    client = Client(declaration("remote"))
    source = {
        "kind": "github",
        "owner": "owner",
        "repository": "repo",
        "path": "default",
        "branch": "main",
    }
    settings_before = (project.home / "config.toml").read_bytes()
    result = pull_profile(project.home, "default", source, client=client)
    assert result["commit"] == "a" * 40 and client.branches == ["main"]
    profiles = remote_profiles(project.home)
    assert "remote" in (profiles["default"] / "traits.toml").read_text()
    assert select_profile(project.root, project.home) == (
        "default",
        profiles["default"],
    )
    assert (project.home / "config.toml").read_bytes() == settings_before
    use_profile(project.root, project.home, "default")
    project.initialize()
    project.sync()
    assert client.downloads == 1


def test_remote_failures_and_cache_validation_preserve_revision(project):
    from overspec.core.remotes import pull_profile, remote_profiles, update_profile

    source = {
        "kind": "github",
        "owner": "owner",
        "repository": "repo",
        "path": "default",
    }
    client = Client(declaration("good"))
    first = pull_profile(project.home, "default", source, client=client)
    current = remote_profiles(project.home)["default"]
    download = project.home / ".state/remotes/default/download/traits.toml"
    download.write_text("invalid TOML")
    with pytest.raises(ValueError):
        update_profile(project.home, "default", client=client)
    assert remote_profiles(project.home)["default"] == current
    client.commit = "b" * 40
    client.text = None
    with pytest.raises(ValueError):
        update_profile(project.home, "default", client=client)
    assert (current / "traits.toml").read_text() == declaration("good")
    client.text = declaration("new")
    second = update_profile(project.home, "default", client=client)
    assert second["revision"] != first["revision"]
    assert remote_profiles(project.home)["default"] != current
    with pytest.raises(ValueError, match="source"):
        pull_profile(
            project.home, "default", {**source, "path": "different"}, client=client
        )


def test_cached_default_resolves_offline_while_mode_is_off(project):
    from overspec.core.profiles import toggle_profiles
    from overspec.core.remotes import pull_profile

    client = Client(declaration("cached"))
    pull_profile(
        project.home,
        "default",
        {"kind": "github", "owner": "owner", "repository": "repo", "path": "default"},
        client=client,
    )
    unrelated = project.home / ".state/remotes/unrelated"
    unrelated.mkdir()
    (unrelated / "current.json").write_text("invalid JSON")
    toggle_profiles(project.home)
    client.text = None
    project.initialize()
    assert "cached" in project.sync()["candidate"]
    assert client.downloads == 1


def test_remote_selectors_invalid_sources_and_collision(project):
    from overspec.core.remotes import pull_profile

    client = Client(declaration("a"))
    source = {
        "kind": "github",
        "owner": "owner",
        "repository": "repo",
        "path": "default",
        "commit": "b" * 40,
    }
    assert (
        pull_profile(project.home, "pinned", source, client=client)["commit"]
        == "b" * 40
    )
    assert not client.branches
    for invalid in (
        {**source, "kind": "gitlab"},
        {**source, "commit": "short"},
        {**source, "branch": "main"},
    ):
        with pytest.raises(ValueError):
            pull_profile(project.home, "bad", invalid, client=client)
    (project.home / "profile-local").mkdir()
    with pytest.raises(ValueError, match="collision"):
        pull_profile(project.home, "local", source, client=client)


def test_validate_exact_bytes_that_will_be_published(project, monkeypatch):
    import overspec.core.remotes as remotes

    client = Client(declaration("valid"))
    capture = remotes.material

    def changed_during_capture(root):
        if root.name == "download":
            (root / "traits.toml").write_text("invalid TOML")
        return capture(root)

    monkeypatch.setattr(remotes, "material", changed_during_capture)
    with pytest.raises(ValueError):
        remotes.pull_profile(
            project.home,
            "default",
            {
                "kind": "github",
                "owner": "owner",
                "repository": "repo",
                "path": "default",
            },
            client=client,
        )
    assert not (project.home / ".state/remotes/default/current.json").exists()


def test_interrupted_revision_copy_can_retry_without_losing_previous(
    project, monkeypatch
):
    import overspec.core.remotes as remotes
    from overspec.core import storage

    client = Client(declaration("old"))
    config = {
        "kind": "github",
        "owner": "owner",
        "repository": "repo",
        "path": "default",
    }
    remotes.pull_profile(project.home, "default", config, client=client)
    previous = remotes.remote_profiles(project.home)["default"]
    client.commit = "c" * 40
    client.text = declaration("new")
    write = storage.atomic_write

    def fail_trait(root, relative, content, **kwargs):
        if "/revisions/" in relative and relative.endswith("traits.toml"):
            raise OSError("interrupted copy")
        return write(root, relative, content, **kwargs)

    monkeypatch.setattr(storage, "atomic_write", fail_trait)
    with pytest.raises(OSError):
        remotes.update_profile(project.home, "default", client=client)
    assert remotes.remote_profiles(project.home)["default"] == previous
    monkeypatch.setattr(storage, "atomic_write", write)
    remotes.update_profile(project.home, "default", client=client)
    assert remotes.remote_profiles(project.home)["default"] != previous
