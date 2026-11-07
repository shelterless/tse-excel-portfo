# Architecture — Approved Four-Project Boundaries and Feature-First Organization

> **Status:** The four-project modular-monolith architecture, feature-first organization, and naming conventions are approved in [D-025](../decisions/0025-four-project-feature-first-architecture.md). Extensible broker integration and Excel-hosted trading are approved direction in [D-026](../decisions/0026-extensible-brokers-excel-hosted-trading.md). The four-project source refactoring was completed and accepted in commit a98a6bd7. The opening-order POC is specifically scoped by [D-028](../decisions/0028-excel-hosted-mofid-opening-order-poc.md).

The validated pre-MVP Ribbon/JSON prototype is part of the existing source baseline. The Mofid and market-data adapters are separate feature work; a folder shown as a target below does not imply that its implementation already exists.

## Approved separation of concerns

```text
Excel Workbook (user data, formulas, tables, dashboards)
                  ↕
AddIn (Excel-DNA, Ribbon, Excel interop, composition, UI)
                  ↓
Application (use cases, workflows, external capability contracts)
                  ↓
Domain (typed business models, invariants and calculations)

Infrastructure (adapters implementing Application contracts):
  MarketData/Tsetmc/   → TSETMC endpoints
  Brokers/Mofid/       → Mofid integration
  Storage/Json/        → File persistence
```

Infrastructure references Application and, where needed, Domain. AddIn references Application and Infrastructure only for composition/bootstrap. Domain is independently unit-testable without Excel, live HTTP or market hours. Excel interop must not contain pricing, financial or order-execution business rules.

## Approved project layout

```text
src/
  Domain/Domain.csproj
  Application/Application.csproj
  Infrastructure/Infrastructure.csproj
  AddIn/AddIn.csproj

tests/
  AddIn.Tests/
  Application.Tests/
  Infrastructure.Tests/

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

The four-project structure was implemented and accepted by the PO. The TSETMC and Mofid folders represent integrations that must be verified and implemented, not assumed existing adapters.

## D-028 Mofid opening-order feature organization

D-028 is the authoritative feature specification. The following is the target organization for that feature, not a claim that these folders or classes already exist. Inspect the current source tree before creating anything, and create only folders that contain real implementation.

```text
src/
  Domain/
    Trading/
      Orders/
        # Pure order concepts, invariants and financial rules

  Application/
    Trading/
      OpeningOrders/
        # Workflow, dispatch orchestration, contracts and progress

  Infrastructure/
    Brokers/
      Mofid/
        Authentication/
        Drafts/
        Orders/
        # Mofid transport, API mapping and session adapters

  AddIn/
    Composition/
    Ribbon/
    ExcelInterop/
    Trading/
      OpeningOrders/
        Forms/
        # Persian Windows Forms workflow
```

### Feature responsibility map

| Concern | Owning project |
|---|---|
| Order-side concepts, order terms and financial rules | Domain |
| Draft-to-order workflow and dispatch orchestration | Application |
| Application-owned broker/session contracts | Application |
| Mofid authentication, session and HTTP transport | Infrastructure |
| Mofid draft, metadata and request mapping | Infrastructure |
| Broker-specific DTOs | Infrastructure |
| Ribbon commands and Persian forms | AddIn |
| UI state and presentation | AddIn |
| Dependency wiring | AddIn composition root |

### Folder and dependency rules

- Keep code feature-first within each existing production project.
- Keep broker-specific DTOs and API details under `Infrastructure/Brokers/Mofid/`.
- Keep application contracts beside the use case that owns them.
- Do not create global `Services/`, `DTOs/`, `Interfaces/` or `Helpers/` buckets.
- Do not create empty future-provider folders or speculative abstractions.
- Do not create a fifth production project for Mofid or opening orders.
- Do not move or refactor the existing WorkbookJson feature as part of D-028.
- Preserve the project-reference matrix above. A change to project boundaries requires PO approval.

## AddIn presentation and dispatch boundaries

The existing AddIn project already enables Windows Forms. D-028 uses that capability; do not introduce WPF or another UI framework without approval.

Forms are responsible for user interaction and presentation only. They must not own broker request construction, financial calculations or the dispatch scheduling loop. Ribbon callbacks open the workflow; they do not perform network requests or run dispatch loops.

The dispatch engine runs independently of the Windows Forms UI thread. It owns scheduling, local attempt counts, timestamps and compact log records. UI updates must be marshalled safely to the UI thread and batched so rendering does not throttle dispatch. Never access Excel COM from a background dispatch worker.

The D-028 log is a fixed-height, vertically scrollable view with one compact line per locally initiated attempt. Do not create a card, bordered container or UI control per attempt. The attempt count is not a broker acceptance or execution count.

Use a monotonic clock for elapsed timing and dispatch intervals; use local system time for the requested wall-clock start time. Windows scheduling and network latency do not guarantee microsecond delivery or queue priority.

## Test organization

Use the existing test projects and mirror the production feature boundaries:

```text
tests/
  AddIn.Tests/
    Trading/
      OpeningOrders/

  Application.Tests/
    Trading/
      OpeningOrders/

  Infrastructure.Tests/
    Brokers/
      Mofid/
```

These are target feature locations, not a requirement to create empty directories. Do not create an empty test project. Keep financial calculations and dispatch orchestration testable without Excel, live APIs or brokerage accounts. Use deterministic fakes and sanitized fixtures; automated tests must never send real orders.

## Composition

`AddInComposition` remains the composition root. Construct application workflows there and inject their Infrastructure implementations. Do not instantiate concrete Mofid API clients directly from forms or Ribbon callbacks.

## Mandatory design properties

- Type-safe, idiomatic C#; OOP and SOLID, dependency inversion and explicit business models. Use design patterns when justified, not automatically. See [ENGINEERING-STANDARDS](ENGINEERING-STANDARDS.md).
- Separate fetch, parse, validate, reconcile and workbook-write responsibilities. A workflow must know when data is insufficient or contradictory before mutating sheets.
- Use exact textual `InsCode` as identity; never convert it through floating-point Excel numbers.
- Strongly distinguish valid zero from missing, unknown, failed, stale or partial data.
- Prevent UI freezes through appropriate asynchronous/network design while honoring Excel/COM thread affinity.
- Preserve formulas, manual cells and user-specific workbook contents. Schema migrations require PO approval and recoverability.
- Unit tests for every source change; contract/integration tests at external boundaries; local Excel acceptance checks by the PO.
- All engineering documents, source comments and docstrings are in English. D-028 user-facing UI is Persian.

## Open architectural choices

Framework and Excel-DNA compatibility, Office bitness/minimum version, packaging and trust model, HTTP strategy, caching, workbook-version compatibility and deployment remain open where not fixed by existing source or accepted decisions. Present material options and trade-offs to the PO rather than silently selecting them.

## Delivery responsibility

ChatGPT proposes architecture and reads source read-only. Codex implements and tests without committing. The PO validates locally and personally commits source. ChatGPT may commit only PO-approved documentation.
