# ChatGPT Context Index — Lazy Loading

The source of truth is `shelterless/tse-excel-portfo`, branch `main`. Copied ChatGPT Project Sources may be stale.

## Mandatory start of EVERY conversation

1. Read **[OPERATING-CONTRACT.md](OPERATING-CONTRACT.md)** from current `main`. This is mandatory, **not** subject to lazy loading.
2. Read this index.
3. Read **only** other documents needed for the task. Never bulk-load context without a reason.

If live GitHub access is unavailable, say so instead of claiming access. Resolve material contradictions with the PO before making a decision.

## Task-based loading

| Topic | Load only these additional documents |
|---|---|
| Product goals and MVP | [PROJECT-CONTEXT.md](PROJECT-CONTEXT.md) |
| Architectural decisions | [PROJECT-CONTEXT.md](PROJECT-CONTEXT.md), [ARCHITECTURE.md](ARCHITECTURE.md), relevant [DECISIONS.md](DECISIONS.md) |
| **Any coding task or code review** | **[ENGINEERING-STANDARDS.md](ENGINEERING-STANDARDS.md)** plus relevant contracts |
| **Codex/Astra implementation prompt** | **[ENGINEERING-STANDARDS.md](ENGINEERING-STANDARDS.md)**, **[CODEX-HANDOFF.md](CODEX-HANDOFF.md)**, [DEVELOPMENT-WORKFLOW.md](DEVELOPMENT-WORKFLOW.md) plus relevant technical contracts |
| Workbook fields, formulas, migration | [WORKBOOK-CONTRACT.md](WORKBOOK-CONTRACT.md) |
| TSETMC, status, data quality, errors | [DATA-RELIABILITY.md](DATA-RELIABILITY.md), relevant workbook contract |
| Documentation, Git, access and context sync | [GOVERNANCE.md](GOVERNANCE.md), target document |
| Decision records | [DECISIONS.md](DECISIONS.md); [CHANGELOG.md](CHANGELOG.md) when needed |

## Evidence precedence

Explicit newer PO statements > verified current `main` > observed build/test evidence > copied Project Sources > historical discussion. Explain unresolved contradictions; do not fill unknowns with assumptions.

All documents and work packages are **English** unless explicitly directed otherwise; PO/ChatGPT discussion is **Persian**. ChatGPT has **read-only source access**, may commit **PO-approved documentation only**, and must not touch source. Codex/Astra writes and tests code **without committing**; PO alone accepts and commits source after local testing.

Report actual documentation commits and which Project Sources must be replaced. Only changes to [PROJECT-INSTRUCTIONS.md](PROJECT-INSTRUCTIONS.md) require updating the ChatGPT Project Instructions field.
