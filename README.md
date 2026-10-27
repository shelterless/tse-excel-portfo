# TSE Excel Portfolio

A planned **C#/.NET + Excel-DNA** add-in for Microsoft Excel for retrieving, validating and presenting Iranian capital-market data. The initial focus is securities, trading status, order queues, and retail/institutional activity.

> **Status:** Project definition and documentation. A working C# solution, XLL package, installer, or automated test suite is not yet confirmed. The former Excel/VBA workbook is a behavioral reference, not the planned implementation.

## MVP direction

- Before the market-data MVP, validate a minimal Excel Ribbon prototype that creates a JSON file beside its workbook and displays that JSON in a message dialog. Locking and API integrations are deferred.
- Windows desktop Excel is the initial target; exact Office and .NET compatibility requirements remain open.
- Excel owns the workbook, user-entered data, formulas and dashboards. Compiled C# libraries and an Excel-DNA XLL handle refresh and processing.
- Preserve exact `InsCode` identifiers, differentiate halted symbols from missing API data, detect stale/partial responses and avoid destructive updates.
- Initial releases are built and installed locally. No new VBA/VB, Auto-Updater, hosted backend, license service, commercial subscription platform or Python runtime in MVP.

## Roles and delivery

The **user is the Product Owner (PO)**, owns all approvals, runs local acceptance tests and is the **only person committing/pushing source code**. **ChatGPT** is the advisor, requirements analyst and documentation steward; it reads source **read-only**, prepares complete Codex work packages, and may commit **documentation only after PO approval of the finished draft**. **Codex** implements/tests source but never commits or pushes.

The PO and ChatGPT converse **in Persian**. **All documentation, source comments, docstrings and engineering briefs are in English** unless the PO explicitly requests a different language for an artifact.

## Documentation

Start at the [Documentation Map](docs/README.md); open only relevant topic documents.

| Area | Current document |
|---|---|
| ChatGPT bootstrap | [PROJECT-INSTRUCTIONS](docs/gpt/PROJECT-INSTRUCTIONS.md) |
| Project context and workflow | [Project context](docs/project/PROJECT-CONTEXT.md) |
| Architecture and quality | [Engineering standards](docs/engineering/ENGINEERING-STANDARDS.md) |
| Workbook and market-data contracts | [Workbook contract](docs/contracts/WORKBOOK-CONTRACT.md) |
| Accepted decisions and open questions | [Decision index](docs/decisions/README.md) |
| Revision history | [CHANGELOG](docs/CHANGELOG.md) |

## ChatGPT Project setup

Current ChatGPT Project name: **Mohsen-TSE-Excel**. Paste [PROJECT-INSTRUCTIONS.md](docs/gpt/PROJECT-INSTRUCTIONS.md) into ChatGPT Project Instructions. The canonical documentation map is [docs/README.md](docs/README.md). Load detailed documents and accepted decisions from GitHub `main` only as relevant. Do not upload the whole `docs/` folder to Project Sources. If GitHub is unavailable, disclose the limitation rather than assuming cached documents are current. Re-paste Project Instructions only when that canonical bootstrap changes.

## Safety

This repository was **public** when these documents were prepared. Do not publish personal holdings, brokerage exports, secrets, customer data or confidential commercial algorithms. The canonical branch is [`main`](https://github.com/shelterless/tse-excel-portfo/tree/main). Source commits belong exclusively to the PO after local testing; ChatGPT documentation commits require prior PO approval.
