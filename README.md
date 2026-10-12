# TSE Excel Portfolio

A planned **C#/.NET + Excel-DNA** add-in for Microsoft Excel for retrieving, validating and presenting Iranian capital-market data. The initial focus is securities, trading status, order queues, and retail/institutional activity.

> **Status:** Project definition and documentation. A working C# solution, XLL package, installer, or automated test suite is not yet confirmed. The former Excel/VBA workbook is a behavioral reference, not the planned implementation.

## MVP direction

- Windows desktop Excel is the initial target; exact Office and .NET compatibility requirements remain open.
- Excel owns the workbook, user-entered data, formulas and dashboards. Compiled C# libraries and an Excel-DNA XLL handle refresh and processing.
- Preserve exact `InsCode` identifiers, differentiate halted symbols from missing API data, detect stale/partial responses and avoid destructive updates.
- Initial releases are built and installed locally. No new VBA/VB, Auto-Updater, hosted backend, license service, commercial subscription platform or Python runtime in MVP.

## Roles and delivery

The **user is the Product Owner (PO)**, owns all approvals, runs local acceptance tests and is the **only person committing/pushing source code**. **ChatGPT** is the advisor, requirements analyst and documentation steward; it reads source **read-only**, prepares complete Codex/Astra work packages, and may commit **documentation only after PO approval of the finished draft**. **Codex/Astra** implements/tests source but never commits or pushes.

The PO and ChatGPT converse **in Persian**. **All documentation, source comments, docstrings and engineering briefs are in English** unless the PO explicitly requests a different language for an artifact.

## ChatGPT context documents

| Document | Purpose |
|---|---|
| [PROJECT-INSTRUCTIONS](docs/gpt/PROJECT-INSTRUCTIONS.md) | Minimal ChatGPT Project bootstrap |
| [OPERATING-CONTRACT](docs/gpt/OPERATING-CONTRACT.md) | **Mandatory first read for every conversation** |
| [Context Index](docs/gpt/README.md) | Task-based lazy-loading map |
| [PROJECT-CONTEXT](docs/gpt/PROJECT-CONTEXT.md) | Product goal, MVP, excluded phases |
| [ENGINEERING-STANDARDS](docs/gpt/ENGINEERING-STANDARDS.md) | OOP, SOLID, type safety, mandatory unit tests |
| [CODEX-HANDOFF](docs/gpt/CODEX-HANDOFF.md) | Complete Codex/Astra implementation prompt contract |
| [DEVELOPMENT-WORKFLOW](docs/gpt/DEVELOPMENT-WORKFLOW.md) | PO-led implementation and local acceptance lifecycle |
| [ARCHITECTURE](docs/gpt/ARCHITECTURE.md) | Approved direction and proposed boundaries |
| [WORKBOOK-CONTRACT](docs/gpt/WORKBOOK-CONTRACT.md) | Observed legacy workbook schema and formulas |
| [DATA-RELIABILITY](docs/gpt/DATA-RELIABILITY.md) | TSETMC validity, status and failure policy |
| [GOVERNANCE](docs/gpt/GOVERNANCE.md) | Documentation approval, access controls and sync |
| [DECISIONS](docs/gpt/DECISIONS.md) | Approved decisions versus open questions |
| [CHANGELOG](docs/gpt/CHANGELOG.md) | Context documentation changes |

## ChatGPT Project setup

Suggested project name: **Mohsen-Portfo-TSE-Excel**. Paste only [PROJECT-INSTRUCTIONS.md](docs/gpt/PROJECT-INSTRUCTIONS.md) into **Project Instructions**; add the remaining `docs/gpt/*.md` documents to **Project Sources**. At the beginning of every new conversation, read the current [OPERATING-CONTRACT.md](docs/gpt/OPERATING-CONTRACT.md), then the index; load other docs only as needed. Project Sources are **not automatically synchronized** with GitHub: replace changed copies after an approved documentation commit. Re-paste Project Instructions **only if** its bootstrap file changed.

## Safety

This repository was **public** when these documents were prepared. Do not publish personal holdings, brokerage exports, secrets, customer data or confidential commercial algorithms. The canonical branch is [`main`](https://github.com/shelterless/tse-excel-portfo/tree/main). Source commits belong exclusively to the PO after local testing; ChatGPT documentation commits require prior PO approval.
