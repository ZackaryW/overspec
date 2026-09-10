# Overspec controls

## Files and terms

| Item | Meaning |
| --- | --- |
| `~/.overspec` | User profiles, named selection, and profile activation state; `--home` or `OVERSPEC_HOME` can override it |
| `openspec/.over` | The owning project's trait sources and optional variables |
| `profile-default` | Default profile; the project's same-name directory replaces the user default |
| Loose `trait*.toml` | Local declarations outside profile trees, layered over the chosen profile |
| `.vars.toml` | Optional persistent variables, eligible for Git tracking |
| `.current.toml` | Mutable local variables, initialized when missing and ignored by basename |
| `.state.json` | One current compilation, synchronized resolution, and sync receipt |
| OpenSpec `changeRoot` | Exact selected change directory, possibly outside the implementation repository |

A trait has a short stable name and a compact, independently actionable `body`.
Optional `details` supplies literal elaboration on request, never automatically
inserted into config. An `attach` selects `context`, `rules.<artifact-id>`,
`operations.apply.guidance`, or `operations.archive.guidance`. The entire suffix
after `rules.` is one literal artifact ID. Choose context for cross-operation
guidance and an operation attachment for a specific workflow stage. Lifetimes are
`compiletime-trait` at init/update, ordinary `trait` at sync/static resolve, and
`runtime-trait` when its saved command is executed. Use create-overspec-trait for
authoring and schema validation.

The two variable files can live in `openspec/.over/` and directly in one
OpenSpec change root. There are no new user-home variable files. Neither file
declares traits. Example for either file:

```toml
[vars]
language = "Python"
strict = true
reviewers = ["maintainer", "peer"]
"build.target" = "desktop"
```

Only `[vars]` is allowed. Missing files, empty documents, and an empty vars table
contribute nothing. Values are strings, booleans, integers, finite floats, or
lists of these; dates, nested maps/lists, and unknown root fields are errors.
Keys are literal: `build.target` above is not a path. An override replaces the
whole value, including lists. Omission inherits; there is no deletion sentinel.
Explicit JSON still supports null.

## Precedence and lifetimes

Highest to lowest for init/update/sync and static resolve:

1. Explicit `--vars-file` JSON.
2. Project `.current.toml`.
3. Project `.vars.toml`.
4. Project `.over/config.toml` vars.
5. User `~/.overspec/config.toml` vars.

Change variables never affect shared static sync. `compiletime-trait` freezes at
init/update; changing a used effective input requires update. Unrelated variables
do not. Ordinary `trait` reads project variables on each sync/preview.

Highest to lowest for version-2 saved runtime commands:

1. Explicit `--context-file` JSON.
2. Selected change `.current.toml`.
3. Selected change `.vars.toml`.
4. Project `.current.toml`.
5. Project `.vars.toml`.
6. Retained configured defaults: user/project config plus sync's explicit JSON.

Runtime rereads file layers on each invocation. Removing a file removes that
layer; temporary values are not fallback defaults. Assertions and body rendering
use the same final mapping. No `--change-root` means project scope only, with no
automatic change selection. Missing/moved/redirected explicit roots fail.
Retained defaults and definitions do not follow live profile/config edits.

Only the current synchronized resolution is retained in `.over/.state.json`.
An explicit resolution ID guards that snapshot; superseded IDs fail. Legacy
multi-file state is not loaded. Run `overspec init --setup-only` for new ignore
coverage, then `overspec update`, preview, and sync to
regenerate; remove the obsolete generated `.over/.state/` only after verification.
Setup-only does not migrate compilation. If .state.json is corrupt, restore a
valid copy or move it aside before explicit update/sync regeneration.
`${key}` interpolates scalars only; `$$` is a literal dollar. Details stay literal
and can be read with `overspec trait show <name> --details`, optionally with
`--resolution <id>`, even when live variable files are malformed.

`runtime-context-match` performs exact typed equality: true differs from 1.
`runtime-context-includes` tests exact list membership; `$name` in its includes
operand reads another list for overlap. Equality does not dereference `$name`.
There are no regex, glob, generic expression, or static variable predicates.

## Choosing commands and handling diagnostics

| Situation | Action |
| --- | --- |
| First compilation | `overspec init --project <root>` |
| Current files missing after compilation | `overspec init --setup-only --project <root>` |
| New change in a selected store | Get OpenSpec status with `--store <id>`, then setup-only with its `--change-root` |
| All active changes in that store | `overspec init --setup-only --project <root> --store <id>` |
| Several exact changes | Repeat `--change-root` on init; do not also supply `--store` |
| Relevant compile-time source/input changed | `overspec update`, then preview/sync |
| Ordinary/runtime source changed | Preview/sync; runtime definitions are retained by resolution ID |
| Named profile management requested | `overspec profile activate` toggles mode; inspect profile help before selecting |

Setup-only does not compile, sync, pull profiles, or toggle activation. Normal
init refuses an existing compilation before setup writes. Existing current files
retain bytes and times. No setup path automatically creates `.vars.toml`.

Setup uses zuu's verified Git-ignore operations for `.current.toml` coverage in
each containing worktree. This basename pattern covers future nested changes.
Already effective coverage makes no edit. Tracked current files remain tracked
and are reported for deliberate cleanup; setup never stages removals. Existing
rules that ignore an authored `.vars.toml` are reported without being removed.
Non-Git roots can initialize files but report ignore coverage as unavailable.
Partial results name created/preserved/failed targets and are safe to retry;
discovery errors fail instead of being mistaken for no active changes.

## Archive decision examples

During implementation, commit all nonignored work except the active change's
resolved `changeRoot` directory. Its proposal, design, tasks, delta specs, and
reports wait for final handling. `.over`, `openspec/config.yaml`, tests, skills,
canonical specs, and previously archived records are included in incremental
commits. This is not an exclusion of the entire OpenSpec directory.

For the selected change, explain these effects and wait for the user's answer:

| Explicit answer | Intended result to review before final handling |
| --- | --- |
| Discard | Remove the change's planning record; do not silently discard implementation or merge its delta specs |
| Archive normally | Merge accepted delta specs and retain the change as an archive record through the OpenSpec workflow |
| Dissolve into zmem | Preserve verified durable decisions through zmem, then remove the superseded change record according to the confirmed scope |
| Only form specs | Merge accepted delta specs into canonical specs and remove the transient change record without retaining an archive copy |

If the reply is pending, take no archive/removal action. For example,
`archive = "discard"` in `.current.toml` is data, not consent. If dissolution
needs clarification about spec retention, resolve that concrete ambiguity before
removing records. Use the installed OpenSpec skills and zmem-author-commits for
their actual procedures; these outcomes are not invented Overspec subcommands.
Final commits include retained OpenSpec records and their authored persistent
vars. Never stage current files, including when an archive move carries them.
