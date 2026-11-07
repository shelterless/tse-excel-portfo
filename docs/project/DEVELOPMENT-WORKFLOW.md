# Development Workflow — PO, ChatGPT, Codex

## Role-driven lifecycle

1. PO defines and approves a bounded task and acceptance criteria.
2. ChatGPT verifies current `main` and relevant engineering/decision documents read-only.
3. ChatGPT prepares the complete Codex implementation package after scope approval.
4. Codex creates an isolated feature branch, implements and tests without modifying `main`.
5. Codex commits and pushes only that feature branch, optionally opens a PR, and reports the exact head SHA, diff, and build/test evidence.
6. ChatGPT reviews the remote source diff and tests read-only; blockers are resolved on the feature branch and reviewed again.
7. PO explicitly approves a specific reviewed head for merge. The authorized merge is performed only if current permissions permit; otherwise PO merges. No approval carries over to a changed head.
8. PO pulls `main`, locally runs the build, tests, Excel checks, and any separately approved live-account test. PO owns acceptance and any subsequent corrective work decision.

## Documentation lifecycle — separate approval gate

1. ChatGPT proposes documentation changes and prepares the **finished English draft**.
2. **PO reads and explicitly approves** the completed draft. Prior discussions and informal agreement with the idea are not sufficient approval to commit its final wording.
3. ChatGPT itself applies and **commits the approved documentation changes only** directly to `main` (not via patches for the PO), checks its final contents, and reports exact paths/commit SHA.
4. Detailed documents remain canonical in GitHub, not duplicated in Project Sources. Replace ChatGPT Project Instructions **only when** `docs/gpt/PROJECT-INSTRUCTIONS.md` changes.

## Definition of ready for Codex

A work package must have sufficiently clear product behavior, approved boundaries, authoritative references, data contracts, testable acceptance criteria and compatibility assumptions (or explicitly labeled unresolved prerequisites). If a material decision is open, ask the PO first.

## Definition of done for source delivery

- Functionality satisfies agreed acceptance conditions.
- Type-safe, maintainable C# conforms to OOP/SOLID and relevant standards.
- Automated unit tests exist for **every** code change, with meaningful negative cases; relevant integration/contract tests included.
- Build/test results are reported honestly and any unavailable check is disclosed.
- Workbook values, user formulas, manual columns and private data are protected.
- The feature branch, head SHA, diff and test evidence have been reviewed; the PO has explicitly authorized the reviewed merge. Local Excel/live acceptance remains pending until the PO performs it after pulling `main`.

Avoid lengthy rounds of manual micro-tests. Prefer cohesive implementation and one PO acceptance pass, supported by developer-run automated tests.

## Local Development Preference — GUI First

Prefer supported VS Code graphical tools, extensions, Solution Explorer, NuGet package management, and integrated Tasks over repetitive terminal commands. Use direct shell commands for initial setup, troubleshooting, or actions without a suitable graphical workflow.

When build, test, and quality checks recur, use a small repeatable VS Code Task or repository-managed entry point (for example, `checkAll`) if justified. Do not introduce scripts or automation just for the initial JSON proof of concept. Continue to require automated tests for source changes and PO-run local Excel acceptance.

When coaching the PO through local setup, provide one actionable stage at a time and wait for the outcome before advancing.

## Phase boundary

Initial target: locally built C#/.NET + Excel-DNA Windows Excel add-in. Auto-Updater, license management, hosted backend, monetization and Python are out of the MVP. Exact .NET/Excel-DNA versions, Office compatibility and installer approach remain PO decisions.
