# Architecture — Approved Four-Project Boundaries and Deferred Integrations

> **Status:** The four-project modular-monolith architecture, feature-first organization, and naming conventions are approved in [D-025](../decisions/0025-four-project-feature-first-architecture.md). Extensible broker integration and Excel-hosted trading are approved as deferred direction in [D-026](../decisions/0026-extensible-brokers-excel-hosted-trading.md). The source refactoring, detailed external API contracts, supported platforms and deployment format are not implemented or finalized by these decisions.

The validated pre-MVP proof of concept currently implements Excel Ribbon interaction and workbook-adjacent JSON creation/read/display. Market-data and broker integrations remain separate future tasks.

## Approved separation of concerns

```text
Excel Workbook (user data, formulas, tables, dashboards)
                  ↕
AddIn (Excel-DNA, Ribbon, Excel interop, composition)
                  ↓
Application (use cases, workflows, external capability contracts)
                  ↓
Domain (typed identifiers, market/trading models, rules, calculations)

Infrastructure (adapters implementing Application contracts):
  MarketData/Tsetmc/   → TSETMC endpoints
  Brokers/Mofid/       → Mofid API (future integration)
  Storage/Json/        → File persistence
```

Infrastructure references Application and, where needed, Domain; AddIn references Infrastructure only for application composition. The Domain layer must be independently unit-testable without Excel, live HTTP or market hours. Excel interop must not contain pricing, financial or order-execution business rules.

## Approved target repository layout — migration pending

```text
src/
  Domain/Domain.csproj
  Application/Application.csproj
  Infrastructure/Infrastructure.csproj
    MarketData/Tsetmc/
    Brokers/Mofid/
    Storage/Json/
  AddIn/AddIn.csproj
tests/
  [matching test projects as needed]
workbook/             # Only approved sanitized templates

docs/                 # Canonical documentation, routed through docs/README.md
```

The physical project names and folders are short; assembly names and namespaces retain the `TseExcel.` prefix (for example, `Domain.csproj`, `TseExcel.Domain`, and `TseExcel.Domain.Trading`). Organize code by feature rather than global `Services/`, `DTOs/`, or `Interfaces/` buckets. Create folders and abstractions when needed, not as empty future-provider scaffolding.

| Project | Permitted production project references |
|---|---|
| `Domain` | None |
| `Application` | `Domain` |
| `Infrastructure` | `Application` and, when needed, `Domain` |
| `AddIn` | `Application`, plus `Infrastructure` for composition/bootstrap only |

The existing implementation still uses `src/TseExcel.AddIn/` and its tests. The four-project structure is **approved but not yet implemented**; Codex must inspect the current repository and preserve tested Ribbon/JSON behavior during a separate PO-approved migration. The TSETMC and Mofid folders represent future integrations, not already-implemented adapters.

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

ChatGPT proposes architecture and reads source **read-only**. Codex implements and tests, **without committing**. The PO validates locally and personally commits source. ChatGPT may commit **approved documentation only**.
