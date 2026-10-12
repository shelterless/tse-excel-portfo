# Architecture — Approved Direction and Proposed Boundaries

> **Status:** The C#/.NET + Excel-DNA direction is approved. The detailed project layout, interfaces, dependencies, supported platforms and deployment format remain **proposals**, not implemented facts.

## Intended separation of concerns

```text
Excel Workbook (user data, formulas, tables, dashboards)
                  ↕
Excel-DNA XLL / Ribbon / Excel interop adapter (C#)
                  ↕
Application orchestration (refresh workflow, results, diagnostics)
                  ↕
Domain/core (typed instrument IDs, quotes, states, validation, calculations)
                  ↕
TSETMC adapter (HTTP, parsing, DTO translation, quality metadata)
                  ↕
TSETMC endpoints
```

The domain/core layer must be independently unit-testable without Excel, live HTTP or market hours. Excel interop should not contain pricing or financial business rules.

## Candidate repository layout — not yet created

```text
src/
  TseExcel.Core/
  TseExcel.Tsetmc/
  TseExcel.AddIn/
tests/
  TseExcel.Core.Tests/
  TseExcel.Tsetmc.Tests/
workbook/             # Only approved sanitized templates

docs/gpt/             # ChatGPT context and working contracts
```

Do **not** assume these directories or any `.csproj` already exist. Codex/Astra should inspect the actual current repository before implementing.

## Mandatory design properties

- **Type-safe, idiomatic C#; OOP and SOLID**, with dependency inversion and explicit business models. Use design patterns when justified, not automatically. See [ENGINEERING-STANDARDS](ENGINEERING-STANDARDS.md).
- Separate Fetch → Parse → Validate → Reconcile → Write-to-Workbook. The workflow should know when data is insufficient or contradictory **before** mutating sheets.
- Use exact text `InsCode` as identity; never convert through floating-point Excel numbers.
- Strongly distinguish valid `0` from missing/unknown/failed/stale. Keep provenance and timestamps where available.
- Prevent UI freezes via appropriate async/network design, while honoring Excel/COM thread affinity for spreadsheet access.
- Preserve formulas, manual cells and user-specific workbook contents. Schema migrations need PO approval and recoverability.
- Unit tests for every change; contract/integration tests at external boundaries; local Excel acceptance checks by the PO.
- All engineering documents, source comments and docstrings must be in English.

## Open architectural choices

Framework and Excel-DNA versions; Office bitness/minimum version; packaging and trust model; HTTP strategy and caching; workbook-version compatibility; refresh UI and error-reporting design. Present options and trade-offs to the PO rather than silently selecting them.

## Delivery responsibility

ChatGPT proposes architecture and reads source **read-only**. Codex/Astra implements and tests, **without committing**. The PO validates locally and personally commits source. ChatGPT may commit **approved documentation only**.
