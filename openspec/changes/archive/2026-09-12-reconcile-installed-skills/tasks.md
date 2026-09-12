## 1. Reconciliation

- [x] 1.1 Adapt existing real ZuAT lifecycle tests, observe RED for repeated install and automatic unowned/edited replacement, implement reconciliation through existing APIs, and verify exact bytes, no-op history, scoped restoration, and provider/identity errors under GREEN.
- [x] 1.2 Update Typer signatures/help and observe CLI RED then GREEN for repeated install/refresh and removal of install/update --force; preserve restore/remove controls.

- [x] 1.3 Integrate ZuU case11 required agent/skill selectors after observed RED; verify actual selector confirmation/cancellation, recorded historical choices, and noninteractive/JSON behavior before native mutation.

## 2. Documentation and verification

- [x] 2.1 Revise README and packaged bootstrap/configure guidance; validate edited skill metadata and ensure current instructions no longer require force for install/update.
- [x] 2.2 Run affected lifecycle/CLI and installed-package checks plus strict change validation; record observed results in utility-evidence.md and commit implementation separately from active change artifacts.
