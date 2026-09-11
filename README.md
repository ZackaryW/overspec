# overspec

Overspec composes reusable traits into an existing OpenSpec project's native
`context`, `rules`, and apply/archive `guidance`. OpenSpec remains responsible for
schemas, artifacts, and change lifecycle. Runtime guidance is advisory: OpenSpec
shows a command to the agent; it does not execute that command automatically.

Requires Python 3.12+ and the companion OpenSpec CLI supporting
`operations.apply.guidance` and `operations.archive.guidance` (tested with 1.12.0).

```sh
uv sync
uv run overspec --help
```

The CLI uses Typer and Rich. Run `overspec` without arguments for a command
overview, or use `-h`/`--help` at any command level. Help groups project, input,
output, and runtime options; profile listings and resolution explanations use
tables. Sync previews separate the status summary, candidate YAML, and diff.
Terminal previews highlight and wrap long lines; redirected previews retain full
plain text. `--json` produces undecorated structured output, and resolved guidance
keeps its literal text and markers. Common `--home`, `--project`, and `--json`
options work before or after subcommands. Typer also exposes shell completion
through `--show-completion` and `--install-completion`.

## Start with an existing OpenSpec project

The installed package serves `profile-default` directly from its bundled resources.
No second clone, Saucepan connection, or local profile directory is needed. Profile
mode is off by default; ordinary setup needs no activation. The single authored
source remains this repository's `openspec/.over/profile-default`.

```sh
overspec init --project /path/to/project
overspec sync --project /path/to/project --dry-run
overspec sync --project /path/to/project
```

Run commands through `uv run overspec` when using this checkout rather than an
installed console command. Before init, `overspec trait resolve --explain` lists
discovered traits as unevaluated without writing state. Initialization creates
normal `.over` state/current files, but does not copy the packaged profile there.

To install a built release wheel into a user tool environment:

```sh
uv tool install /path/to/overspec-0.1.0-py3-none-any.whl
```

The wheel declares pinned Git dependencies for zuat and zuu; installation needs
those dependencies available. Subsequent default loading does not use the network.

Use the repository's `overspec-bootstrap` skill for first-time orientation or
setup after creating another change. Normal init discovers active changes through
OpenSpec and initializes missing `.current.toml` files. With an existing
compilation, setup can be repeated independently:

```sh
overspec init --setup-only --project /path/to/project
overspec init --setup-only --project /path/to/project --store team
overspec init --setup-only --project /path/to/project --change-root /resolved/change/one --change-root /resolved/change/two
```

Obtain exact roots from `openspec status --change <name> --json`, preserving
`--store <id>` when selected. `--store` on init only scopes discovery; it is
mutually exclusive with explicit roots. Setup-only preserves compilation, config,
profile mode, and existing current-file contents. It never fetches profiles.

Sync deliberately replaces all existing context and rules, plus apply/archive
guidance. Put any manual guidance you want to retain in traits before syncing.
Other configuration values, including unknown keys and operation siblings, survive.
Preview prints the target, candidate YAML, diff, resolution ID, and whether config
would change. Add `--json` for structured output.

## Shared sources through Saucepan

Install the optional SDK with `uv sync --extra saucepan` in this checkout and
install the Saucepan 0.5 executable separately. The SDK is locked to the inspected
current-API revision. Overspec does not install or initialize Saucepan.
Register the `overspec` app in Saucepan, acquire whole repositories under that
app, and save its returned JSON token in a private marker file. Then add this
table to the chosen user home's `config.toml` (normally `~/.overspec/config.toml`):

```toml
[sources.saucepan]
marker = ".saucepanhash"
order = []
# binary = "bin/saucepan" # Optional executable path; .exe on Windows
```

Marker and executable paths may be absolute or relative to that user home.
Without `binary`, the SDK uses Saucepan's shared user-level executable. Keep the
marker private; it belongs to the user environment, not project Git history.
The connection works with profile mode off. Homes without this table need no SDK
or Saucepan executable. A configured but unavailable connection fails explicitly.

Every eligible repository in the authenticated `overspec` scope contributes.
Overspec uses public returned paths, without copying acquired profiles into
`~/.overspec` or creating project profile directories. Repository layouts are:

| Category | First choice | Fallback when first choice is absent |
| --- | --- | --- |
| Standalone traits | `over-traits/**/trait*.toml` | `openspec/.over/**/trait*.toml`, excluding profiles/state |
| Profiles | `over-profiles/profile-*` | `openspec/.over/profile-*` |

Each category chooses independently. An empty top-level directory intentionally
disables that category's fallback. Invalid selected paths or declarations are
errors. Profiles are immediate directories; selected profile traits are recursive.
Inactive profile declarations are not parsed. Acquired variable files and skills
are not imported.

`order` lists canonical 64-character Saucepan source IDs from low to high priority.
Unlisted eligible sources come first, sorted by source ID. Later sources win;
refresh times never determine precedence. An absent/filtered listed source remains
an inactive priority entry. Use Saucepan's scoped view or Overspec's JSON
explanations to inspect IDs.

Profile selection chooses a **name**; source priority decides which declarations win.
Apply sources from low to high:

1. Packaged `profile-default`, when default is selected.
2. Each acquired repository in the order above: its selected profile, then its standalone traits.
3. Workspace `openspec/.over`: its selected profile, then its standalone traits.

Profiles extend trait-by-trait. Base `alpha,beta` plus extension `beta,gamma` yields
base `alpha`, extension `beta`, and extension `gamma`. A higher repository's profile
beats a lower repository's standalone declaration. A replacement replaces every
field; nonconflicting lower names survive. Duplicates within one profile contributor
or standalone layer are errors. An empty higher profile erases nothing. Every
selected contributor is validated, even when its declarations are overridden.

Automatic discovery uses only each source's **current whole-root artifact visible
in the Overspec app view**. Historical, folder-only, or pinned-only acquisitions
are excluded with guidance. If another app advances shared current, reacquire that
whole current root under `overspec` before it contributes. Sync, previews, and
listing never acquire, refresh, mirror, or change Saucepan filters. Acquisition
belongs to Saucepan; Overspec has no profile pull/update commands.

Run `overspec update` when the effective profile or compile-time declarations
change, then preview and sync. Ordinary/runtime-only refreshes need sync. Saved
runtime commands and details continue to work without Saucepan; they retain the
synchronized definitions and use the consuming project's variable rules.
`overspec trait resolve --explain --json` reports source provenance and exclusions;
`profile list --json` reports ordered `contributors` for each profile when mode
is on. Contributors identify `kind` (package/repository/workspace), origin/location,
and package version or repository source/revision. A composite profile has no
singular winning directory.

To run the real SDK/executable integration test, set
`OVERSPEC_TEST_SAUCEPAN_BINARY` to an installed executable and run
`uv run --extra saucepan pytest tests/test_saucepan_public_integration.py`.
The test uses an explicit isolated test store and never modifies the real user store.

## Sources and activation

```text
openspec/
  config.yaml
  .over/
    config.toml
    profile-default/
      traits.toml
      trait-tdd.toml
      trait-zuu.toml
    profile-team/
      nested/trait-python.toml
    team/trait-local.toml
```

Any immediate `.over/profile-<name>` directory is a profile. Trait files match
`trait*.toml` recursively: `trait.toml`, `traits.toml`, and nested
`trait-testing.toml` all qualify. Off mode uses `default`. Local project traits outside
every profile subtree supplement it; inactive profiles and `.state/` are excluded.
The repository's own authored traits all live in `profile-default`, so consumers
can reuse that directory as a unit.

User **settings** live under `~/.overspec`, overridden by `OVERSPEC_HOME` or
`--home`: activation, saved selection, Saucepan connection/order, and configured
variables. Direct user-home trait/profile directories and legacy remote copies
are not sources. They are neither migrated nor deleted automatically. Overspec
does not read or migrate `~/.over`, which may belong to another application.
Project sources and generated resolution state remain under `openspec/.over/`.

While mode is **off**, default composes the packaged base, repository extensions,
and workspace overrides. Other profile names and saved/environment selections
are ignored. Default is always available in a healthy installation.

`profile activate` toggles the optional profile feature for the chosen user home.
It takes no name: run it once to enable, and again to disable. Only `activate`
appears under `profile` while off; `list` and `use` become
available while on. Disabled commands are unavailable through direct invocation
and completion too. Ordinary project and trait commands work in both modes.

While mode is **on**, selection follows `OVERSPEC_PROFILE`, then the saved user
choice, then implicit `default`. All matching profile contributors compose in
source order. A named profile such as team does not implicitly inherit packaged
default. A missing explicit selection or an empty environment value is an error.
Project selectors, `--profile`, and `profile use --user` are not supported.

```sh
overspec profile activate
overspec profile list --json
overspec profile use team
overspec update
overspec sync
overspec profile activate
```

This example starts with mode off and an available `team` profile. The final
toggle returns to default resolution. Run `update` and then `sync` when changing
the effective profile; toggling with the same effective default does not alone
invalidate compilation. The commands never compile or sync implicitly.

The user settings are explicit:

```toml
[profiles]
enabled = true
selected = "team"
```

For an invocation override in PowerShell, set `$env:OVERSPEC_PROFILE = "team"`;
remove it with `Remove-Item Env:OVERSPEC_PROFILE`. In POSIX shells, use
`OVERSPEC_PROFILE=team overspec sync`. The variable only applies while mode is on
and does not rewrite the saved choice. `profile list` distinguishes the effective
profile, saved selection, and source scope; `profile use` reports any environment
override. Overspec does not modify shell startup files.

Toggling and selection update only the user settings, preserving unrelated fields
and the remembered choice when disabled. Project `.over/config.toml` holds project
variables. Profiles remain on disk. Profile identity disappears from emitted names.
Local declarations replace same-name profile declarations completely, including
details, lifetime, and attachment. Duplicate names within either layer are errors.

## Small traits, three lifetimes

```toml
[[trait]]
name = "review"
attach = "rules.proposal"
body = "State the observable outcome and how it will be verified."
details = "Give a concrete trigger and expected result; avoid implementation-only acceptance criteria."
```

| Declaration | Evaluation time |
| --- | --- |
| `[[compiletime-trait]]` | Init/update; results remain frozen between updates |
| `[[trait]]` | Every sync or read-only static resolve |
| `[[runtime-trait]]` | When the embedded resolution command runs |

`name`, `attach`, and a nonblank `body` are required. Names use lowercase letters,
digits, and hyphens, starting with a letter. Keep one responsibility in a few
self-contained sentences. Optional literal `details` holds explanations or
examples; omitted/blank details means no elaboration. Details are never automatically
inserted into config or normal runtime output. There is no arbitrary body word limit.

Attachments are `context`, `rules.<artifact-id>`, `operations.apply.guidance`, or
`operations.archive.guidance`. The whole suffix after `rules.` is a literal artifact
ID: `rules.review.notes` targets `review.notes`.

Context contributions end with `<!-- over:review -->`. Rule and operation list
items carry `# over:review` on their scalar header. Sync repairs missing/wrong
markers and removes stale contributions. Repeated equivalent sync preserves config
bytes and modification time.

## Assertions, actions, and variables

```toml
[[trait]]
name = "zuu"
attach = "operations.apply.guidance"
body = "Prefer applicable public zuu APIs before writing equivalent utilities."

[trait.assert.1]
[[trait.assert.1.assertion]]
type = "files-exist"
paths = [".python-version", "uv.lock"]
[[trait.assert.1.assertion]]
type = "python-dependency"
name = "zuu"
```

Every group uses AND by default; `or = true` selects OR for that group. A group
contains either `[[...assertion]]` leaves or numbered child groups. Child numbers
are positive integers without leading zeros and run in numeric order (`1`, `2`,
`10`); they need not be consecutive. Leaves run in array order. AND stops at the
first false child; OR stops at the first true child, at every depth.

For `(A AND B) OR (C AND D)`, put two AND groups under an OR root:

```toml
[[trait]]
name = "python-tooling"
attach = "context"
body = "Use the available Python environment tooling."

[trait.assert]
or = true

[trait.assert.1]
[[trait.assert.1.assertion]]
type = "files-exist"
paths = [".python-version", "uv.lock"] # A
[[trait.assert.1.assertion]]
type = "which"
app = "uv" # B

[trait.assert.2]
[[trait.assert.2.assertion]]
type = "files-exist"
paths = ["Pipfile.lock"] # C
[[trait.assert.2.assertion]]
type = "which"
app = "pipenv" # D
```

Nesting works the same way: `[trait.assert.2.1]` and `[trait.assert.2.2]` form
children of group 2. Set `or = true` on group 2 to make those alternatives while
the root remains AND. A simple root can also contain direct
`[[trait.assert.assertion]]` leaves.

Put `body`, `details`, and `actions` **before** assertion tables. TOML tables bind
to the latest declaration of their type, so use `compiletime-trait.assert` or
`runtime-trait.assert` for those lifetimes. Use the spelling `assertion`.

Omit `assert` for unconditional traits. Explicit empty groups, mixed leaves and
numbered children, and nonboolean `or` are errors. A leading `~` negates any leaf:
`~loaded-trait` means the referenced trait has not matched. Existing flat
`assert = [...]` with `assert_or_grouping` remains supported, including empty
lists and retained resolutions; do not combine that flag with group tables.
All references are validated even inside branches that evaluation would skip.

| Assertion | Payload and behavior |
| --- | --- |
| `which` | `app`: executable availability, without execution |
| `files-exist` | `paths`: all entries must be regular project-root files |
| `python-dependency` | `name`: normalized declaration in `project.dependencies` |
| `require-trait`, `loaded-trait` | `trait`: previously matched name, including prior phases |
| `runtime-context-match` | `kv = "flag=true"`: exact typed runtime comparison |
| `runtime-context-includes` | `k`, `includes`: exact list membership; `$variable` uses list overlap |

Dependency matching accepts versions, extras, direct references, and markers. It
checks declarations, not installed packages or active markers. Dev/optional-only
dependencies and `tool.uv.sources` do not establish a match. Missing files or lists
are non-matches; malformed inputs and inspection errors are reported.

```toml
actions = [{ type = "remove-trait", trait = "older-guidance" }]
```

An action runs only after a match. Removal suppresses output but preserves matched
history, so `loaded-trait` still succeeds for a matched suppressed trait. Evaluation
is a deterministic single pass: unknown/later-phase references fail; known forward
references have not matched yet. Runtime dependencies and suppression stay within
the same attachment group; runtime actions cannot suppress earlier phases.

Bodies support `${key}` scalar interpolation and `$$` for a literal dollar. Names,
attachments, and details are never interpolated. Missing or non-scalar body values
fail; body text is never executed. Optional variable files contain only `[vars]`:

```toml
[vars]
language = "Python"
strict = true
reviewers = ["maintainer", "peer"]
"build.target" = "desktop"
```

Use `openspec/.over/.vars.toml` for shared persistent defaults and
`openspec/.over/.current.toml` for mutable local state. The same filenames can
live directly in a selected OpenSpec change root, including an external store.
`.vars.toml` is optional and never automatically created; commit it when authored.
Init creates only missing current files, preserving existing bytes and times.
In each Git worktree, zuu verifies the `.current.toml` basename ignore pattern
without duplicating effective coverage. Setup reports tracked current files,
preexisting rules that ignore authored persistent files, and non-Git roots where
ignore coverage is unavailable. It never untracks files or initializes Git.
Partial setup reports each target's outcome and can be retried.

Missing/empty documents contribute no variables. Values can be finite scalars or
lists of scalars; lists replace whole values. Dates, nested tables/lists, and other
top-level fields are errors. Keys are literal, including quoted dotted keys.
Explicit JSON still supports null; there is no deletion sentinel. Lists cannot
be interpolated into bodies.

For static init/update/sync/resolve, precedence from highest to lowest is
`--vars-file` JSON, project current, project persistent, project
`.over/config.toml` vars, then user `~/.overspec/config.toml` vars. Change files
never affect shared static guidance. Compile-time values remain frozen until update. Changes to relevant
compile-time definitions, details, activation, or configured inputs require update;
ordinary/runtime-only edits need only sync.

## Runtime commands and saved details

```toml
[[runtime-trait]]
name = "archive-check"
attach = "operations.archive.guidance"
body = "Keep the current change unarchived."

[runtime-trait.assert.1]
or = true
[[runtime-trait.assert.1.assertion]]
type = "runtime-context-match"
kv = "do-not-archive=true"
[[runtime-trait.assert.1.assertion]]
type = "runtime-context-includes"
k = "do-not-archive"
includes = "$activeChanges"
```

Sync emits one command per resolution and attachment, with each trait ID once:

```sh
overspec trait resolve --resolution <id> --attach operations.archive.guidance --trait archive-check --trait another-check --context-file context.json
```

Run it from the owning project root, or supply `--project`. A context file is a JSON
object, for example `{"do-not-archive": ["example"], "activeChanges": ["example"]}`.
For newly synced version-2 resolutions, precedence is explicit context JSON,
selected-change current, selected-change persistent, project current, project
persistent, then retained configured defaults. Those defaults contain user/project
config and sync's explicit JSON, excluding variable-file layers. File layers are
read fresh for every invocation; removing a temporary file removes its override.
Both assertions and rendering see the final mapping. Exact matching remains typed;
includes supports list membership or `$name` list overlap, while equality does not
dereference variables. No regex, glob, or expression matching is added.

Append `--change-root <path>` from OpenSpec status to the emitted runtime command
for a selected change. The shared config contains no fixed change path or values.
Without selection only project layers apply. An invalid, moved, or redirected root
fails rather than falling back to another change. Only the currently synchronized
resolution is available; superseded IDs fail. Invocations do not share context. Returned
matched, unsuppressed bodies have individual name markers. Runtime resolution uses
the saved group and its history, runs offline, and writes no state. It does not
advance, block, or archive OpenSpec changes.

```sh
overspec trait resolve --explain
overspec trait show tdd --details
overspec trait show tdd --details --resolution <current-id>
```

`resolve --explain` shows the group tree, condition paths, operators, evaluated
reasons, and skipped branches. Add `--json` for structured traces. Migrating a
compile-time declaration to grouped tables requires `overspec update` before
sync; ordinary/runtime migrations need only sync. Previously synchronized runtime
commands retain their original conditions until sync replaces the current snapshot.

Default detail lookup uses the last successful sync receipt and verifies owned
config values and markers. Editing the active profile after sync does not change
the saved explanation. Edited owned config requires resync or an explicit current
ID; unowned edits do not invalidate the receipt. Lookup reports origin and phase,
does not reevaluate conditions or read live variable files, and returns an explicit
message if details are absent. Malformed current files do not prevent saved lookup.

State lives in one ignored `openspec/.over/.state.json`:

- `compilation` contains frozen results and inputs; init/update replace this section.
- `resolution` contains the currently synchronized definitions, static results,
  defaults, and literal details; sync replaces this section.
- `sync` identifies the resolution and fingerprints its generated guidance.

The document is root-bound and section hashes validate its content. Hashes are
identifiers, not generation filenames. Repeated equivalent writes preserve bytes
and modification time. State size follows current inputs, not the number of syncs;
no performance speedup is implied. Update preserves the current resolution until
sync, and runtime still reads variable files afresh. Copied state in another root
fails validation and needs that project's own init/sync.

Sync writes config before atomically saving the new resolution and receipt together.
If the state write fails, the previous state survives and the error explains that
config may have changed; retry sync. Default details verify the config fingerprint.
Use a single writer: these two replacements are not a cross-file transaction or lock.

For older installations containing `.over/.state/`, run `overspec init --setup-only`
to establish ignore coverage for the new file, then `overspec update`, inspect
`overspec sync --dry-run`, then `overspec sync`. This rebuilds current results; it
does not import old generations. After verifying runtime/details, remove only the
obsolete generated `.over/.state/` directory. Historical IDs no longer select old
data. A corrupt .state.json must be restored or moved aside before regeneration.

## Upgrading the source model

Legacy profile `pull`/`update` commands and direct user-home sources are removed
without compatibility aliases. For shared extensions, explicitly acquire their
whole repository through Saucepan in the `overspec` scope. Move independently
authored user-home traits into a workspace or source repository deliberately.
Old files remain untouched. An already acquired Overspec repository remains a
normal higher-priority repository source until you explicitly remove it through
Saucepan; it is no longer needed solely to obtain the packaged default.

Run top-level `overspec update`, review `overspec sync --dry-run`, then sync when
adopting a changed selected name or effective compile-time guidance. Package
version changes, installation relocation, and fully overridden lower changes do
not alone invalidate compilation. Saved runtime guidance remains usable until
successful synchronization replaces its resolution. Missing/corrupt bundled
content is an error, not a trigger to download a replacement.

## Development

For each behavior: write and run the focused test, observe its intended failure,
implement minimally, rerun to green, then refactor under passing tests. Preserve
the observed evidence. Nonbehavioral edits need appropriate verification rather than
artificial failing tests. The default `tdd` trait carries the compact instruction
and its full process in a separate details field.

```sh
uv run pytest -q
uv lock --check
uv build
openspec validate --all --strict
openspec validate --archived --strict
```

The full test suite requires the companion OpenSpec executable on PATH. It exercises
OpenSpec in temporary projects, ordered repository sources through an injectable
public SDK boundary, and actual wheel installation in an isolated environment
without Saucepan. Wheel tests build directly and from an sdist; installation can
fetch declared dependencies when uncached. The optional real Saucepan test uses
its own test store. No test modifies sibling repositories or the user store. Assertions and actions each implement an abstract
base contract with one concrete handler per file under `src/overspec/core/`.
