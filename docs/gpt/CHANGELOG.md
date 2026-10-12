# Context Documentation Changelog

> This file describes **approved documentation changes**, not source-code releases.

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
