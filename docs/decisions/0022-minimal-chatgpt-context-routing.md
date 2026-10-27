# D-022 — Minimal ChatGPT Context Routing

- **Status:** Accepted
- **Date accepted:** 2026-10-27

## Context

The previous setup required reading a full Operating Contract at startup and duplicating topic documents into Project Sources. The PO wants a tiny bootstrap and GitHub-first lazy retrieval.

## Decision

- Keep only `docs/gpt/PROJECT-INSTRUCTIONS.md` under `docs/gpt/` and paste its contents into ChatGPT Project Instructions.
- On project conversation start, read the current `docs/README.md` routing index; load the full Operating Contract only for governance, documentation changes, source authorization, and Codex/implementation activities where material.
- Keep topic documents and decisions in their proper `docs/` subfolders. Do not preload all ADRs or upload them to Project Sources by default.
- Preserve the PO's exclusive source commit authority, ChatGPT documentation-approval gate, and Codex no-commit rule in the always-on bootstrap and canonical contracts.
- If GitHub is inaccessible, disclose the blocker and request narrowly relevant current evidence rather than relying on stale copies.
- Re-paste Project Instructions only after a verified change to `docs/gpt/PROJECT-INSTRUCTIONS.md`.

## Consequences

D-013 and D-014 are superseded in their context-loading and copied-sources requirements only. Their original wording and status remain preserved in the historical log. This reduces default context loading without relaxing Git authority or documentation approvals.
