# Codex / Astra Work Package Contract

ChatGPT prepares a complete, professional implementation prompt **after discussing and confirming the task with the user**. Codex/Astra is the implementation agent; this document standardizes the handoff without authorizing code changes by ChatGPT.

## Mandatory prompt sections

1. **Objective and business context:** what problem is being solved and why.
2. **Repository and baseline:** `shelterless/tse-excel-portfo`, `main`, current verified paths/commit when available; do not invent paths or claim a working build without evidence.
3. **Authoritative references:** direct links to current relevant `docs/gpt/` Markdown files, **always** [OPERATING-CONTRACT.md](OPERATING-CONTRACT.md) and [ENGINEERING-STANDARDS.md](ENGINEERING-STANDARDS.md), plus the applicable architecture, workbook, data reliability, and workflow contracts.
4. **In scope / out of scope:** narrow, independently demonstrable deliverable; deferred features stay excluded.
5. **Existing behavior / constraints:** exact API and workbook data contracts, financial units, threading, compatibility requirements and any verified baseline.
6. **Design requirements:** object-oriented design, SOLID, type-safe domain models, testable dependency boundaries and justified patterns (not forced patterns), code and comments/docstrings **in English**.
7. **Implementation instructions:** concrete intended outcomes and touched areas, but allow maintainable choices within approved architecture; no undocumented assumptions.
8. **Test plan:** automated unit tests for every code change, contract/integration tests as appropriate, failure cases and deterministic fixtures; specify runnable commands when known.
9. **Acceptance criteria:** objectively verifiable user-visible behavior, data-integrity invariants, error cases, exact expected outputs or invariants, and a local Excel validation checklist.
10. **Delivery report:** files changed, important design decisions, commands and results, tests not run and why, remaining risks and any decision needed from the user.
11. **Hard Git and role restrictions:** Codex/Astra **MUST NOT** commit, push, tag, create/merge PRs, or publish releases. Leave changes uncommitted; user alone validates and commits source. ChatGPT only reads source and may commit user-approved documentation changes.

## How to handle ambiguity

- Ask the user before writing a work package when a material decision is missing; do not fill gaps with invented assumptions.
- If Codex/Astra discovers a material conflict or unapproved schema/architecture change, **stop and report it for user clarification** instead of silently deciding.
- Never assert Build, tests, or Excel integration passed unless executed with actual results.
- Do not instruct Codex/Astra to modify `docs/gpt` as a workaround for missing requirements; ask ChatGPT/user to handle approved documentation changes separately.

## Suggested short prompt outline (adapt per task)

~~~text
Task:
Repository/main baseline:
Read first (URLs):
Confirmed requirements:
Scope / exclusions:
Contracts and safety invariants:
Design constraints (OOP, SOLID, type safety, justified patterns):
Implementation outcomes:
Automated tests and commands:
Manual Excel acceptance checks:
Acceptance criteria:
Expected delivery report:
Git restriction: NO git commit / push / PR / tag / publish. User commits after local tests.
~~~

ChatGPT should prepare a **complete handoff**, not a long series of fragmented manual experiments.
