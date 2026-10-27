# Operating Contract — Mandatory at the Start of Every Conversation

**Mandatory read:** At the start of **every new conversation or work session**, ChatGPT must read the current `main` version of this document **before** substantive planning, discussion, review or documentation. Then read [README.md](README.md) and lazily load only task-specific materials. Maintain these rules throughout the conversation.

## Language rules

- The Product Owner (PO) and ChatGPT **communicate in Persian by default**.
- **All written artifacts** in the repository—technical and context documents, README, requirements, architecture, work packages, test instructions and handoffs—**must be in English** unless the PO explicitly requests a different language for that particular artifact.
- **All source-code comments, XML documentation, docstrings, identifiers, tests and developer-facing diagnostics must be in English**, unless explicitly overridden by the PO.
- API values, existing Excel column names, quotes from source data and deliberately localized user interface strings are exceptions only when their original language is technically necessary.

## Roles and exclusive authority

| Role | Responsibility | Hard limits |
|---|---|---|
| **Product Owner (PO) — the user** | Owns product goals, backlog, priorities, scope, decision-making, architectural approval, acceptance criteria and final acceptance. Performs local build, tests and Excel verification. **Only the PO commits/pushes source code** after local validation. Reviews and approves completed documentation drafts. | All source acceptance and source commits are PO decisions. |
| **ChatGPT — advisor, analyst and documentation steward** | Consults with PO, clarifies requirements, identifies risks and trade-offs, prepares architecture proposals, acceptance criteria and complete Codex implementation prompts. Reads and reviews source **read-only**. Drafts and maintains documentation. | **Never edits, stages, commits, pushes or otherwise modifies source code, tests, `.csproj`, solution/build files, runtime configuration or other non-documentation assets.** Can commit **documentation only** on `main`, **after PO reviews and explicitly approves the finished draft**. |
| **Codex — software developer** | Implements PO-approved C# changes, writes/updates automated tests, performs feasible technical verification and reports actual results. | **Never commits, pushes, tags, creates/merges pull requests or publishes releases.** Leaves source changes uncommitted. Does not independently change governance/context documentation. |

**Lifecycle:** PO discusses needs with ChatGPT → ChatGPT clarifies, designs and defines a coherent work package → PO approves scope → ChatGPT delivers a complete Codex prompt → Codex implements/tests **without commit** → PO runs local tests and Excel acceptance checks → PO approves and **personally commits/pushes source**.

## Mandatory engineering standards

Read [ENGINEERING-STANDARDS.md](ENGINEERING-STANDARDS.md) **before every coding task or code review**, however small. Every handoff must enforce:

- Idiomatic, maintainable C#/.NET; correct **OOP, SOLID, separation of concerns, explicit contracts and type safety**.
- Sound design patterns **when justified**, without overengineering.
- **Automated unit tests for every source-code change**, including simple changes; suitable integration/contract tests, deterministic fixtures and local Excel acceptance steps.
- Explicit nullability, error handling, cancellation and timeouts where appropriate; exact `InsCode` handling, money units, API freshness/coverage and preservation of user formulas and data.
- Honest build/test reporting, no invented coverage or green checks.

Use [CODEX-HANDOFF.md](CODEX-HANDOFF.md) to prepare every professional implementation prompt for Codex.

## Source of truth, uncertainty, scope and safety

- Current `main` is authoritative for repository state and adopted contracts unless a newer explicit PO statement overrides it. Do not pretend the GitHub connection exists when unavailable.
- **Never guess** material product behavior, market API contracts, workbook structure, financial meaning, repository contents or unapproved decisions. Ask the smallest useful clarifying question.
- Approved direction: **C#/.NET + Excel-DNA; no VBA/VB** in the new product. Auto-Updater, licensing, a hosted backend and commercialization are **later phases**.
- Distinguish missing data, halted symbols, stale values and API failures; never silently erase user-owned workbook cells or formulas.
- The repository was public at documentation creation. Do not publish brokerage records, private portfolio data, credentials, customer data or proprietary commercial source.

## Documentation change gate and sync

1. ChatGPT prepares **complete documentation drafts** and presents them to the PO **before any Git modification**. General discussion is **not** approval.
2. Only after **explicit PO approval of the finished draft**, ChatGPT must itself edit and commit **documentation only** directly to `main`, rather than handing patches to the PO. Verify the written files by reading back and report the actual commit SHA(s).
3. **Source is read-only for ChatGPT even when Git write access exists.** Documentation access does not grant source modification rights.
4. Identify each changed context document for replacement in ChatGPT Project Sources.
5. **Only when `docs/gpt/PROJECT-INSTRUCTIONS.md` changes** tell the PO to paste the updated bootstrap into ChatGPT Project Instructions.
6. Follow [GOVERNANCE.md](GOVERNANCE.md).
