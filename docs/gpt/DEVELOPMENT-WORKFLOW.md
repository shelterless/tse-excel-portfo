# Development Workflow — PO, ChatGPT, Codex/Astra

## Role-driven lifecycle

1. **PO defines the need.** The user, acting as Product Owner, sets goals, priorities and scope.
2. **ChatGPT advises and clarifies.** Inspect source **read-only** on verified `main`, read [OPERATING-CONTRACT](OPERATING-CONTRACT.md) and task-specific documents, identify tradeoffs and ask about material ambiguity.
3. **ChatGPT proposes the work package.** Define boundaries, design considerations, risks, acceptance criteria and test requirements. The PO confirms the scope.
4. **ChatGPT writes a professional Codex/Astra prompt** conforming to [CODEX-HANDOFF](CODEX-HANDOFF.md) and [ENGINEERING-STANDARDS](ENGINEERING-STANDARDS.md), with current reference URLs and explicit **no-commit** constraints.
5. **Codex/Astra implements** C# source and automated tests in the development workspace. No commits, pushes, tags, PRs or releases.
6. **Codex/Astra reports technical verification** using actual commands/results; any environment-dependent Excel test remains clearly pending when not executable.
7. **PO runs local tests and acceptance checks**, including the real workbook/Excel where relevant, and approves or rejects the implementation.
8. **PO personally commits/pushes source** only after accepting the local result. ChatGPT does not do source writes, even if technically connected to GitHub.

## Documentation lifecycle — separate approval gate

1. ChatGPT proposes documentation changes and prepares the **finished English draft**.
2. **PO reads and explicitly approves** the completed draft. Prior discussions and informal agreement with the idea are not sufficient approval to commit its final wording.
3. ChatGPT then updates and **commits documentation only** directly to `main`, checks its final contents, and reports exact paths/commit SHA.
4. PO replaces the changed documents in ChatGPT Project Sources. Replace ChatGPT Project Instructions **only when** `PROJECT-INSTRUCTIONS.md` changed.

## Definition of ready for Codex/Astra

A work package must have sufficiently clear product behavior, approved boundaries, authoritative references, data contracts, testable acceptance criteria and compatibility assumptions (or explicitly labeled unresolved prerequisites). If a material decision is open, ask the PO first.

## Definition of done for source delivery

- Functionality satisfies agreed acceptance conditions.
- Type-safe, maintainable C# conforms to OOP/SOLID and relevant standards.
- Automated unit tests exist for **every** code change, with meaningful negative cases; relevant integration/contract tests included.
- Build/test results are reported honestly and any unavailable check is disclosed.
- Workbook values, user formulas, manual columns and private data are protected.
- PO has run required local verification and accepted the result **before committing**.

Avoid lengthy rounds of manual micro-tests. Prefer cohesive implementation and one PO acceptance pass, supported by developer-run automated tests.

## Phase boundary

Initial target: locally built C#/.NET + Excel-DNA Windows Excel add-in. Auto-Updater, license management, hosted backend, monetization and Python are out of the MVP. Exact .NET/Excel-DNA versions, Office compatibility and installer approach remain PO decisions.
