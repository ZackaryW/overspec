# Trait format

Sources are TOML arrays of declarations. Filenames match `trait*.toml` recursively.
Each declaration requires `name`, `attach`, and a nonblank `body`; optional fields
are `details`, `assert`, and `actions`. Names match `[a-z][a-z0-9-]*`. One file can
contain multiple declarations, but a separate file helps keep a responsibility small.

| Declaration | Evaluation |
| --- | --- |
| `[[compiletime-trait]]` | Init/update; retained between updates |
| `[[trait]]` | Sync or read-only static resolution |
| `[[runtime-trait]]` | Stage invocation, using current definitions and variables |

Attachments are `context`, `rules.<artifact-id>`, `operations.apply.guidance`, and
`operations.archive.guidance`. The entire suffix after `rules.` is one literal
artifact ID. Use context for guidance that applies across operations, such as a
commit-authoring skill reference; there is no `operations.commit.guidance` target.

## Small reference trait

For an externally shared repository, standalone traits belong in `over-traits/`
and profiles in `over-profiles/profile-<name>/`. Each category independently falls
back to `openspec/.over/` when its top-level directory is absent. An existing empty
top-level directory suppresses fallback. This repository keeps its authored
default under `openspec/.over/profile-default`; no relocation is required.

The consumer applies packaged default, acquired repositories in stable source
order, then the workspace. Each repository/workspace applies its selected profile
before its own standalone traits. A higher source profile beats lower standalone
traits. All same-name profile contributors extend trait-by-trait; a matching name
replaces the complete declaration, including phase, conditions, body, and details.
Duplicates within one profile contributor or standalone layer fail. Use plain
names without source/profile prefixes. Only selected-name profile bodies are
parsed, and named profiles do not implicitly inherit default. Direct user-home
traits/profiles are not sources. Source variables and skills are not imported.

```toml
[[trait]]
name = "zmem-commits"
attach = "context"
body = "When authoring or reviewing commit messages, use the zmem-author-commits skill."

[trait.assert.1]
[[trait.assert.1.assertion]]
type = "which"
app = "zmem"
```

This checks the executable at sync. It neither installs nor executes the skill.
For unconditional guidance, omit the whole assert section.

## Grouped conditions

Each group uses AND by default; `or = true` selects OR for that group. A group
contains either a nonempty `assertion` array or numbered child groups, recursively.
Never mix both kinds within one group. Numbered keys are positive decimal integers
without leading zeros and are evaluated numerically; array leaves retain order.
Empty groups and nonboolean `or` fields are invalid. Groups short-circuit.

This expresses `(uv project files AND uv executable) OR poetry executable`:

```toml
[[trait]]
name = "python-environment"
attach = "operations.apply.guidance"
body = "Use the project's available environment manager when running checks."

[trait.assert]
or = true

[trait.assert.1]
[[trait.assert.1.assertion]]
type = "files-exist"
paths = [".python-version", "uv.lock"]
[[trait.assert.1.assertion]]
type = "which"
app = "uv"

[trait.assert.2]
[[trait.assert.2.assertion]]
type = "which"
app = "poetry"
```

Use the owning phase prefix throughout: for example
`[[runtime-trait.assert.1.assertion]]`. TOML binds nested tables to the most recent
declaration of that type. Put body, details, and actions before nested tables or
they will become fields of the last opened table. Use the spelling `assertion`.
Prefer grouped tables for new traits; legacy flat arrays exist for older sources.

| Assertion type | Payload |
| --- | --- |
| `which` | `app = "tool"` |
| `files-exist` | `paths = ["path/to/file"]`; all must be regular project-root files |
| `python-dependency` | `name = "zuu"`; normalized declaration in project.dependencies |
| `require-trait`, `loaded-trait` | `trait = "name"`; previously matched trait |
| `runtime-context-match` | `kv = "flag=true"`; typed scalar equality |
| `runtime-context-includes` | `k = "changes"`, `includes = "$activeChanges"`; list overlap |

A leading `~` negates a leaf, such as `type = "~loaded-trait"`. It does not name a
different handler. Runtime-context assertions belong only in runtime traits.
Validate references even in branches that would be skipped. References cannot
point to unknown names or later phases; runtime-to-runtime references must stay
within the same attachment. Evaluation is ordered, not recursive trait loading.

An optional root action is `actions = [{type = "remove-trait", trait = "name"}]`.
It suppresses output only after a match; matched history remains available.
Suppression follows phase restrictions and runtime attachment boundaries.

## Bodies, overrides, and saved details

Bodies support `${key}` scalar interpolation and `$$` for a literal dollar.
Names, attachments, and details are not interpolated. Bodies are not executed.
Do not write generated provenance markers into source bodies; sync adds them.

Profile contributors compose trait-by-trait from package through acquired repositories to workspace. Matching names replace complete declarations, including omitted details; other lower names survive. Standalone declarations follow the selected profile within each source. Duplicates within a layer are errors.

`overspec trait show NAME --details` reads details retained by the last successful
sync; `--resolution ID` must match the current snapshot in `.over/.state.json`.
Superseded IDs fail; no historical generations are kept. Editing live source does not
rewrite previously saved details. Runtime guidance loads current definitions and
variables from the current source/profile selection without a resolution ID.

## Scoped variable inputs

Use optional `[vars]` documents at `openspec/.over/.vars.toml` for committed
defaults and `.current.toml` for ignored local overrides. Both filenames also
work directly inside an explicitly selected OpenSpec `changeRoot`. Neither is
a trait source. For example:

```toml
[vars]
strict = true
language = "Python"
reviewers = ["maintainer", "peer"]
"build.target" = "desktop"
```

Only finite scalars and lists of scalars are accepted; no dates, nested tables,
nested lists, or other root fields. Lists override whole lists and cannot render
into bodies. Dotted keys are literal. Missing files are empty layers; explicit
JSON null remains supported.

Static precedence is explicit `--vars-file` JSON over project current, persistent,
project config vars, and user config vars. Change variables do not enter static
sync. Changed inputs used by compiled bodies require update; ordinary bodies are
fresh at sync. Runtime assertions remain runtime-only.

Runtime precedence is `--context-file` JSON over selected-change current,
selected-change persistent, project current, project persistent, project config,
and user config vars. Files are reread for each invocation and feed both conditions
and body rendering. Removing a layer does not restore its old captured values.
Match is exact and typed; `$name` dereferencing is supported only for an includes
list operand, not equality. No regex/glob/expression predicates are available.

Get the exact change root using `openspec status --change <name> --json`, keeping
the selected `--store`. Append `--change-root <path>` to the runtime command.
Omitting it means project-only variables, not automatic active-change selection.
External roots are allowed; missing/moved/redirected ones fail. Legacy multi-file
state requires explicit update then sync; old commands are not historical lookups.
Details remain literal and readable even when live variable files fail.

Use `overspec-bootstrap` for setup decisions: `overspec init` creates missing
current files during first compilation; `overspec init --setup-only` handles later
changes without recompilation. Init accepts either `--store <id>` for discovery
or repeatable `--change-root <path>` for exact targets, never both. Setup never
creates persistent files or untracks current files. Commit authored persistent
files when their records are retained; keep current files local.

## Reuse existing conditions

For configurable guidance, use runtime traits with a leading negated runtime-context-match for a typed-false policy control. Use runtime-context-includes for explicit list selection, including bdd framework names. Do not add handlers, actions, attachment types, or test suites for a trait-only migration. If an actual capability is missing, surface it as separate scope.
