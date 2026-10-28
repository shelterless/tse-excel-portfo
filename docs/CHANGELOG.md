# Context Documentation Changelog

> This file describes **approved documentation changes**, not source-code releases.

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

- Rewrote the root README and ChatGPT context documentation in **English**; PO/ChatGPT conversation remains in Persian.
- Added a mandatory **Operating Contract**, read at the start of every new conversation, plus lazy-loading instructions for task-specific docs.
- Formalized **Product Owner / ChatGPT advisor and documentation steward / Codex-Astra developer** role separation.
- Prohibited ChatGPT source-code modifications and commits; prohibited all Codex/Astra Git commits and pushes. Reserved source acceptance, local tests and commits to the PO.
- Made **PO approval of the finished documentation draft** mandatory before ChatGPT writes/commits documentation to `main`.
- Established mandatory **OOP, SOLID, type safety, justified design patterns and unit tests for every code change**, with code comments/docstrings in English.
- Defined the complete Codex/Astra implementation handoff format, including context links, scope, acceptance criteria, test obligations and no-commit instruction.
- Preserved product boundaries: C#/.NET + Excel-DNA MVP, with Auto-Updater and commercial platform features deferred.

**Approval status:** Approved by the PO on 2026-10-12 for direct documentation commit to `main`.

## 2026-10-12 — Earlier bootstrap

- Initial repository README and `docs/gpt/` context were created in GitHub. They were primarily Persian and did not yet fully enforce the later-confirmed PO/ChatGPT/Codex role boundaries.
