# Overspec controls

## Files and terms

| Item | Meaning |
| --- | --- |
| `~/.overspec` | User settings: named selection, activation, Saucepan connection/order, and configured vars; `--home` or `OVERSPEC_HOME` can override it |
| `openspec/.over` | The owning project's trait sources and optional variables |
| `profile-default` | Packaged base; repository and workspace same-name traits override individual declarations |
| Loose `trait*.toml` | Declarations outside profile trees, layered after their own source's selected profile |
| `.vars.toml` | Optional persistent variables, eligible for Git tracking |
| `.current.toml` | Mutable local variables, initialized when missing and ignored by basename |
| `.state.json` | Current compilation, synchronized resolution, sync receipt, and optional schema baseline |
| OpenSpec `changeRoot` | Exact selected change directory, possibly outside the implementation repository |

A trait has a short stable name and a compact, independently actionable `body`.
Optional `details` supplies literal elaboration on request, never automatically
inserted into config. An `attach` selects `context`, `rules.<artifact-id>`,
`operations.apply.guidance`, or `operations.archive.guidance`. The entire suffix
after `rules.` is one literal artifact ID. Choose context for cross-operation
guidance and an operation attachment for a specific workflow stage. Lifetimes are
`compiletime-trait` at init/update, ordinary `trait` at sync/static resolve, and
`runtime-trait` when its live command is executed. Use overspec-create-trait for
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

Highest to lowest for runtime commands:

1. Explicit `--context-file` JSON.
2. Selected change `.current.toml`.
3. Selected change `.vars.toml`.
4. Project `.current.toml`.
5. Project `.vars.toml`.
6. Current project config vars, then current user config vars.

Runtime rereads file layers on each invocation. Removing a file removes that
layer; temporary values are not fallback defaults. Assertions and body rendering
use the same final mapping. No `--change-root` means project scope only, with no
automatic change selection. Missing/moved/redirected explicit roots fail.
Runtime definitions, profile selection, and configured defaults are read live.
Runtime commands have no resolution ID and never reuse sync's transient JSON.

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

## Shared Saucepan sources

The optional `[sources.saucepan]` table in the chosen user home's `config.toml`
connects independently of profile mode. It requires `marker`, a private registered
`overspec` JSON token file. Optional `binary` selects the executable; both paths
are home-relative or absolute. Optional `order` contains unique canonical source
IDs, low to high; unlisted eligible sources sort first by ID. Without the table,
no Saucepan dependency is required. A configured connection must succeed.

Inspect scope using Saucepan's public API. Whole-current-root artifacts must be
visible in the `overspec` view. Historical/folder-only/pinned-only content and
current snapshots touched only by another app are excluded with acquisition
guidance. Do not repair discovery by scanning internal storage or copying cache
directories. Acquisition is explicit work in Saucepan, outside init/sync/preview.

Each acquired repository independently selects `over-traits/` and `over-profiles/`
before their `openspec/.over/` fallbacks. Existing empty top-level directories
suppress fallback; invalid selected content fails. All contributors to the selected name are parsed; inactive profile bodies are not. Acquired variables and skills do not enter the consuming project.

Low-to-high source priority is packaged default, each acquired repository, then
workspace. Within each repository/workspace, selected-profile declarations precede
standalone declarations. A higher repository profile beats a lower repository's
standalone trait. Same-name profiles extend trait-by-trait, preserving other names;
matching names replace whole declarations. Duplicates inside one profile contributor
or standalone layer fail. Named profiles do not implicitly inherit packaged default.

The installed default needs no clone, acquisition, or profile copy. The authored
source is `openspec/.over/profile-default`; released wheels carry those documents.
Before init, `trait resolve --explain` reports unevaluated inventory without writes.
Init still creates normal state/current files. Missing packaged resources are errors.
Inspect `trait resolve --explain --json` for package/repository/workspace provenance
and `profile list --json` for ordered `contributors` while mode is on. Only activate
is available while off; enabled mode adds use/list. Direct user-home content and
legacy profile pull/update commands are removed with no compatibility aliases.
Existing files stay untouched; relocate/acquire sources deliberately. Top-level
update remains the compilation refresh command. Changed effective compiled inputs
or selected name require update; ordinary/runtime-only edits need sync. Saved
detail lookup does not load the package or call Saucepan; runtime commands do read
current effective sources.

## Choosing commands and handling diagnostics

| Situation | Action |
| --- | --- |
| First compilation | `overspec init --project <root>` |
| Current files missing after compilation | `overspec init --setup-only --project <root>` |
| New change in a selected store | Get OpenSpec status with `--store <id>`, then setup-only with its `--change-root` |
| All active changes in that store | `overspec init --setup-only --project <root> --store <id>` |
| Several exact changes | Repeat `--change-root` on init; do not also supply `--store` |
| Relevant compile-time source/input changed | `overspec update`, then preview/sync |
| Ordinary source changed | Preview/sync |
| Runtime body/condition changed | Next runtime invocation loads it; sync only to update emitted names/attachments |
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

## Compiled setting gates

`setting = "key"` on a compiletime-trait is checked only during sync/preview for
eligible guidance. Static variable precedence applies; missing enables, false
suppresses publication, and a nonboolean value fails. Use project .vars/.current
or configured defaults, not a selected change file. Toggle and sync without
updating compilation; assertions and compiled actions remain retained. Use
overspec-configure, overspec-sync, and overspec-diagnose for these tasks.

## Managed skills and project schema

`overspec skill list` reads packaged skills without native installation. For native
operations select --agent and --name/--all, or use ZuU checklists when omitted in a
terminal. JSON/noninteractive execution requires explicit selections. Cancellation
changes no native skills. Install adds missing skills and refreshes existing ones;
install/update automatically replace differing supported selected content, including
unowned/local edits, with recovery history. Current managed content is a no-op.
Install/update have no --force option; restore/remove retain it. Keep provider errors visible.
User-level skill setup works without a project or profile activation.

The selected Overspec home contains the ZuAT registry at `zuat` and its immutable
native-home binding at `zuat-home.json`. --agent-home chooses native agent files,
independently of --home. Use separate Overspec homes for different native homes.
History yields operation IDs for `overspec skill restore <id> --agent <agent>
--name <skill>`. Restore checks later edits and can restore historical skills no
longer packaged. Do not remove the registry/binding as a repair or mistake an ID
for a Git hash. Results are per target, not a cross-agent transaction. Missing
external skills such as zmem-author-commits remain external prerequisites.

Normal project init installs `openspec/schemas/overspec` and its templates before
change discovery. Update refreshes only unchanged managed files; the current
baseline stays in .state.json. Different unmanaged or locally edited schema
content causes a conflict. Reconcile/back up those files explicitly before retry;
there is no force-schema option. Identical preexisting packaged content can be
adopted without rewriting it. Preserve unrelated files and other schema names.
Setup-only/sync do not publish schema files, and config.yaml/active-change schema
selections are preserved. Select `schema: overspec` explicitly when requested.
Schema writes target the owning project even with --store: a separate planning
store needs its own schema availability. Skill restore does not restore schemas;
schema customizations are normal project files suitable for Git.
