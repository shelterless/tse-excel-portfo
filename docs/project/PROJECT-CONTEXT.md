# Product Context — TSE Excel Portfolio

## Product purpose

Build a maintainable Excel add-in to retrieve, validate, analyze and present Iranian securities-market data. The first market-data use case comes from an Excel market-watch/portfolio workbook and includes prices, price limits, buy/sell queues, retail participant counts, estimated retail flow and trading-state diagnostics. The potential to expand to all listed symbols and commercial analytics is a future possibility, not an approved first-phase deliverable.

The GitHub repository is `shelterless/tse-excel-portfo`; the current ChatGPT Project name is `Mohsen-TSE-Excel`.

## Background observations

- A prior personal Excel/VBA prototype was developed and tested. It provides a behavioral reference, not proof of the new add-in's implementation.
- The bulk MarketWatch endpoint omitted some instruments whose individual TSETMC instrument endpoint still returned valid details. In earlier tests, SHPNA and FGOSTAR were examples of a halted state (`IS`).
- Bulk retail/institutional participation (ClientType) coverage varied between executions; successful HTTP responses alone do not prove a full, fresh snapshot.
- Errors should not silently zero out previous valid quotes, destroy formulas or falsely describe a halted security as an invalid identifier.

## Approved product and technical direction

- **C#/.NET + Excel-DNA/XLL** for an initially Windows desktop Excel add-in; no VBA/VB in the new product.
- Excel remains the presentation, workbook, tables and formulas layer; typed C# modules handle domain rules and external integrations.
- Local-first building, testing and installation for the initial product.
- Strong OOP/SOLID/type safety and automated unit tests are mandatory for every implementation change, per [ENGINEERING-STANDARDS](../engineering/ENGINEERING-STANDARDS.md).
- **PO** approves scope, performs local acceptance tests and commits source. **ChatGPT** advises, reads source read-only, prepares handoffs and commits only PO-approved documentation. **Codex** implements/tests but never commits.

## Existing pre-MVP Ribbon/JSON prototype

The initial Excel-DNA Ribbon/JSON prototype is part of the current source baseline. Preserve its behavior while implementing later features:

- A saved workbook has a corresponding business-configuration JSON file beside it, with the same basename.
- A Ribbon command can explicitly create a minimal JSON file when absent, without overwriting an existing file.
- A separate test Ribbon command reads the corresponding JSON and displays its contents.
- Unrelated workbooks remain unaffected; the add-in must not automatically create configuration files for them.
- Locking, JSON edits through the add-in, concurrent-workbook coordination, market API calls, automatic worksheet creation, licensing and commercial packaging were outside that prototype's scope.

The JSON schema, file-locking implementation, Save As behavior and concurrent-workbook policy remain open for later design and PO approval. Do not refactor this feature as part of D-028.

## Next approved implementation milestone — Mofid opening-order POC

[D-028](../decisions/0028-excel-hosted-mofid-opening-order-poc.md) authorizes a bounded, local, Excel-hosted Mofid opening-order proof of concept using the existing four-project architecture and Persian Windows Forms UI.

The frozen Python reference at `POC/easytrader_poc.py` may be inspected as a behavioral reference only. It is strictly read-only: do not modify, format, move, delete, execute, import, invoke or use it as a runtime dependency. The C# implementation must be independent.

D-028 defines the six-stage workflow: draft selection, order details, dispatch timing, explicit confirmation, bounded dispatch with a compact scrollable log, and completion. The dispatch log has fixed dimensions, one compact line per locally initiated attempt, and vertical scrolling. Its counter reports local dispatch attempts, not broker-accepted or executed orders.

D-028 does not authorize a production trading platform, broker-response reconciliation, unattended execution outside the active Excel/add-in session, live SELL dispatch before separate verification/approval, or the deferred items in [PRODUCT-BACKLOG](PRODUCT-BACKLOG.md). The private Mofid API contract and permitted third-party usage remain subject to verification; this decision does not assert broker authorization.

The opening-order POC is separate from the market-data MVP described below.

## Market-data MVP behavior

1. Load quotes and supplemental data for a confirmed Excel table contract.
2. Resolve instruments using exact `InsCode` and reliable fallback methods for symbols absent from bulk snapshots.
3. Derive or label trading states, queue volumes and retail metrics with clear source/estimate semantics.
4. Report missing, partial, stale and error conditions without destructive writes.
5. Provide a usable Excel refresh interaction and accurate operation summary.

## Out of scope for the current milestones

Auto-Updater, license/subscription management, hosted backend, commercial data service, production licensing/distribution and a Python production engine. These may be considered after the relevant MVP acceptance milestones. The frozen Python POC is a read-only reference, not a production engine.

### Deferred commercial distribution and updates

A later phase may provide automated CI/CD, signed add-in release packaging, notifications when a new version is available, and a safe user-initiated one-click update experience. Installer privileges, Excel/XLL file locks, possible Excel restart requirements, compatibility, rollback, trust and signing must be assessed before choosing an updater design. No release or updater infrastructure is authorized by this statement.

## Unresolved decisions — ask PO when material

- Minimum supported Excel and Windows versions, Office bitness and exact .NET/Excel-DNA compatibility requirements.
- Exact market-data workbook schema and migration plan.
- TSETMC freshness, ClientType publication timing, bulk coverage thresholds, rate limits and commercial-use rights.
- Verified Mofid authentication, draft, instrument-metadata and order-request contracts; API access permissions and applicable terms.
- Secure session persistence details, broker-response reconciliation, production trading safeguards and deployment model.

## Privacy and boundaries

This repository is a software product repository, not a personal accounting record. It was public when these documents were drafted. Avoid personal positions, brokerage evidence, confidential algorithms, credentials, session tokens and other secrets in this repository unless privacy and authorization have been explicitly resolved.
