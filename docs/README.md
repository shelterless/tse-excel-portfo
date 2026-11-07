# TSE Excel — Documentation Map

**Canonical source:** `shelterless/tse-excel-portfo`, current `main`. This is a routing index, not a duplicate policy store. Read only the smallest relevant documents. Do not recursively load linked materials.

| Task | Load when needed |
|---|---|
| ChatGPT bootstrap | `gpt/PROJECT-INSTRUCTIONS.md` (paste into Project Instructions only) |
| Product context and approved milestone scope | `project/PROJECT-CONTEXT.md`; relevant accepted ADR |
| Roles, authority, change approval | `project/OPERATING-CONTRACT.md`, `project/GOVERNANCE.md` |
| PO/Codex handoff and local workflow | `project/DEVELOPMENT-WORKFLOW.md`, `engineering/CODEX-HANDOFF.md`, `decisions/0029-feature-branch-source-review-workflow.md` |
| Coding and testing | `engineering/ENGINEERING-STANDARDS.md`, affected code/tests |
| Architecture and folder/dependency rules | `engineering/ARCHITECTURE.md`, applicable decision records |
| Mofid opening-order POC | `decisions/0028-excel-hosted-mofid-opening-order-poc.md`, `project/PRODUCT-BACKLOG.md`, `engineering/ARCHITECTURE.md` |
| Deferred trading enhancements | `project/PRODUCT-BACKLOG.md` |
| Workbook structure and formulas | `contracts/WORKBOOK-CONTRACT.md` |
| TSETMC reliability and errors | `contracts/DATA-RELIABILITY.md` |
| Decisions and unresolved matters | `decisions/README.md` → only relevant accepted ADRs; `decisions/OPEN-QUESTIONS.md` when necessary |
| Documentation revision history | `CHANGELOG.md` |

**Authority:** Newer explicit PO decisions > verified current `main` accepted records > verified source/test evidence > historical/cached context. Material contradictions require PO clarification. D-029 governs source delivery on reviewable feature branches and explicit PO merge authorization; ChatGPT source review remains read-only, and local/Excel/live-account acceptance remains PO-owned. ChatGPT commits only PO-approved documentation.

**ChatGPT synchronization:** Normally only `docs/gpt/PROJECT-INSTRUCTIONS.md` is pasted into Project Instructions; do not upload the full `docs/` tree to Project Sources. Re-paste only when that file changes. If live GitHub access is unavailable, disclose and request the smallest necessary current source rather than guessing.
