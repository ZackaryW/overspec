## 1. User-home connection and scoped adapter

- [x] 1.1 Write and run failing tests for optional `[sources.saucepan]` settings, marker/binary paths, ordered source IDs, invalid configuration, and preservation through profile toggles; implement settings parsing until green. Verify disconnected homes require no Saucepan import and profile activation does not control this connection.
- [x] 1.2 Write failing adapter tests for authenticated `overspec` views, invalid proof/app identity, missing executable, and unsupported responses; implement an injectable adapter over the public Python SDK until green. Add and lock an optional SDK extra at a verified release or immutable revision; verify ordinary installation remains usable without it and diagnostics never expose tokens.
- [x] 1.3 Write failing tests for whole-current-root selection, historical/folder-only artifacts, pins, filters, and a shared current snapshot invisible to Overspec; implement scoped inventory selection until green. Verify each eligible source contributes once, excluded sources have guidance, and no internal storage traversal or acquisition occurs.

## 2. Repository layouts and profile candidates

- [x] 2.1 Write failing tests for independent top-level/fallback selection, intentional empty directories, missing categories, malformed selected content, and invalid or redirected roots; implement layout selection until green. Verify unselected fallback declarations are not read.
- [x] 2.2 Write failing tests for recursive standalone `trait*.toml` discovery, profile/state exclusions, confinement, and duplicate physical files; implement scanning through existing zuu-backed boundaries until green. Verify fallback profile content cannot leak into standalone layers.
- [x] 2.3 Write failing tests for immediate `profile-*` candidates, same-name whole-profile replacement, inactive malformed profiles, and recursive selected-profile declarations; implement the external catalog until green. Verify only the winning selected profile is parsed.

## 3. Deterministic composition and explanation

- [x] 3.1 Write failing tests for lexical unlisted sources, explicit low-to-high source order, inactive configured IDs, and shuffled view entries; implement stable priority until green. Verify refresh time and artifact identity cannot change precedence.
- [x] 3.2 Write failing tests for selected-profile, external, user-standalone, and project-standalone layers; generalize composition until green. Cover complete replacement across types/attachments/details, errors within a layer, final-inventory reference validation, and stable insertion/phase order.
- [x] 3.3 Write failing lifecycle tests for external default with mode off, project/user profile overrides, enabled named selection, absent default, and legacy user-tier collisions; integrate external candidates and user standalone scanning until green. Verify no copied profile directories or extra commands appear and existing activation/environment rules hold.
- [x] 3.4 Write failing explanation/listing tests for source ID, revision, relative path, selected layout, exclusions, and winners/losers; implement provenance until green. Verify emitted trait identities remain plain names and no connection secret enters saved output.

## 4. Compilation, saved resolutions, and publication

- [x] 4.1 Write failing tests for runtime-only refresh, effective compile-time changes, overridden compile-time declarations, selected-profile changes, and unrelated repository changes; integrate stable origin/compatibility inputs until green. Verify snapshot cache-path changes alone do not require update, while effective compilation changes do.
- [x] 4.2 Write failing tests for saved runtime/details access after removing the connection or making Saucepan unavailable; integrate saved provenance until green. Verify current-only resolution IDs, fresh consuming-project variables, and exclusion of acquired repository variable files remain intact.
- [x] 4.3 Write failing race tests for view/filter/current-pointer changes, source files and layout changes, and connection/priority edits during preparation; add captured evidence and publication rechecks until green. Verify rejected publication, unchanged no-op bytes/mtime, and truthful config-first/state-second partial failure reporting.

## 5. Public integration, documentation, and verification

- [x] 5.1 Add an isolated SDK/executable integration test using Saucepan's explicit test-store facilities and local repository fixtures; first demonstrate the missing integration, then pass it. Exercise registration/acquisition only inside that test store, public view verification and paths, both layouts, and scope isolation; verify the user's real store is untouched.
- [x] 5.2 Document the optional dependency/executable prerequisites, user-home connection, source ordering, top-level layouts, fallback rules, and whole-current-root limitation. Update relevant bootstrap/trait-authoring guidance without copying skill workflows into traits; validate examples and skill structure. State that pull/update redesign and source skill/variable imports remain outside this change.
- [x] 5.3 At meaningful source implementation milestones, use `zmem-author-commits` under existing authorization and review each staged diff. Verify incremental commits include relevant nonignored tests/config/skills but exclude this active change's artifacts and generated local state.
- [x] 5.4 Run the full regression suite, targeted public integration, configured lint/build/lock checks, and strict OpenSpec validation; resolve failures and record results. Verify implementation against every delta scenario before requesting the user's explicit archive outcome; leave this change active until that outcome is supplied.
