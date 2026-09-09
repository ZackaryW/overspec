import pytest


def test_variable_documents_are_optional_typed_and_readonly(tmp_path):
    from overspec.core.variables import load_variables

    assert load_variables(tmp_path, ".vars.toml") == {}
    assert list(tmp_path.iterdir()) == []
    path = tmp_path / ".vars.toml"
    for text, expected in [
        ("", {}),
        ("[vars]\n", {}),
        (
            '[vars]\nflag=true\ncount=2\nratio=1.5\n"a.b"="literal"\nitems=["x", 2, false]',
            {
                "flag": True,
                "count": 2,
                "ratio": 1.5,
                "a.b": "literal",
                "items": ["x", 2, False],
            },
        ),
    ]:
        path.write_text(text)
        before = path.stat().st_mtime_ns
        assert load_variables(tmp_path, ".vars.toml") == expected
        assert path.read_text() == text and path.stat().st_mtime_ns == before


@pytest.mark.parametrize(
    "text,key",
    [
        ("[vars", "TOML"),
        ("other=1", "other"),
        ("vars=[]", "vars"),
        ("[vars]\nx=1979-05-27", "x"),
        ("[vars]\nx=inf", "x"),
        ("[vars]\nx=[[1]]", "x"),
        ("[vars.x]\ny=1", "x"),
    ],
)
def test_variable_document_errors_identify_source_and_key(tmp_path, text, key):
    from overspec.core.variables import load_variables

    (tmp_path / ".current.toml").write_text(text)
    with pytest.raises(ValueError, match=key) as error:
        load_variables(tmp_path, ".current.toml")
    assert ".current.toml" in str(error.value)


def test_variable_layers_replace_lists_and_keep_json_null():
    from overspec.core.trait_system.rendering import variables, render

    values = variables({"x": ["a", "b"], "flag": True}, {"x": ["c"]}, {"flag": None})
    assert values == {"x": ["c"], "flag": None}
    assert render("${flag}", values) == "null"
    with pytest.raises(ValueError, match="scalar"):
        render("${x}", values)
    with pytest.raises(ValueError, match="x"):
        variables({"x": {"nested": 1}})


def test_static_files_precedence_and_compilation(project):
    from conftest import declaration, source

    source(project, '[vars]\nx="configured"', "config.toml")
    source(project, '[vars]\nx="persistent"', ".vars.toml")
    current = source(project, '[vars]\nx="current"', ".current.toml")
    source(
        project,
        declaration("c", "compiletime-trait", body="${x}")
        + declaration("s", body="${x}"),
    )
    source(project, '[vars]\nx="change"', "../changes/one/.vars.toml")
    project.initialize(values={"x": "frozen"})
    assert project.prepare()["static"]["bodies"] == {"c": "frozen", "s": "current"}
    assert (
        project.prepare(values={"x": "explicit"})["static"]["bodies"]["s"] == "explicit"
    )
    current.write_text('[vars]\nx="current"\nunrelated=1')
    project.prepare()
    current.write_text('[vars]\nx="new"')
    with pytest.raises(ValueError, match="update"):
        project.prepare()
    project.initialize(update=True)
    assert project.prepare()["static"]["bodies"] == {"c": "new", "s": "new"}


@pytest.mark.parametrize("operation", ["compile", "sync"])
@pytest.mark.parametrize("mutation", ["add", "remove", "change"])
def test_variable_publication_race_preserves_pointers(
    project, monkeypatch, operation, mutation
):
    from overspec.core import storage

    path = project.over / ".current.toml"
    if mutation != "add":
        path.write_text("[vars]\nx=1")
    project.initialize()
    pointer = project.state / "compiled.json"
    config = project.root / "openspec/config.yaml"
    before = pointer.read_bytes(), config.read_bytes()
    publish = storage.publish

    def intervene(*args):
        identity = publish(*args)
        if mutation == "remove":
            path.unlink()
        else:
            path.write_text("[vars]\nx=2")
        return identity

    monkeypatch.setattr(storage, "publish", intervene)
    with pytest.raises(ValueError, match="changed"):
        project.initialize(update=True) if operation == "compile" else project.sync()
    assert (pointer.read_bytes(), config.read_bytes()) == before
