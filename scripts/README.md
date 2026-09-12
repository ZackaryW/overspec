# Repository maintenance

This directory is its own uv project. It does not install or import Overspec,
read project configuration, or use the root lockfile. `sync_zmem_skills.py` acquires
the three zmem skills from `main` through Saucepan and refreshes their full trees
under `.agents/skills`. `.agents/zmem-skills.json` records the immutable revision
and SHA-256 of every copied file.

## Setup

Install uv and Lefthook. Use a Saucepan executable containing unscoped acquisition
(implementation commit `2f62983e7af9c6b65906f14cf68bfd73453f8b26` or a descendant).
Version 0.5.0 alone does not distinguish old and new executables. The pinned Python
SDK already forwards omitted identity; it does not download or update the binary.

For a Saucepan development checkout containing that commit:

```powershell
cargo build --locked --manifest-path ../saucepan/Cargo.toml --bin saucepan
$env:SAUCEPAN_BINARY = (Resolve-Path ../saucepan/target/debug/saucepan.exe).Path
& $env:SAUCEPAN_BINARY init # Once only, when the user store does not yet exist
uv sync --project scripts --locked
lefthook install
```

On macOS/Linux select `target/debug/saucepan` with `export SAUCEPAN_BINARY=...`.
An installed executable defaults to `~/.saucepan/bin/saucepan[.exe]` when neither
`--binary` nor `SAUCEPAN_BINARY` is set. Initialize its encrypted user store once;
an unavailable native credential service is an error. The script never initializes
a store, registers an app, creates a marker, or falls back to direct Git.

Run a manual refresh from the repository root:

```sh
uv run --project scripts scripts/sync_zmem_skills.py
```

Use `--binary /path/to/saucepan` to select the executable for a single run, or
`--root /path/to/destination` to select the owning repository. These are filesystem
inputs and do not activate profiles or read Overspec settings.

## Review and recovery

The same command runs before commits through Lefthook:

- Exit **0**: bytes and provenance are unchanged; permit the commit.
- Exit **2**: refreshed content or provenance; review and stage the reported paths,
  then retry. The hook never stages files or creates commits.
- Exit **1**: acquisition, validation, or publication failed. Resolve the reported
  prerequisite or error; stale cached content is never reported as a fresh update.

Only `zmem-author-commits`, `zmem-query-memory`, and `zmem-design-extensions` are owned.
Obsolete files within those trees are removed; unrelated skills remain untouched.
All input trees and destinations are validated before replacement. Replacements
are staged, with originals retained until all trees and provenance are published.
On a publication failure the script attempts restoration and reports the retained
`.agents/.zmem-sync-*` recovery directory. Inspect that path before removing it;
an incomplete restoration identifies affected destinations and keeps their backups.
This is recoverable sequential replacement, not a cross-directory transaction.

The hook checks `main` each time, so it needs upstream access. Builds and installed
catalog operations use the committed snapshot and never run this script. Commit
the three skill trees and provenance together after review.

## Verification

```powershell
$env:SAUCEPAN_TEST_BINARY = $env:SAUCEPAN_BINARY
uv run --project scripts pytest -c scripts/pyproject.toml scripts/tests
lefthook run pre-commit --no-auto-install --no-tty
```

The focused tests use real local Git repositories and isolated encrypted Saucepan
stores; they do not use the user keyring. Failure injection is limited to filesystem
replacement to exercise recovery. Existing root distribution tests verify offline
bundling and installed resource use separately.
