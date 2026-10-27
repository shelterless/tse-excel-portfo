# TSE Excel — Documentation Map

**Canonical source:** `shelterless/tse-excel-portfo`, current `main`. This is a routing index, not a duplicate policy store. Read only the smallest relevant documents. Do not recursively load linked materials.

| Task | Load when needed |
|---|---|
| ChatGPT bootstrap | `gpt/PROJECT-INSTRUCTIONS.md` (paste into Project Instructions only) |
| Product context and prototype scope | `project/PROJECT-CONTEXT.md` |
| Roles, authority, change approval | `project/OPERATING-CONTRACT.md`, `project/GOVERNANCE.md` |
| PO/Codex handoff and local workflow | `project/DEVELOPMENT-WORKFLOW.md`, `engineering/CODEX-HANDOFF.md` |
| Coding and testing | `engineering/ENGINEERING-STANDARDS.md`, affected code/tests |
| Architecture | `engineering/ARCHITECTURE.md`, applicable decision records |
| Workbook structure and formulas | `contracts/WORKBOOK-CONTRACT.md` |
| TSETMC reliability and errors | `contracts/DATA-RELIABILITY.md` |
| Decisions and unresolved matters | `decisions/README.md` -> only relevant accepted ADRs; `decisions/OPEN-QUESTIONS.md` when necessary |
| Documentation revision history | `CHANGELOG.md` |

**Authority:** Newer explicit PO decisions > verified current `main` approved records > verified source/test evidence > historical/cached context. Material contradictions require PO clarification. Source is read-only to ChatGPT; only the PO commits source after testing. ChatGPT commits only PO-approved documentation to `main`. Codex never commits source in this repository.

**ChatGPT synchronization:** Normally only `docs/gpt/PROJECT-INSTRUCTIONS.md` is pasted into Project Instructions; do not upload the full `docs/` tree to Project Sources. Re-paste only when that file changes. If live GitHub access is unavailable, disclose and request the smallest necessary current source rather than guessing.
