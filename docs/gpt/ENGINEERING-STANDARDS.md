# Engineering Standards — Required for All Implementation Work

> Normative engineering requirements for source code prepared by Codex/Astra and evaluated by ChatGPT. Read together with [OPERATING-CONTRACT.md](OPERATING-CONTRACT.md) before defining or reviewing code changes.

## Design principles

- **C#/.NET**, strict static typing, appropriately encapsulated object-oriented design, **SOLID** (SRP, OCP, LSP, ISP, DIP), high cohesion and low coupling.
- Use clean boundaries between domain rules, external data access, orchestration and Excel interop; **depend on abstractions**, inject external dependencies, and test domain logic without Excel or live TSETMC connectivity.
- Apply proven **design patterns only where appropriate** (e.g., Adapter for TSETMC, Strategy for alternative policies, Factory where construction is complex). Avoid unnecessary interfaces, over-generalization and speculative frameworks.
- Prefer immutable domain/value objects, explicit result/status models, named units and strongly typed identifiers (`InsCode`, dates, money) instead of opaque strings or untyped dictionaries in domain logic.
- Follow idiomatic, consistent C# naming and public contracts; enable nullable reference type checking. Use analyzers and treat relevant warnings as actionable; exact toolset/settings require solution-level decisions.
- Avoid `dynamic`, pervasive reflection, magic numbers/strings, broad catch-and-ignore blocks, implicit unit conversions and silent default values that mask failures.
- Keep methods focused, effects explicit, ownership clear, and error handling observable. Fail closed when integrity could be compromised.

## Type and data safety

- `InsCode` must never be round-tripped through floating-point representations; preserve exact digit strings.
- Model financial quantities with explicit units (IRR vs IRT, price vs value, estimated vs executed). Use numeric types appropriate to the required precision and overflow range.
- Treat `null`, missing, zero, unavailable, stale, halted and unknown as distinguishable concepts.
- Validate API response shapes, allowed values, IDs and timestamps before committing changes to the workbook.
- Use asynchronous I/O and cancellation where supported; dispose resources correctly. Respect Excel-DNA and Excel COM/threading constraints when accessing the workbook.
- Never overwrite user-input columns or formulas; plan atomic/batched writes and safe failure behavior. Schema migration must be independently reviewed and approved.
- Never log or commit private brokerage data, credentials or other sensitive user content.

## Test requirements

**Every change, no matter how small, must include or update relevant automated unit tests.** If a change is not meaningfully unit-testable, the work package must explicitly explain why and provide the closest automated verification at the right boundary; this is an exception to justify, not an excuse to skip testing.

- Unit tests must be fast, deterministic, isolated and runnable without Excel, market hours or a live TSETMC network.
- Use test doubles or recorded **sanitized** fixtures for HTTP/API interactions and precise assertions for data conversions, status mapping, time handling and failure cases.
- Add integration/contract tests when a change crosses adapters, Excel interop, persistence, or external API boundaries. Tests requiring installed Excel should be clearly identified as local/manual or environment-dependent.
- Test success **and** negative/edge cases: halted instruments missing from MarketWatch, unknown status codes, missing ClientType, partial snapshots, malformed JSON, timeout/HTTP failures, mismatched InsCode, very long IDs, number/locale differences, stale queues, formula preservation and recoverability.
- No arbitrary percentage coverage promise without agreed tooling; demand meaningful branch/behavior coverage and document untested risks. Fix or disclose failures before requesting user acceptance.
- Tests and build commands must be specified in every Codex/Astra handoff. Codex must report exact commands/results and must not fabricate green builds.

## Code review and maintainability

- Preserve the existing architecture unless the user approves a deviation.
- Document public APIs and non-obvious decisions with **English XML documentation/comments**; avoid comments that merely restate code.
- Keep PR-sized changes coherent and free of unrelated refactoring. Prefer readable, maintainable solutions over cleverness.
- Require useful diagnostics with no sensitive payloads, explicit quality/freshness metadata and user-safe error reporting.
- Identify compatibility assumptions before implementation: target framework, Office bitness, Excel-DNA version, deployment method and trusted add-in constraints remain open until approved.

## Acceptance gate

A work package is complete only when its specified functionality, tests, build checks, documentation implications, manual Excel verification instructions and known limitations are reported. **Codex/Astra never commits; the user tests locally and commits source. ChatGPT never changes source.**
