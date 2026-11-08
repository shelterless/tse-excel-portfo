# Context Documentation Changelog

## 2026-11-08 — Native HTTP opening-order reference and Excel port

- Recorded D-030 as the PO-approved technical direction for porting the newer native-HTTP Mofid opening-order POC into the existing Excel-DNA add-in.
- Designated `POC/easytrader_direct_http_poc.py` and its companion offline tests as frozen, read-only reference assets after PR #4 merge; the older Python reference remains unchanged and read-only.
- Required manual browser authentication only, verified browser teardown, and native .NET HTTP for all subsequent Mofid reads and order POSTs.
- Specified the 300 ms live minimum, 350 ms default, bounded non-response-driven dispatch, TCP/TLS warmup followed by final preflight, and no extra artificial delay or catch-up bursts.
- Required always-on, sanitized, workbook-adjacent per-run trace logs for the Excel phase; a future JSON-configured logging toggle is deferred.
- Preserved the existing Persian forms and D-028 order/financial safeguards. Real broker acceptance and queue position remain PO-owned live-market acceptance; the supplied nine rejected responses do not establish acceptance.
- Documentation only; no source, test, workbook, or runtime files were changed by this documentation commit.

> This file describes approved documentation changes, not source-code releases.

## 2026-11-07 — Feature-branch delivery governance

- Accepted D-029 to make approved source changes reviewable on dedicated feature branches before merge.
- Clarified Codex's branch-only commits/pushes, ChatGPT's read-only source review and strictly PO-authorized merge boundary, and the PO's post-merge local/Excel acceptance.
- Updated the operating contract, governance, development workflow, Codex handoff, documentation index and ChatGPT bootstrap consistently. No source or test files were changed by the documentation revision.

## 2026-11-07 — Excel-hosted Mofid opening-order POC

- Accepted D-028 as the authoritative bounded scope for the Excel-hosted Mofid opening-order proof of concept.
- Recorded the strict read-only boundary for `POC/easytrader_poc.py`: inspection only; no modification, formatting, execution, import, invocation or runtime dependency.
- Specified the six-stage Persian Windows Forms workflow, session handling, draft immutability, order calculations, local dispatch timing, explicit confirmation and completion behavior.
- Defined the fixed-height, vertically scrollable, one-line-per-attempt dispatch log and separated local dispatch attempts from broker acceptance/execution.
- Clarified D-027's partial supersession without removing its API uncertainty, authentication, credential-protection or broker-authorization caveats.
- Added the deferred trading backlog and documented feature-first folders, project ownership, dependency boundaries, testing and Codex handoff requirements.
- No source files, Python files, tests or runtime assets were changed.

## 2026-11-03 — EasyTrader web API strategy and local trading experiment

- Accepted D-027: investigate the private web APIs behind EasyTrader, starting with the desktop client, for future Mofid integration without assuming officially published API access.
- Prioritized a minimal local C# Console proof of concept for legitimate authentication, one preauthorized limited real order, reconciliation and timing measurements before Excel trading integration.
- Preserved D-025/D-026 architecture and execution safeguards; API details, permissions and production security remain unverified or deferred.
- Updated the decision index and open-questions summary without rewriting earlier decisions.

## 2026-10-28 — Architecture and future trading decisions

- Accepted D-025: four-project modular monolith, feature-first organization, dependency boundaries, short physical project names and `TseExcel.`-qualified assemblies/namespaces.
- Accepted D-026 as deferred implementation direction: Mofid-first broker extensibility, manually confirmed orders, and future preapproved automated orders only while Excel and the add-in are active.
- Aligned the architecture proposal and open-questions index with these decisions; source refactoring and trading/API integrations remain separate future work.

## 2026-10-27 — Approved documentation layout migration

- Moved canonical project, engineering, contract and governance documents out of `docs/gpt/` into topic folders without discretionary rewriting.
- Split D-001 through D-021 into independent ADR files, retaining all original statements/statuses and a verbatim historical log plus open questions and evidence.
- Adopted the minimal bootstrap and lazy-loading rules through D-022, documenting supersession of D-013 and D-014.
- Recorded GUI-first local development and deferred automatic release/update goals through D-023 and D-024.
- Repaired documentation links and revised ChatGPT Project synchronization guidance.

## 2026-10-27 — PO-approved prototype scope and tool clarification

- Recorded a deliberately minimal Excel-DNA pre-MVP prototype: Ribbon commands to create a workbook-adjacent JSON file and show its contents, without locking or market APIs.
- Preserved the existing market-data MVP, and deferred advanced configuration editing, locking, workbook generation and commercial infrastructure.
- Clarified that Codex is the implementation tool; the underlying model is not fixed by project documentation.
- Clarified ChatGPT's responsibility to apply and commit PO-approved documentation changes directly to `main`, without requiring the PO to apply patches; source commits remain PO-only.
- Recorded one-step-at-a-time local setup and the actual ChatGPT Project name, `Mohsen-TSE-Excel`.
- Retained historical changelog entries unchanged.

## 2026-10-12 — PO-approved documentation revision

- Rewrote the root README and ChatGPT context documentation in English; PO/ChatGPT conversation remains in Persian.
- Added a mandatory Operating Contract, read at the start of every new conversation, plus lazy-loading instructions for task-specific docs.
- Formalized Product Owner / ChatGPT advisor and documentation steward / Codex-Astra developer role separation.
- Prohibited ChatGPT source-code modifications and commits; prohibited all Codex/Astra Git commits and pushes. Reserved source acceptance, local tests and commits to the PO.
- Made PO approval of the finished documentation draft mandatory before ChatGPT writes/commits documentation to `main`.
- Established mandatory OOP, SOLID, type safety, justified design patterns and unit tests for every code change, with code comments/docstrings in English.
- Defined the complete Codex/Astra implementation handoff format, including context links, scope, acceptance criteria, test obligations and no-commit instruction.
- Preserved product boundaries: C#/.NET + Excel-DNA MVP, with Auto-Updater and commercial platform features deferred.

## 2026-10-12 — Earlier bootstrap

- Initial repository README and `docs/gpt/` context were created in GitHub. They were primarily Persian and did not yet fully enforce the later-confirmed PO/ChatGPT/Codex role boundaries.
