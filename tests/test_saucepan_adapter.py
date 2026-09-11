import copy
import hashlib
import sys

import pytest


class Client:
    def __init__(self):
        self.document = {
            "version": 1,
            "app": "overspec",
            "settings": {},
            "filters": {},
            "entries": {},
        }
        self.states = {}
        self.paths = {}
        self.calls = []

    def view(self):
        self.calls.append("view")
        return copy.deepcopy(self.document)

    def verify(self, view):
        self.calls.append("verify")
        return {"verified": view == self.document}

    def history(self, source):
        self.calls.append("history")
        return copy.deepcopy(self.states.get(source))

    def path(self, artifact):
        self.calls.append("path")
        return self.paths.get(artifact)

    def add(self, root, source="a" * 64, snapshot="1" * 64, folder=None):
        files = {}
        for path in sorted(root.rglob("*")):
            files[path.relative_to(root).as_posix()] = {
                "digest": hashlib.sha256(path.read_bytes()).hexdigest()
                if path.is_file()
                else None,
                "executable": False,
            }
        artifact = {
            "id": source + snapshot,
            "source_id": source,
            "snapshot_id": snapshot,
            "source": {"provider": "local", "path": str(root)},
            "revision": snapshot,
            "folder": folder,
            "content_id": "c" * 64,
            "files": files,
        }
        self.document["entries"][artifact["id"]] = artifact
        self.states[source] = {
            "source": artifact["source"],
            "current": {
                "id": snapshot,
                "revision": snapshot,
                "files": files,
                "content_id": "c" * 64,
            },
            "history": [],
            "sequence": 1,
        }
        self.paths[artifact["id"]] = str(root)
        return artifact


def test_optional_sdk_failure_is_actionable(tmp_path, monkeypatch):
    from overspec.core.external.adapter import create_client
    from overspec.core.external.settings import Connection

    monkeypatch.setitem(sys.modules, "saucepan_sdk", None)
    with pytest.raises(ValueError, match="extra|install"):
        create_client(Connection(tmp_path / "marker", None, ()))


def test_only_current_visible_whole_roots(tmp_path):
    from overspec.core.external.adapter import repositories

    client = Client()
    root = tmp_path / "repo"
    root.mkdir()
    client.add(root, snapshot="0" * 64)
    current = client.add(root)
    roots, excluded, evidence = repositories(client)
    assert len(roots) == 1 and roots[0].artifact == current
    assert not excluded and evidence
    client.states[current["source_id"]]["current"]["id"] = "2" * 64
    assert repositories(client)[0] == []
    assert "whole current root" in repositories(client)[1][0]["reason"]
    client.add(root, folder="subset")
    assert repositories(client)[0] == []
    assert set(client.calls) <= {"view", "verify", "history", "path"}


@pytest.mark.parametrize(
    "corruption",
    ["app", "version", "entries", "proof", "missing-path", "manifest", "history"],
)
def test_invalid_connected_inventory_fails(tmp_path, corruption):
    from overspec.core.external.adapter import repositories

    client = Client()
    (tmp_path / "trait.toml").write_text("test")
    artifact = client.add(tmp_path)
    if corruption == "app":
        client.document["app"] = "foreign"
    elif corruption == "version":
        client.document["version"] = 2
    elif corruption == "entries":
        client.document["entries"] = []
    elif corruption == "proof":
        client.verify = lambda _: {"verified": False}
    elif corruption == "missing-path":
        client.paths.clear()
    elif corruption == "manifest":
        (tmp_path / "trait.toml").write_text("tampered")
    elif corruption == "history":
        client.states[artifact["source_id"]] = None
    with pytest.raises(ValueError, match="Saucepan"):
        repositories(client)


def test_backend_errors_do_not_echo_credentials():
    from overspec.core.external.adapter import repositories

    client = Client()

    def fail():
        raise RuntimeError("very-private-token")

    client.view = fail
    with pytest.raises(ValueError) as error:
        repositories(client)
    assert "very-private-token" not in str(error.value)


def test_authenticated_empty_scope():
    from overspec.core.external.adapter import repositories

    roots, excluded, evidence = repositories(Client())
    assert roots == excluded == [] and evidence


def test_real_sdk_missing_executable(tmp_path):
    pytest.importorskip("saucepan_sdk")
    from overspec.core.external.adapter import create_client, repositories
    from overspec.core.external.settings import Connection

    client = create_client(Connection(tmp_path / "marker", tmp_path / "missing.exe", ()))
    with pytest.raises(ValueError, match="executable"):
        repositories(client)
