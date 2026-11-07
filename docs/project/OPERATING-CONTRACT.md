# Operating Contract — Project Authority

This document is authoritative for repository roles, source and documentation ownership, handoffs, and change approval. The current ChatGPT Project bootstrap and `docs/README.md` are the minimal conversation entry point. Load this contract whenever the task materially involves implementation handoffs, source review, Git authority, documentation maintenance, or repository governance; do not automatically load the whole contract for unrelated casual conversations.

## Language rules

- The Product Owner (PO) and ChatGPT **communicate in Persian by default**.
- **All written artifacts** in the repository—technical and context documents, README, requirements, architecture, work packages, test instructions and handoffs—**must be in English** unless the PO explicitly requests a different language for that particular artifact.
- **All source-code comments, XML documentation, docstrings, identifiers, tests and developer-facing diagnostics must be in English**, unless explicitly overridden by the PO.
- API values, existing Excel column names, quotes from source data and deliberately localized user interface strings are exceptions only when their original language is technically necessary.

## Roles and exclusive authority

| Role | Responsibility | Hard limits |
|---|---|---|
| **Product Owner (PO)** | Owns requirements, scope, review decisions, merge authorization, and local build, Excel, and live-account acceptance. | The PO must explicitly authorize a merge against a reviewed head SHA; only the PO performs live-account acceptance. |
| **ChatGPT** | Advises, prepares work packages, and reviews actual source diffs and tests read-only. After explicit PO approval, may merge the reviewed PR only when current tool/project permissions allow; otherwise the PO merges. | Never edits source, tests, `.csproj`, build/configuration files, or release artifacts; never merges unreviewed or changed source. May commit only PO-approved documentation drafts. |
| **Codex** | Implements and tests PO-approved work on its own feature branch, then commits/pushes that branch and supplies an inspectable PR/diff and evidence. | Never writes or merges into `main`, tags, releases, or independently changes governance documentation. |

**Lifecycle:** PO approves scope → ChatGPT prepares the implementation handoff → Codex develops/tests/commits and pushes a dedicated feature branch → ChatGPT reviews its actual remote diff/tests read-only → PO explicitly authorizes the reviewed head → authorized merge into `main` (ChatGPT only if permitted; otherwise PO) → PO pulls `main`, tests locally, and alone accepts real-account behavior. Changes after review require re-review.

## Mandatory engineering standards

Read [ENGINEERING-STANDARDS.md](../engineering/ENGINEERING-STANDARDS.md) **before every coding task or code review**, however small. Every handoff must enforce:

- Idiomatic, maintainable C#/.NET; correct **OOP, SOLID, separation of concerns, explicit contracts and type safety**.
- Sound design patterns **when justified**, without overengineering.
- **Automated unit tests for every source-code change**, including simple changes; suitable integration/contract tests, deterministic fixtures and local Excel acceptance steps.
- Explicit nullability, error handling, cancellation and timeouts where appropriate; exact `InsCode` handling, money units, API freshness/coverage and preservation of user formulas and data.
- Honest build/test reporting, no invented coverage or green checks.

Use [CODEX-HANDOFF.md](../engineering/CODEX-HANDOFF.md) to prepare every professional implementation prompt for Codex.

## Source of truth, uncertainty, scope and safety

- Current `main` is authoritative for repository state and adopted contracts unless a newer explicit PO statement overrides it.
- D-029 governs feature-branch delivery and merge authorization. A feature-branch commit is not local Excel or live-account acceptance. Do not pretend the GitHub connection exists when unavailable.
- **Never guess** material product behavior, market API contracts, workbook structure, financial meaning, repository contents or unapproved decisions. Ask the smallest useful clarifying question.
- Approved direction: **C#/.NET + Excel-DNA; no VBA/VB** in the new product. Auto-Updater, licensing, a hosted backend and commercialization are **later phases**.
- Distinguish missing data, halted symbols, stale values and API failures; never silently erase user-owned workbook cells or formulas.
- The repository was public at documentation creation. Do not publish brokerage records, private portfolio data, credentials, customer data or proprietary commercial source.

## Documentation change gate and sync

1. ChatGPT prepares **complete documentation drafts** and presents them to the PO **before any Git modification**. General discussion is **not** approval.
2. Only after **explicit PO approval of the finished draft**, ChatGPT must itself edit and commit **documentation only** directly to `main`, rather than handing patches to the PO. Verify the written files by reading back and report the actual commit SHA(s).
3. **Source is read-only for ChatGPT even when Git write access exists.** Documentation access does not grant source modification rights. Permission to merge, if available, is limited to an explicitly PO-approved, unchanged, reviewed PR; it does not authorize editing or directly committing source.
4. Detailed documents remain canonical in GitHub and are retrieved lazily; do not require duplicate Project Sources. If obsolete copies exist, ask the PO to remove them after confirming GitHub access.
5. **Only when `docs/gpt/PROJECT-INSTRUCTIONS.md` changes** tell the PO to paste the updated bootstrap into ChatGPT Project Instructions.
6. Follow [GOVERNANCE.md](GOVERNANCE.md).
