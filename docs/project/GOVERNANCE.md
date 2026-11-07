# Repository Governance and ChatGPT Context Synchronization

## Source of truth and language

- Repository: `shelterless/tse-excel-portfo`; canonical branch: `main`.
- At the beginning of a project conversation, read the current [Documentation Map](../README.md) and lazily load only relevant canonical documents. Load [Operating Contract](OPERATING-CONTRACT.md) for governance, source handoffs, documentation modifications, and other tasks where its rules materially apply.
- PO/ChatGPT conversation is **Persian**; all repository documents, source comments/docstrings and work-package artifacts are **English** unless the PO explicitly directs an exception.
- A newer explicit PO decision takes precedence over stale contextual copies. Conflicts affecting behavior or scope require clarification.

## Write-access matrix

| Actor | Read source | Edit source/tests/build files | Commit/push source | Merge into `main` | Documentation |
|---|---|---|---|---|---|
| **PO** | Yes | As owner | Yes | Explicitly authorizes; may perform | Approves documentation drafts |
| **ChatGPT** | Read-only | Never | Never | Only an unchanged reviewed PR after explicit PO approval and only if current permissions allow; otherwise PO merges | Drafts and commits only explicitly approved documentation |
| **Codex** | Yes | Only its approved feature branch | Feature branch only | Never | No independent governance changes |


ChatGPT's ability to write documentation does **not** grant permission to modify any `.cs`, tests, `.sln`, `.csproj`, configuration, scripts, runtime artifacts, workbook, release pipeline or source-adjacent implementation files. If a requested documentation change would necessarily change code, send that code task through the PO → Codex workflow instead.

## Documentation approval procedure

1. ChatGPT reads the current documents on `main` and prepares the complete, coherent **English proposal**.
2. ChatGPT presents the **finished draft** and the proposed changed-file list to the PO. **Do not write GitHub yet.**
3. PO explicitly approves the draft (possibly with corrections). If revised, present the updated version for approval where material.
4. ChatGPT itself writes and commits **approved documentation files only** directly to `main` (not via patches for the PO), avoiding unrelated rewrites, and reads back the final files. Report actual commits and changed paths. If GitHub write fails, say so without claiming completion.
5. Keep detailed documentation in canonical GitHub and retrieve it lazily. Do not require copied Project Sources; if obsolete copies exist, ask the PO to remove or replace them after verifying access to the canonical files.
6. **Only if `docs/gpt/PROJECT-INSTRUCTIONS.md` changes**, tell the PO to paste the updated complete bootstrap into ChatGPT Project Instructions.
7. Record approved lasting decisions in [DECISIONS](../decisions/HISTORICAL-DECISIONS.md) and material documentation changes in [CHANGELOG](../CHANGELOG.md).

## Codex delivery and Git rule

Codex works on a bounded feature branch, runs automated checks, commits/pushes only that branch, and provides the branch SHA, PR and actual verification evidence. ChatGPT reviews the remote diff and tests without source writes. The PO approves or rejects the precise reviewed head. A source merge must never occur without explicit PO authorization and cannot be inferred from green checks. The PO then pulls `main` and performs local/Excel acceptance. Documentation approval remains separate.

## Security and other boundaries

- The repository was public when the context was drafted. Never commit credentials, brokerage/portfolio exports, customer data or proprietary algorithms to public Git.
- Do not treat this repository as canonical personal-portfolio accounting. It is a software product repository.
- Proposal paths and folder trees are not proof a C# implementation exists. Verify repository state before discussing it as implemented.
