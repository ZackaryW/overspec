# Implementation evidence

## Upstream prerequisite

Saucepan implementation commit: `2f62983e7af9c6b65906f14cf68bfd73453f8b26`.
The local executable was built at `../saucepan/target/debug/saucepan.exe` and tested
against isolated stores and the initialized user store. Scripts pin the existing
SDK at `43ba58936c48c3daf00e0e1cd25b870d4869731a`: its no-context acquire call already
forwards the new CLI behavior without SDK changes. This SDK pin does not imply
that an old executable at that revision supports unscoped acquisition.

`uv sync --project scripts` installs Saucepan SDK, ZuU, and test dependencies only.
The integration test asserts Overspec is unavailable in this environment. Root
`pyproject.toml` and `uv.lock` are unchanged.

## RED and GREEN

`uv run --project scripts pytest -c scripts/pyproject.toml scripts/tests -q --tb=short`
with `SAUCEPAN_TEST_BINARY` selecting the built executable:

1. RED: three failures against the command scaffold, which returned unchanged
   without synchronization or prerequisite diagnostics.
2. GREEN: three passing tests after acquisition, validated staging, publication,
   no-op comparison, and diagnostics were implemented. A checkout CRLF mismatch
   in the fixture expectation was corrected to compare committed Git bytes.
3. Recovery RED: two observed failures after injection of a mid-publication error,
   including a second injected restore error. Original destinations were not restored.
4. Recovery GREEN: five tests passed after restoration and retained-backup diagnostics.

Tests use real local Git sources and a real Saucepan CLI/store. Only filesystem
replacement failures are injected. Coverage includes recursive support files,
upstream removals, provenance hashes/revision, unchanged mtimes, unrelated skill
preservation, incomplete source rejection, independent execution, and recovery.

## Live hook and source refresh

`lefthook run pre-commit --no-auto-install --no-tty --force` using the built binary:

- First run: script exit 2, Lefthook exit 1; refreshed three skill trees plus
  `.agents/zmem-skills.json` at zmem `59aa3d5b420fc241b5b7b4f42931fb1095a4f17d`.
- Second run: exit 0, unchanged.
- Missing executable: script and hook exit 1 with explicit prerequisite diagnostic.
- Git index inventory before/after the refresh was identical: no auto-staging.

The nine acquired files include all three SKILL.md documents, their referenced
documentation, and `agents/openai.yaml` metadata. Provenance contains no machine
cache paths or timestamps. The user store was absent and initialized explicitly
for this live check; the script itself never initializes or registers anything.
Hook installation remains an explicit maintainer setup command in scripts/README.md.

## Distribution

With `UV_OFFLINE=true`, HTTP/HTTPS proxies pointing to an unavailable local port,
and `SAUCEPAN_BINARY` pointing to a missing executable:

```
uv run --no-sync pytest tests/test_distribution.py::test_release_and_sdist_wheels_contain_only_authored_traits tests/test_installed_package.py::test_installed_resources_are_unchanged tests/test_installed_package.py::test_installed_skill_lifecycle_and_schema_instructions -q --tb=short
```

Result: **3 passed**. Existing checks compare complete asset bytes between direct
and source-distribution wheels, and exercise installed resources outside the source
checkout. No package build or runtime code changed.
