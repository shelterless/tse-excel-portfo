# Decisions and Open Questions

This file separates **explicitly approved decisions** from design proposals, observations and unresolved choices. Only the Product Owner (PO) approves or changes binding decisions.

## Confirmed decisions

| ID | Decision | Status |
|---|---|---|
| D-001 | Canonical repository: `shelterless/tse-excel-portfo`, branch `main` | Approved |
| D-002 | New product implementation uses **C#/.NET; no VBA/VB** | Approved |
| D-003 | Excel-DNA/XLL is the initial add-in integration direction | Approved direction |
| D-004 | Workbook manages user data, formulas and display; compiled C# handles integration/logic | Approved direction |
| D-005 | MVP uses local build/install; **Auto-Updater deferred** | Approved |
| D-006 | ChatGPT Project uses minimal bootstrap, `docs/gpt/`, and task-based lazy loading | Approved |
| D-007 | Conversation with ChatGPT is **Persian**; **all documentation, technical context, source comments and docstrings are English**, except explicit PO exceptions | Approved |
| D-008 | Implementation quality requires **OOP, SOLID, type safety, justified design patterns and automated unit tests for every code change**, including small changes | Approved |
| D-009 | User acts as **Product Owner**, approves requirements/architecture, runs local acceptance tests and **alone commits/pushes source** | Approved |
| D-010 | ChatGPT acts as advisor, analyst and **documentation steward**; source **read-only**, prepares complete Codex prompts | Approved |
| D-011 | Codex is the developer; it writes code/tests but **never commits/pushes/tags/merges PRs/publishes releases** | Approved |
| D-012 | ChatGPT can **commit documentation only after PO approval of its finished draft**, directly to `main`; it never modifies source/tests/project/build/config files | Approved |
| D-013 | The [Operating Contract](OPERATING-CONTRACT.md) is a **mandatory first read at the start of every conversation**; load other docs lazily | Approved |
| D-014 | ChatGPT announces Project Instructions re-paste **only when `PROJECT-INSTRUCTIONS.md` changes**; changed context Source files must be synchronized separately | Approved |
| D-015 | Commercial backend, licensing/subscription infrastructure and Python runtime are deferred beyond MVP | Approved as deferral |
| D-016 | First deliver a minimal Ribbon prototype that creates a workbook-adjacent JSON file and displays its contents; it precedes and does not replace the market-data MVP | Approved |
| D-017 | Workbook-specific business configuration uses a same-basename JSON file alongside the saved workbook; creation must be explicit and must not overwrite an existing file | Approved direction |
| D-018 | Future business configuration may be edited by users and the add-in; manual edits are intended while the matching workbook is closed, with add-in-managed edits and locking while it is open | Approved direction; implementation deferred |
| D-019 | Guide the PO through local setup and prototype verification one actionable step at a time, advancing only after confirmation | Approved |
| D-020 | Codex is the implementation tool; documentation does not prescribe its underlying model | Approved |
| D-021 | After approval of finished documentation changes, ChatGPT itself commits only those changes directly to `main`, without requiring the PO to apply patches | Approved |

## Unresolved decisions (do not guess)

| Topic | Status |
|---|---|
| Minimum supported Excel and Windows versions, x86/x64 and exact .NET/Excel-DNA versions | Open |
| Actual `.sln`/project structure, NuGet versions, Ribbon UX and local add-in installation | Proposed only |
| Workbook schema versioning and migration from the VBA prototype | Requires current workbook inspection and PO approval |
| Market-data freshness, ClientType publication timing, bulk coverage thresholds | Open; needs evidence |
| TSETMC terms of use, scaling/rate limits and rights for commercial redistribution | Open |
| Public versus private repository for proprietary source code | Open; currently observed as public |
| Source build automation, signing and release distribution | Future decisions |
| Business JSON schema, locking mechanism, Save As behavior and concurrent-workbook policy | Deferred; requires future design and PO approval |

## Technical evidence — not binding API contracts

- Earlier tests observed `instrumentState.cEtaval` values `A` (permitted) and `IS` (halted).
- SHPNA and FGOSTAR were missing in a bulk API snapshot but returned valid individual endpoint data and `IS` state.
- ClientType snapshot coverage varied significantly across observed tests.

For technical interpretation, consult [WORKBOOK-CONTRACT](WORKBOOK-CONTRACT.md) and [DATA-RELIABILITY](DATA-RELIABILITY.md). For role authority, consult [OPERATING-CONTRACT](OPERATING-CONTRACT.md).
