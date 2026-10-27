# D-024 — Future Automated Release and User-Initiated Update

- **Status:** Accepted as deferred future direction
- **Date accepted:** 2026-10-27

## Context

The PO wants future automated releases, update notifications and safe one-click installation for end users.

## Decision

- Defer CI/CD release automation, signing, installer design, version management, update notifications and one-click add-in updates until after initial local prototypes are accepted.
- Research Excel/XLL trust, signing, installer privileges, Excel-in-use replacement constraints, version compatibility, security, rollback and recovery before approving a deployment mechanism.
- Do not promise in-place updates without Excel restart until technically demonstrated; use the smallest safe Windows/Excel-compatible updater design.

## Consequences

Commercial distribution remains future scope; no updater service, pipeline or release infrastructure is created by this documentation migration.
