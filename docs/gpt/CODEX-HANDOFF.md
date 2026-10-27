# Codex Work-Package Contract

ChatGPT prepares a **complete implementation prompt** only after discussing the change with the Product Owner and obtaining approval for the task scope. Codex is the development tool, with no prescribed underlying model; the PO is the final acceptance authority.

## Required sections of each implementation prompt

1. **Objective and context:** user problem, business outcome and verified existing behavior.
2. **Repository baseline:** `shelterless/tse-excel-portfo`, current `main`, known files and verified commit when available. Do not invent paths or claim a build exists.
3. **Read-first documentation:** always link to [OPERATING-CONTRACT](OPERATING-CONTRACT.md), [ENGINEERING-STANDARDS](ENGINEERING-STANDARDS.md) and this handoff; add only task-relevant [ARCHITECTURE](ARCHITECTURE.md), [WORKBOOK-CONTRACT](WORKBOOK-CONTRACT.md), [DATA-RELIABILITY](DATA-RELIABILITY.md) and [DEVELOPMENT-WORKFLOW](DEVELOPMENT-WORKFLOW.md).
4. **PO-approved scope:** functional requirements, in-scope/out-of-scope decisions, invariants and constraints.
5. **Design and implementation requirements:** clean C#, OOP, SOLID, type safety, nullable reference safety, justified design patterns, dependency boundaries, English comments/docstrings and data integrity.
6. **Behavioral edge cases:** missing/invalid data, halted symbols, HTTP failures, stale values, localization/precision and workbook ownership as relevant.
7. **Tests and verification:** **unit tests for every change**, adapter/contract/integration tests as applicable, reproducible build/test commands and sanitization of fixtures.
8. **Acceptance criteria:** objective conditions, expected output, failure behavior, no-loss invariants, and the PO's local Excel acceptance checklist.
9. **Delivery report:** changed files, architecture choices, exact commands and observed results, unrun tests/reasons, risks and pending PO decisions.
10. **Hard Git restrictions:** **Codex MUST NOT commit, push, tag, create/merge PRs or publish releases.** Leave all source changes uncommitted for the PO's local testing and personal commit. Do not edit `docs/gpt` governance without the PO's separate documentation approval process.

## Mandatory escalation

If repository facts, API semantics, schema, financial meanings or dependencies contradict the approved task, stop and request clarification. Never silently invent a solution, claim unrun tests passed or change documentation to reinterpret requirements.

## Suggested prompt skeleton

```text
Objective and confirmed context:
Repository and verified baseline:
Authoritative documentation URLs:
PO-approved scope and explicit exclusions:
Requirements and data contracts:
Design requirements (C#, OOP, SOLID, type safety, patterns where justified):
Implementation deliverables:
Automated unit tests, integration tests, and commands:
PO local Excel acceptance checklist:
Objective acceptance criteria:
Delivery report requirements:
Git: DO NOT COMMIT, PUSH, TAG, CREATE/MERGE PRs, OR RELEASE.
Leave changes uncommitted; PO alone tests/accepts/commits source.
```

Prefer an end-to-end implementable work package to fragmented micro-experiments. Technical tests should be automated by Codex, not repeatedly delegated to the PO unless local Excel is required.
