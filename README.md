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

This repository provides its reusable profile at `openspec/.over/profile-default`.
Copy that directory into your project's `openspec/.over/`. Profile mode is off
by default; ordinary setup needs no activation:

```sh
overspec init --project /path/to/project
overspec sync --project /path/to/project --dry-run
overspec sync --project /path/to/project
```

Run commands through `uv run overspec` when using this checkout rather than an
installed console command. Remote retrieval is available after enabling profile
mode, as described below.

Sync deliberately replaces all existing context and rules, plus apply/archive
guidance. Put any manual guidance you want to retain in traits before syncing.
Other configuration values, including unknown keys and operation siblings, survive.
Preview prints the target, candidate YAML, diff, resolution ID, and whether config
would change. Add `--json` for structured output.

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

User profiles live under `~/.overspec`, overridden by `OVERSPEC_HOME` or `--home`.
User mode and selection are stored in `~/.overspec/config.toml`, with remote downloads and
revisions under `~/.overspec/.state/remotes/`. Overspec does not automatically read
or migrate `~/.over`, which may belong to another application. Project sources and
resolution state remain under `openspec/.over/`.
While mode is **off**, Overspec uses `profile-default` automatically. A project
default completely replaces a user default. Loose local traits then override
same-name profile traits. Other named profiles and saved/environment selections
are ignored. Without a default, loose local traits alone still work. A previously
retrieved user default remains usable offline.

`profile activate` toggles the optional profile feature for the chosen user home.
It takes no name: run it once to enable, and again to disable. Only `activate`
appears under `profile` while off; `list`, `use`, `pull`, and `update` become
available while on. Disabled commands are unavailable through direct invocation
and completion too. Ordinary project and trait commands work in both modes.

While mode is **on**, selection follows `OVERSPEC_PROFILE`, then the saved user
choice, then implicit `default`. A project source still completely replaces a
same-name user source. A missing explicit selection or an empty environment value
is an error. No implicit default allows local-only composition. Project profile
selectors, `--profile`, and `profile use --user` are no longer supported.

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
fail; body text is never executed. Put scalar variables under `[vars]` in user or
project `.over/config.toml`, or pass a JSON object with `--vars-file` to init, update,
sync, or static resolve. Invocation values override project values, which override
user values. Compile-time values remain frozen until update. Changes to relevant
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
Missing context is an empty object; invocations do not share context. Returned
matched, unsuppressed bodies have individual name markers. Runtime resolution uses
the saved group and its history, runs offline, and writes no state. It does not
advance, block, or archive OpenSpec changes.

```sh
overspec trait resolve --explain
overspec trait show tdd --details
overspec trait show tdd --details --resolution <older-id>
```

`resolve --explain` shows the group tree, condition paths, operators, evaluated
reasons, and skipped branches. Add `--json` for structured traces. Migrating a
compile-time declaration to grouped tables requires `overspec update` before
sync; ordinary/runtime migrations need only sync. Previously synchronized runtime
commands retain their original conditions and remain usable.

Default detail lookup uses the last successful sync receipt and verifies owned
config values and markers. Editing the active profile after sync does not change
the saved explanation. Edited owned config requires resync or an explicit historical
ID; unowned edits do not invalidate the receipt. Lookup reports origin and phase,
does not reevaluate conditions, and returns an explicit message if details are absent.

State lives in `openspec/.over/.state/`. Bundles are immutable, content-addressed,
and bound to the project root. Keep the matching state to execute retained runtime
commands; copied config in another project needs that project's own init/sync.
Garbage collection is not implemented. Bundle publication precedes config replacement;
the receipt follows it. A receipt failure reports that config may already have changed
and can be retried. Use a single writer: atomic config replacement is not a multi-file
transaction or cross-process lock.

## Remote profiles

`profile pull` registers and retrieves a public GitHub directory through
`zuu.case12.GitHubSubpath`. Omit a selector for the default branch, or use `--branch`
or a full 40-character `--commit`. `profile update NAME` refreshes the registered
source. Retrieval never activates profiles or recompiles projects implicitly.

Starting with profile mode off:

```sh
overspec profile activate
overspec profile pull default --owner ZackaryW --repo overspec --path openspec/.over/profile-default
overspec profile use default
```

The remote example requires publication on GitHub. Local copies work before
publication. Retrieval and refresh require enabled mode. Disabling preserves
downloaded revisions and the saved selection; existing runtime commands and
saved detail lookup remain usable regardless of mode.

Downloads live in an owned user-state directory. Every retrieval, including cache
hits, validates source content before publishing a revision. Failed downloads or
validation preserve the last usable revision and activation. Local/remote user-name
collisions are errors. A registered source cannot be changed in place; choose another
name. Ordinary sync, runtime resolution, and detail lookup never fetch remotely.

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
OpenSpec in temporary projects and remote retrieval with generated ZIP archives
through zuu's public injectable client; it does not modify sibling repositories or
depend on live GitHub availability. Assertions and actions each implement an abstract
base contract with one concrete handler per file under `src/overspec/core/`.
