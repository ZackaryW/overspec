# Trait format

Sources are TOML arrays of declarations. Filenames match `trait*.toml` recursively.
Each declaration requires `name`, `attach`, and a nonblank `body`; optional fields
are `details`, `assert`, and `actions`. Names match `[a-z][a-z0-9-]*`. One file can
contain multiple declarations, but a separate file helps keep a responsibility small.

| Declaration | Evaluation |
| --- | --- |
| `[[compiletime-trait]]` | Init/update; retained between updates |
| `[[trait]]` | Sync or read-only static resolution |
| `[[runtime-trait]]` | Saved runtime command with invocation context |

Attachments are `context`, `rules.<artifact-id>`, `operations.apply.guidance`, and
`operations.archive.guidance`. The entire suffix after `rules.` is one literal
artifact ID. Use context for guidance that applies across operations, such as a
commit-authoring skill reference; there is no `operations.commit.guidance` target.

## Small reference trait

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

Project `profile-<name>` replaces the same-name user profile as a complete source.
Loose local traits outside profile trees then replace same-name declarations
completely, including omitted details. Duplicates within a layer are errors.

`overspec trait show NAME --details` reads details retained by the last successful
sync; `--resolution ID` selects a historical bundle. Editing live source does not
rewrite previously saved details. Runtime guidance likewise uses its saved bundle,
even when current profile mode or selection changes.
