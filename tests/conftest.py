import pytest


def declaration(name, phase="trait", body=None, attach="context", **extra):
    fields = {"name": name, "attach": attach, "body": body or name, **extra}
    import tomlkit

    return tomlkit.dumps({phase: [fields]})


@pytest.fixture
def project(tmp_path):
    from overspec.core.project import Project

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
