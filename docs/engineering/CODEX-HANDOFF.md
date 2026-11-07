# Codex Work-Package Contract

ChatGPT prepares a complete implementation prompt only after discussing the change with the Product Owner and obtaining approval for the task scope. Codex is the development tool; no underlying model is prescribed. The PO is the final acceptance authority.

## Required sections of each implementation prompt

1. **Objective and context:** user problem, business outcome and verified existing behavior.
2. **Repository baseline:** `shelterless/tse-excel-portfo`, current `main`, known files and verified commit when available. Do not invent paths or claim a build exists.
3. **Read-first documentation:** always link to [OPERATING-CONTRACT](../project/OPERATING-CONTRACT.md), [ENGINEERING-STANDARDS](ENGINEERING-STANDARDS.md) and this handoff; add only task-relevant [ARCHITECTURE](ARCHITECTURE.md), [WORKBOOK-CONTRACT](../contracts/WORKBOOK-CONTRACT.md), [DATA-RELIABILITY](../contracts/DATA-RELIABILITY.md), [DEVELOPMENT-WORKFLOW](../project/DEVELOPMENT-WORKFLOW.md) and accepted ADRs.
4. **PO-approved scope:** functional requirements, in-scope/out-of-scope decisions, invariants and constraints.
5. **Design and implementation requirements:** clean C#, OOP, SOLID, type safety, nullable-reference safety, justified design patterns, dependency boundaries, English comments/docstrings and data integrity.
6. **Behavioral edge cases:** missing/invalid data, halted symbols, HTTP failures, stale values, localization/precision and workbook ownership as relevant.
7. **Tests and verification:** unit tests for every change, adapter/contract/integration tests as applicable, reproducible build/test commands and sanitized fixtures.
8. **Acceptance criteria:** objective conditions, expected output, failure behavior, no-loss invariants and the PO's local Excel acceptance checklist.
9. **Delivery report:** changed files, design choices, exact commands and observed results, unrun tests/reasons, risks and pending PO decisions.
10. **Hard Git restrictions:** Codex MUST NOT commit, push, tag, create/merge PRs or publish releases. Leave all source changes uncommitted for the PO's local testing and personal commit. Do not independently change approved governance/context documentation.

## Read-only reference assets

When an ADR identifies a file as a read-only reference, Codex may inspect and read it only. The prompt must state explicitly whether execution, importing, copying or other use is prohibited. Do not infer that read-only permission includes permission to run a script. For D-028, `POC/easytrader_poc.py` may be read for behavioral comparison but must not be edited, formatted, moved, deleted, executed, imported, invoked or used as a runtime/build/test dependency. Verify that it remains unchanged before delivery.

## Mandatory escalation

If repository facts, API semantics, schema, financial meanings, reference behavior or dependencies contradict the approved task, stop and request clarification. Never silently invent a solution, claim unrun tests passed or change documentation to reinterpret requirements.

## Suggested prompt skeleton

```text
Objective and confirmed context:
Repository and verified baseline:
Authoritative documentation URLs and ADR:
PO-approved scope and explicit exclusions:
Read-only reference assets and prohibited operations:
Requirements and data contracts:
Design requirements (C#, OOP, SOLID, type safety, justified patterns):
Implementation deliverables:
Automated unit tests, integration tests and commands:
PO local Excel acceptance checklist:
Objective acceptance criteria:
Delivery report requirements:
Git: DO NOT COMMIT, PUSH, TAG, CREATE/MERGE PRs OR RELEASE.
Leave all source changes uncommitted; PO alone tests, accepts and commits source.
```

Prefer an end-to-end implementable work package to fragmented micro-experiments. Technical tests should be automated by Codex, not repeatedly delegated to the PO unless local Excel or live-account acceptance is required.
