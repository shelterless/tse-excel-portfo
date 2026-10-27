# Product Context — TSE Excel Portfolio

## Product purpose

Build a maintainable Excel add-in to retrieve, validate, analyze and present Iranian securities-market data. The first use case comes from an Excel market-watch/portfolio workbook and includes prices, price limits, buy/sell queues, retail participant counts, estimated retail flow and trading-state diagnostics. The potential to expand to all listed symbols and commercial analytics is a **future possibility**, not an approved first-phase deliverable.

The GitHub repository is `shelterless/tse-excel-portfo`; the current ChatGPT Project name is `Mohsen-TSE-Excel`.

## Background observations

- A prior personal Excel/VBA prototype was developed and tested. This provides a behavioral reference, not proof of the new add-in's implementation.
- The bulk MarketWatch endpoint omitted some instruments whose individual TSETMC instrument endpoint still returned valid details. In earlier tests, SHPNA and FGOSTAR were examples of a halted state (`IS`).
- Bulk retail/institutional participation (ClientType) coverage varied between executions; successful HTTP responses alone do not prove a full, fresh snapshot.
- Errors should not silently zero out previous valid quotes, destroy formulas or falsely describe a halted security as an invalid identifier.

## Approved direction

- **C#/.NET + Excel-DNA/XLL** for an initially Windows desktop Excel add-in; **no VBA/VB** in the new product.
- Excel remains the presentation, workbook, tables and formulas layer; typed C# modules handle domain rules and market-data integration.
- Local-first building/testing/installation for MVP.
- Strong OOP/SOLID/type safety/automated unit-test requirements are mandatory for **every implementation change**, per [ENGINEERING-STANDARDS](../engineering/ENGINEERING-STANDARDS.md).
- **PO** approves scope, performs local acceptance tests and commits source. **ChatGPT** consults, documents and writes Codex work packages; it reads source read-only and commits only PO-approved documentation. **Codex** implements/tests but never commits.

## Immediate proof of concept — before the market-data MVP

The first milestone is a deliberately minimal Excel-DNA Ribbon prototype for Windows desktop Excel, built locally with C#/.NET and VS Code without requiring Visual Studio. It precedes, but does not replace, the market-data MVP below.

- A saved workbook has a corresponding business-configuration JSON file beside it, with the same basename (for example, `Analysis.xlsx` and `Analysis.json`). This is not the installed add-in's own configuration.
- A Ribbon command can explicitly create a minimal JSON file when absent, without overwriting an existing file.
- A separate test Ribbon command reads the corresponding JSON and displays its contents in a message dialog.
- Unrelated workbooks must remain unaffected; the add-in must not automatically create configuration files for them.
- Locking, JSON edits through the add-in, concurrent-workbook coordination, market API calls, automatic worksheet creation, licensing and commercial packaging are out of scope for this first prototype.

Later phases may support watchlists, symbol names and exact textual `InsCode` identifiers, stop-loss and target settings, and both manual user editing and add-in-managed editing. The intended rule is manual editing while the corresponding workbook is closed, and add-in-controlled editing with locking while it is open. The JSON schema, file-locking implementation, Save As behavior and concurrent-workbook policy remain open for later design and approval.

Guide the PO through local setup and prototype acceptance **one actionable step per turn**, continuing only after the PO confirms the preceding step.

## MVP behavior

1. Load quotes and supplemental data for a confirmed Excel table contract.
2. Resolve instruments using exact `InsCode` and reliable fallback methods for symbols absent from bulk snapshots.
3. Derive or label trading states, queue volumes and retail metrics with clear source/estimate semantics.
4. Report missing/partial/stale/error conditions without destructive writes.
5. Provide a usable Excel refresh interaction and accurate operation summary.

## Out of scope for MVP

Auto-Updater, license/subscription management, hosted backend, commercial data service, production licensing/distribution and Python engine. These may be considered after an MVP acceptance milestone.

### Deferred commercial distribution and updates

A later phase may provide automated CI/CD, signed add-in release packaging, notifications when a new version is available, and a safe user-initiated one-click update experience. Installer privileges, Excel/XLL file locks, possible Excel restart requirements, compatibility, rollback, trust and signing must be assessed before choosing an updater design. No release or updater infrastructure is part of the first JSON proof of concept or is authorized by this statement.

## Unresolved decisions — ask PO when material

- .NET and Excel-DNA versions, minimum Excel/Windows version and x86/x64 support.
- Exact initial workbook schema, migration plan, ribbon interaction and local installation mechanism.
- Data-source access limits, legally permissible commercial usage, quote update cadence and freshness criteria.
- Precise product packaging/security model and deployment requirements.

## Privacy and boundaries

This repository is a **software product repository**, not a personal accounting record. It was public when these documents were drafted. Avoid personal positions, brokerage evidence, confidential algorithms and secrets in this repository unless privacy and authorization have been explicitly resolved.
