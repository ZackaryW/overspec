---
name: create-overspec-trait
description: Create or revise Overspec TOML traits, including skill references, grouped assertions, lifetimes, and OpenSpec attachments. Use when adding reusable project guidance through traits or adapting existing guidance into a trait.
---

# Create an Overspec Trait

Express one responsibility in a small trait that fits the existing composition
model. Inspect the target project's profile sources and current parser before
authoring; do not introduce new model fields or handlers as part of a source edit.

Read [references/trait-format.md](references/trait-format.md) for the current
declaration format and condition rules.

## Choose the source and behavior

- In this repository, put all authored traits in
  `openspec/.over/profile-default/`, normally a separate `trait-<purpose>.toml`.
  This directory is also the reusable default-profile source. In another project,
  follow its requested profile or local-override scope rather than assuming the
  same authoring policy.
- Profile mode defaults off and still uses default with project overrides. Do not
  enable profile management merely to create a default trait. User profiles live
  under `~/.overspec`; project sources remain under `openspec/.over`.
- Choose a short stable name, one evaluation lifetime, and one attachment. Use
  `trait` for conditions refreshed at sync, `compiletime-trait` for intentionally
  frozen init/update checks, and `runtime-trait` only for invocation-time inputs.
- Keep the body brief and independently actionable. Put optional explanations or
  examples in literal `details`; details are not emitted into config automatically.
- When asked to reference an existing skill, name that skill exactly in the body
  and keep its workflow in the skill. Verify the skill exists in the intended
  environment. Do not copy its procedure into body or details, install it, or
  invent a skill-loading assertion. Tool availability does not establish skill
  availability; report a missing referenced skill plainly.
- Omit conditions for always-applicable guidance. Add only conditions that express
  the intended applicability; do not gate a trait on unrelated tooling. A skill
  reference does not itself authorize actions such as creating commits.

## Validate and integrate

Use the repository's parser to validate authored TOML, then validate it with the
effective inventory so duplicate names, dependencies, and phase restrictions are
checked together. In this checkout, the relevant entry points are
`overspec.core.trait_system.sources.parse_document(text, origin)` and
`overspec.core.project.Project(root, home).inventory()`.

For a new conditional behavior, establish an intended failing test first, then
verify matching and nonmatching cases through observable resolution or sync
output. Use temporary projects/homes and controlled assertion inputs. Prose-only
changes need parsing and output review rather than artificial failing tests.

Use the project's installed `overspec` command, or `uv run overspec` here:

```sh
overspec trait resolve --explain
overspec sync --dry-run
```

Missing compilation requires `init`; changed compile-time definitions require
`update`. Ordinary/runtime source edits need only sync. Respect the user's scope
when writing compilation or synchronized configuration. When sync is requested,
inspect the preview, sync, and verify the emitted body/reference and source marker;
sync replaces owned guidance fields. Keep optional details out of generated text.

For runtime traits, execute the saved resolution command with representative
context to check its output. Sync emits one command per resolution/attachment,
not unconditional runtime bodies. Report the source file, lifetime, attachment,
applicability, and validation performed.
