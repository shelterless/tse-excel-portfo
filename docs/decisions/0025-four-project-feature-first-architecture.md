# D-025 — Four-Project Modular Architecture and Feature-First Organization

- **Status:** Accepted
- **Date accepted:** 2026-10-28

## Context

TSE Excel is expected to grow into a maintainable Excel add-in integrating multiple market-data APIs, portfolio features, and brokerage services.

The PO requires strong OOP/SOLID practices, a predictable folder structure, clear architectural boundaries, and short project names in development tools.

The initial Excel-DNA Ribbon/JSON prototype was implemented in a single `TseExcel.AddIn` project. That prototype is validated, but its current project structure is not the intended long-term architecture.

## Decision

Adopt a four-project modular monolith with dependency boundaries following Clean Architecture principles.

The four production projects are:

1. `Domain`: business models, invariants, financial rules, and domain behavior.
2. `Application`: use cases, workflows, and contracts for external capabilities.
3. `Infrastructure`: implementation of external integrations, persistence, and API adapters.
4. `AddIn`: Excel-DNA, Ribbon, Excel interop, presentation, and application composition.

### Dependency rules

- `Domain` must not reference the other production projects.
- `Application` may reference `Domain`.
- `Infrastructure` may reference `Application` and `Domain`.
- `AddIn` may reference `Application` and `Infrastructure`, with Infrastructure access restricted to composition/bootstrap code.
- Domain and Application must not depend on Excel interop, transport DTOs, broker SDKs, or concrete HTTP clients.
- Concrete integrations implement contracts owned by the appropriate inner layer.

### Naming conventions

Use short physical project names and directories while preserving qualified assembly identities and namespaces.

Examples:

- Directory: `src/Domain/`
- Project: `Domain.csproj`
- Assembly: `TseExcel.Domain`
- C# namespace: `TseExcel.Domain.Trading`

Use explicit C# namespaces where appropriate. Project file names do not dictate public namespace names.

### Feature-first organization

Organize implementation primarily by business capability rather than global class-type folders.

Examples:

- `Application/MarketData/RefreshPrices/`
- `Application/Trading/PlaceOrder/`
- `Domain/Trading/`
- `Infrastructure/MarketData/Tsetmc/`
- `Infrastructure/Brokers/Mofid/`
- `Infrastructure/Storage/Json/`
- `AddIn/Ribbon/`

Create folders and abstractions only when they contain meaningful implementation. Avoid empty future-provider scaffolding, unnecessary factories, and interfaces without a real architectural purpose.

### Testing and implementation

- Maintain automated unit tests for every source change.
- Organize test projects by the production component under test; do not require empty test projects.
- Keep Domain and Application testable without Excel, live APIs, or brokerage accounts.
- Preserve all existing Ribbon and workbook JSON behavior during migration.
- Keep Excel COM access behind the AddIn boundary and on appropriate threads.
- Use a single Excel add-in product; multiple internal C# assemblies do not imply multiple user-facing add-ins.
- Perform the structural migration as a separately approved Codex task, without adding market APIs or trading features.

## Consequences

New features can be added within established layers without creating a new C# project for each API, endpoint, broker, or feature.

The migration requires updating project references, namespaces, file locations, tests, and Excel-DNA packaging. Source changes remain the PO's responsibility to accept and commit.

This decision supersedes the former candidate project layout in `docs/engineering/ARCHITECTURE.md`, not historical ADR records.
