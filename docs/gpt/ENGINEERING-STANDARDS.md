# Engineering Standards — Mandatory for Every Code Change

This document is normative for Codex implementation and ChatGPT review. Always read it with [OPERATING-CONTRACT.md](OPERATING-CONTRACT.md) when preparing **any** coding work package, including trivial fixes.

## OOP, SOLID and code architecture

- Use **C#/.NET**, idiomatic conventions, strongly typed interfaces, clear invariants and maintainable object-oriented design.
- Enforce **SOLID**: SRP, OCP, LSP, ISP and DIP; high cohesion, low coupling, appropriate encapsulation and composition over inheritance when sensible.
- Keep business/domain models independent from Excel interop, external HTTP, transport DTOs and UI/Ribbon logic. Depend on abstractions at boundaries; inject dependencies to make core logic testable.
- Apply established **design patterns only when they solve concrete design problems** (e.g. Adapter, Strategy, Factory); do not add unnecessary abstractions, interfaces or patterns for their own sake.
- Favor immutable value objects, explicit statuses/result types, meaningful naming, readable methods and small testable units. Maintain strict nullable-reference annotations and appropriate static-analysis checks; tool/version choices require approval.
- Avoid `dynamic` in domain logic, unchecked type coercion, silent fallback, magic values, catch-all swallowing, hidden global state and unrelated refactoring.

## Type safety and data integrity

- Preserve `InsCode` as an **exact textual identifier**, not a floating-point Excel number.
- Model quantities, timestamps, market status and financial units explicitly. Distinguish IRR from IRT and estimates from executed trade values.
- Treat `null`, zero, absent, stale, unknown, halted, partial response and HTTP error as **different states**.
- Validate HTTP and JSON shape, IDs, timestamps, numeric bounds and data consistency before using values in the workbook.
- Use safe cancellation, timeouts, disposal and nonblocking I/O where appropriate. Respect Excel/COM and Excel-DNA thread affinity; never access Excel objects unsafely from background workers.
- Preserve user-entered data and formulas. Minimize partial writes, avoid stale queue displays, and obtain explicit approval for any workbook schema migration or destructive operation.
- Protect secrets, personally identifying data, brokerage information and proprietary algorithms; use sanitized test fixtures.

## Automated testing — non-negotiable

- **Every code change, no matter how small, must include or update relevant automated unit tests.** If genuinely not unit-testable, Codex must justify the exception and include the nearest useful automated verification; this is not a blanket exemption.
- Unit tests must be deterministic, fast and isolated from Excel installation, live internet connectivity and current market hours.
- Add integration/contract tests where changes cross HTTP/API, serialization, Excel interop, persistence or add-in registration boundaries. Mark environment-dependent Excel checks separately.
- Cover both success and failure: empty/partial ClientType, halted but valid instruments, unknown codes, malformed JSON, timeouts, invalid/long IDs, date mismatch, currency/locale precision, stale order queues, safe rollback and formula preservation.
- Every implementation prompt must contain runnable build/test commands **when verified**, reporting requirements and explicit PO-run Excel acceptance checks.
- Never invent passing builds, test counts or code coverage. Include actual command output or clearly state that an environment could not run it.

## English artifacts and professional delivery

- Use **English** for source-code comments, XML documentation, docstrings, test names, developer messages, engineering handoffs and all documentation unless the PO explicitly requests an exception.
- Write comments for non-obvious business invariants, public contracts and caveats; avoid redundant comment clutter.
- Keep implementation scope focused and coherent; new dependencies and architecture changes need clear rationale and PO approval.
- A deliverable report must identify changed files, design choices, verified test/build commands and results, tests not executed, unresolved risks and steps for PO local acceptance testing.
- **Codex never commits; ChatGPT never modifies source; the PO alone commits source after local validation.**
