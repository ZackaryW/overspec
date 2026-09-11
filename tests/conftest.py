import pytest


def declaration(name, phase="trait", body=None, attach="context", **extra):
    fields = {"name": name, "attach": attach, "body": body or name, **extra}
    import tomlkit

    return tomlkit.dumps({phase: [fields]})


@pytest.fixture
def project(tmp_path, monkeypatch):
    # Narrow lifecycle/unit fixtures use an explicitly empty package source.
    # Installed-package and bundled-profile tests exercise the real default.
    from overspec.core import bundled
    from overspec.core.project import Project

    class EmptyPackage:
        def contributor(self):
            return {"kind": "package", "package": "overspec", "version": "test",
                    "origin": "package:overspec/profile-default", "path": "package:overspec/profile-default"}

        def documents(self, reader):
            return []

    monkeypatch.setattr(bundled, "default_profile", EmptyPackage)

    root = tmp_path / "project"
    (root / "openspec/.over").mkdir(parents=True)
    (root / "openspec/config.yaml").write_text("schema: spec-driven\n")
    return Project(root, tmp_path / "home")


def source(project, text, file="traits.toml"):
    path = project.root / "openspec/.over" / file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def external(project, tmp_path, monkeypatch):
    from test_saucepan_adapter import Client
    from test_saucepan_settings import configure

    client = Client()
    configure(project.home, {"marker": "marker"})
    (project.home / "marker").write_text("secret-marker")
    monkeypatch.setattr(
        "overspec.core.external.adapter.create_client", lambda _: client
    )
    return client, tmp_path / "external"
