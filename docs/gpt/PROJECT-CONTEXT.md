# Product Context — TSE Excel Portfolio

## Product purpose

Build a maintainable Excel add-in to retrieve, validate, analyze and present Iranian securities-market data. The first use case comes from an Excel market-watch/portfolio workbook and includes prices, price limits, buy/sell queues, retail participant counts, estimated retail flow and trading-state diagnostics. The potential to expand to all listed symbols and commercial analytics is a **future possibility**, not an approved first-phase deliverable.

The GitHub repository is `shelterless/tse-excel-portfo`; the proposed ChatGPT Project name is `Mohsen-Portfo-TSE-Excel`.

## Background observations

- A prior personal Excel/VBA prototype was developed and tested. This provides a behavioral reference, not proof of the new add-in's implementation.
- The bulk MarketWatch endpoint omitted some instruments whose individual TSETMC instrument endpoint still returned valid details. In earlier tests, SHPNA and FGOSTAR were examples of a halted state (`IS`).
- Bulk retail/institutional participation (ClientType) coverage varied between executions; successful HTTP responses alone do not prove a full, fresh snapshot.
- Errors should not silently zero out previous valid quotes, destroy formulas or falsely describe a halted security as an invalid identifier.

## Approved direction

- **C#/.NET + Excel-DNA/XLL** for an initially Windows desktop Excel add-in; **no VBA/VB** in the new product.
- Excel remains the presentation, workbook, tables and formulas layer; typed C# modules handle domain rules and market-data integration.
- Local-first building/testing/installation for MVP.
- Strong OOP/SOLID/type safety/automated unit-test requirements are mandatory for **every implementation change**, per [ENGINEERING-STANDARDS](ENGINEERING-STANDARDS.md).
- **PO** approves scope, performs local acceptance tests and commits source. **ChatGPT** consults, documents and writes Codex/Astra work packages; it reads source read-only and commits only PO-approved documentation. **Codex/Astra** implements/tests but never commits.

## MVP behavior

1. Load quotes and supplemental data for a confirmed Excel table contract.
2. Resolve instruments using exact `InsCode` and reliable fallback methods for symbols absent from bulk snapshots.
3. Derive or label trading states, queue volumes and retail metrics with clear source/estimate semantics.
4. Report missing/partial/stale/error conditions without destructive writes.
5. Provide a usable Excel refresh interaction and accurate operation summary.

## Out of scope for MVP

Auto-Updater, license/subscription management, hosted backend, commercial data service, production licensing/distribution and Python engine. These may be considered after an MVP acceptance milestone.

## Unresolved decisions — ask PO when material

- .NET and Excel-DNA versions, minimum Excel/Windows version and x86/x64 support.
- Exact initial workbook schema, migration plan, ribbon interaction and local installation mechanism.
- Data-source access limits, legally permissible commercial usage, quote update cadence and freshness criteria.
- Precise product packaging/security model and deployment requirements.

## Privacy and boundaries

This repository is a **software product repository**, not a personal accounting record. It was public when these documents were drafted. Avoid personal positions, brokerage evidence, confidential algorithms and secrets in this repository unless privacy and authorization have been explicitly resolved.
