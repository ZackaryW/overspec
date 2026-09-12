## Why

Overspec can already bundle the skills in its authored catalog, but its three zmem skills currently have no automated upstream refresh. A repository-maintenance hook should acquire them from zmem and keep their complete support trees available for packaging without requiring source access on installed computers.

## What Changes

- Add an independent scripts/ maintenance project and Lefthook pre-commit job that acquire `https://github.com/ZackaryW/zmem.git` at `main`, selecting `skills`, through Saucepan's planned unscoped acquisition.
- Synchronize only `zmem-author-commits`, `zmem-query-memory`, and `zmem-design-extensions` into `.agents/skills`, including recursive support files and upstream removals.
- Track the acquired revision and payload hashes in a repository provenance record outside the skill payloads.
- Validate all three source trees before publishing changes, preserve unrelated skills, and avoid rewriting identical files.
- Leave changed files available for review and staging; the pre-commit job stops when refresh changes content and succeeds once a repeat refresh is unchanged.
- Preserve offline wheel/source-distribution builds and installed resource use.

## Capabilities

### New Capabilities

- `maintained-external-skills`: Refresh a fixed upstream skill set into the repository's packaged authored catalog.

### Modified Capabilities

None. The existing packaged-agent-skills resource and installation contracts continue to apply.

## Impact

New `scripts/sync_zmem_skills.py`, `scripts/pyproject.toml`, `scripts/uv.lock`, `scripts/tests/`, Lefthook configuration, three vendored skill trees, provenance, and maintainer documentation. The maintenance implementation imports no Overspec modules and does not require Overspec to be installed. No new trait assertions/actions, installed CLI commands, schema changes, or acquisition during build/install.

Implementation depends on Saucepan's `add-unscoped-acquisition` being implemented and available through a compatible SDK/executable. Do not substitute a scoped app or direct Git fallback. Pin maintenance dependencies in the independent scripts project after that upstream change is available; leave Overspec application dependencies and its root lockfile unchanged.
