# Utility plan

Mode: plan, called by propose through native design. Application implementation is needed, but no new shared utilities, trait assertions, or trait actions are needed.

## Ponytail reuse assessment

| Responsibility | Existing capability | Decision |
| --- | --- | --- |
| Git acquisition, current revision, verification, retention | Saucepan SDK acquire and central store | Reuse after upstream unscoped acquisition is available; do not wrap scoped Overspec discovery or build a second clone cache. |
| Confined source/destination identities | ZuU case5 (independently pinned for scripts) ConfinedPath.inspect and plan.revalidate | Reuse; descendant content requires separate snapshot validation. |
| Stable regular-tree bytes and comparison | ZuU case2 (independently pinned for scripts) FileSystemSnapshot.capture, files, and content | Reuse for the three selected trees and local comparison. |
| Packaged skill catalog | hatch_build.py force_include; core/package_assets.py | Existing downstream packaging remains unchanged; do not import this application code into the script. Distribution tests already cover support files and isolated installed resources. |
| Which skills, destination, provenance, review behavior | New repository maintenance script | Application policy, not a new core utility case. Use standard file staging/replacement with explicit rollback evidence. |

Source findings: no existing Lefthook config or scripts directory in Overspec; the three zmem trees already exist locally as untracked content. Existing catalog discovery includes any immediate SKILL.md directory, so no catalog expansion is needed. No change to those untracked trees is authorized by this planning operation.

Repository memory reinforces keeping build-time copies separate from installed native skill lifecycle and keeping state writes honest about partial publication. Current source/spec contracts take precedence.

## Application boundary to implement later

`sync_zmem_skills(repo_root: Path, client: Saucepan) -> SyncResult` is a proposed script-local entry point, not a public Overspec API. All implementation/helpers and focused tests live under scripts/, with their own pyproject.toml and uv.lock. Neither execution nor dependency resolution requires the Overspec package, root environment, or root configuration. Inputs are the owning repository and an unscoped client; output reports changed paths and resolved provenance. Side effects are acquisition in Saucepan's store and writes confined to three destination trees plus the provenance record. Errors cover unavailable prerequisites, invalid payloads, redirected destinations, and publication failures. The script's command-line wrapper maps unchanged to success, changed to a review-required status in hook mode, and operational failure to a distinct nonzero status.

Focused verification: a local Git fixture through real Saucepan, first sync/update/removal/no-op and malformed-tree preservation, hook exit behavior, an isolated run with Overspec unavailable, and existing downstream distribution tests. Do not retest Saucepan's provider matrix or ZuU's path normalization. Utility maturation is not applicable; script behavior and integration remain pending for apply.
