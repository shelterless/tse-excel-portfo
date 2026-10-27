# Repository Governance and ChatGPT Context Synchronization

## Source of truth and language

- Repository: `shelterless/tse-excel-portfo`; canonical branch: `main`.
- At the beginning of **every conversation**, read [OPERATING-CONTRACT](OPERATING-CONTRACT.md) and [Context Index](README.md); only load other task-relevant files.
- PO/ChatGPT conversation is **Persian**; all repository documents, source comments/docstrings and work-package artifacts are **English** unless the PO explicitly directs an exception.
- A newer explicit PO decision takes precedence over stale contextual copies. Conflicts affecting behavior or scope require clarification.

## Write-access matrix

| Actor | Read source | Edit source/tests/build files | Commit/push source | Draft documentation | Commit documentation to `main` |
|---|---|---|---|---|---|
| **PO (user)** | Yes | As owner | **Exclusive authority, after local tests** | Approves | May directly if desired |
| **ChatGPT** | **Read-only** | **Never** | **Never** | Yes | **Yes, only after PO approval of the finished draft** |
| **Codex** | Yes, for implementation | Yes, in uncommitted working tree | **Never** | Only when task explicitly calls for it; context governance remains PO/ChatGPT-controlled | **Never** |

ChatGPT's ability to write documentation does **not** grant permission to modify any `.cs`, tests, `.sln`, `.csproj`, configuration, scripts, runtime artifacts, workbook, release pipeline or source-adjacent implementation files. If a requested documentation change would necessarily change code, send that code task through the PO → Codex workflow instead.

## Documentation approval procedure

1. ChatGPT reads the current documents on `main` and prepares the complete, coherent **English proposal**.
2. ChatGPT presents the **finished draft** and the proposed changed-file list to the PO. **Do not write GitHub yet.**
3. PO explicitly approves the draft (possibly with corrections). If revised, present the updated version for approval where material.
4. ChatGPT itself writes and commits **approved documentation files only** directly to `main` (not via patches for the PO), avoiding unrelated rewrites, and reads back the final files. Report actual commits and changed paths. If GitHub write fails, say so without claiming completion.
5. PO replaces only affected copied ChatGPT Project Sources.
6. **Only if `docs/gpt/PROJECT-INSTRUCTIONS.md` changes**, tell the PO to copy its new full contents into ChatGPT Project Instructions.
7. Record approved lasting decisions in [DECISIONS](DECISIONS.md) and material documentation changes in [CHANGELOG](CHANGELOG.md).

## Codex delivery and Git rule

Codex must not commit, push, tag, publish, open/merge PRs or alter GitHub release state. It hands uncommitted code and tests to the PO, reports verified tests/builds, and the PO runs local acceptance tests before personally committing source. ChatGPT may review those source changes but **must not make them**.

## Security and other boundaries

- The repository was public when the context was drafted. Never commit credentials, brokerage/portfolio exports, customer data or proprietary algorithms to public Git.
- Do not treat this repository as canonical personal-portfolio accounting. It is a software product repository.
- Proposal paths and folder trees are not proof a C# implementation exists. Verify repository state before discussing it as implemented.
