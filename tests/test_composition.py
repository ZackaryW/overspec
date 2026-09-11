from pathlib import Path
import pytest


def test_parse_all_types_and_optional_details():
    from overspec.core.trait_system.sources import parse_document

    root = Path(__file__).resolve().parents[1] / "openspec/.over/profile-default"
    traits = [
        t
        for p in sorted(root.glob("trait*.toml"))
        for t in parse_document(p.read_text(encoding="utf-8"), str(p))
    ]
    names = [t.name for t in traits]
    assert len(names) == len(set(names))
    assert {"tdd", "zuu", "utility-plan", "utility-mature", "bdd-behave"} <= set(names)
    assert {t.phase for t in traits} == {"compiletime-trait", "trait", "runtime-trait"}
    tdd = next(t for t in traits if t.name == "tdd")
    assert tdd.phase == "compiletime-trait" and tdd.setting == "tdd"
    assert not tdd.predicates and "observe the failure" in tdd.details
    parsed = parse_document(
        '[[trait]]\nname="x"\nattach="rules.review.notes"\nbody="brief"\ndetails="  "',
        "sample",
    )
    assert parsed[0].attach == "rules.review.notes" and parsed[0].details is None


@pytest.mark.parametrize(
    "extra",
    [
        "details=[]",
        "surprise=true",
        'assert_or_grouping="yes"',
        'assert=[{type="unknown"}]',
        'actions=[{type="remove-trait"}]',
    ],
)
def test_invalid_declarations_report_origin(extra):
    from overspec.core.trait_system.sources import parse_document

    with pytest.raises(ValueError, match="source.toml"):
        parse_document(
            '[[trait]]\nname="x"\nattach="context"\nbody="hi"\n' + extra, "source.toml"
        )


def test_full_local_override_preserves_order_and_removes_details():
    from overspec.core.trait_system.sources import parse_document, compose

    profile = parse_document(
        '[[trait]]\nname="a"\nattach="context"\nbody="old"\ndetails="old details"\n[[trait]]\nname="b"\nattach="context"\nbody="b"',
        "profile",
    )
    local = parse_document(
        '[[runtime-trait]]\nname="a"\nattach="context"\nbody="new"\n[[trait]]\nname="c"\nattach="context"\nbody="c"',
        "local",
    )
    effective, overridden = compose(profile, local)
    assert [t.name for t in effective] == ["b", "c", "a"]
    assert effective[-1].details is None and effective[-1].origin == "local"
    assert [t.name for t in overridden] == ["a"]
    with pytest.raises(ValueError, match="profile.*local"):
        compose([], profile + local)


def test_reject_invalid_names_attachments_and_blank_body():
    from overspec.core.trait_system.sources import parse_document

    for name, attach, body in [
        ("BAD", "context", "hi"),
        ("x", "rules.", "hi"),
        ("x", "operations.other.guidance", "hi"),
        ("x", "context", " "),
    ]:
        with pytest.raises(ValueError):
            parse_document(
                f'[[trait]]\nname="{name}"\nattach="{attach}"\nbody="{body}"', "test"
            )
