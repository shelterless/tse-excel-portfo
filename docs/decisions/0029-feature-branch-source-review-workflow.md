# D-029 — Feature-Branch Source Delivery, Review, and Authorized Merge

- **Status:** Accepted
- **Date accepted:** 2026-11-07
- **Related decisions:** D-009, D-010, D-011, D-021, D-022, D-028
- **Authority:** Source-delivery Git permissions, remote review, explicit merge authorization, and post-merge local acceptance.

## 1. Context

Source changes left only in an uncommitted local working tree cannot be inspected reliably through the connected GitHub repository. The PO approves a reviewable feature-branch handoff followed by an explicit merge authorization and PO-run local acceptance.

## 2. Approved workflow

1. The PO approves a bounded implementation task and its acceptance criteria. Codex reads the current authoritative contracts before working.
2. Codex develops and tests in a dedicated feature branch based on the current `main`. It must not work directly on `main` or modify unrelated files.
3. Codex may commit and push the source/test changes **only to its own feature branch**, after automated verification. It may open a pull request targeting `main` for review; it must never merge a PR, push to `main`, tag, or publish a release.
4. Codex delivers the branch name, commit SHA, PR URL (if any), changed-file manifest, actual build/test commands and results, unrun tests, and risks. It must verify that read-only references, protected documentation, and sensitive data remain unchanged.
5. ChatGPT reads the actual GitHub diff and tests **read-only**, checks them against the accepted ADRs and architecture, and reports blockers and acceptance considerations. A successful build or test report is not itself merge approval.
6. The PO reviews ChatGPT's findings and explicitly approves or declines merging a particular branch/PR at a specified head SHA. Any subsequent source changes invalidate the earlier review/approval until checked again.
7. After that explicit approval, ChatGPT may perform the GitHub merge of the approved PR into `main` **only when current tool and project permissions allow it**; otherwise the PO performs the merge. ChatGPT may not edit source, commit source directly, rewrite source history, merge without approval, or silently resolve conflicts. If the approved head has changed, stop and ask the PO.
8. The PO pulls current `main`, performs local build, automated tests, Excel acceptance, and any separately approved live-account validation. A failing acceptance is reported and handled through a new reviewed change or rollback; it is not concealed by the previous merge.
9. Documentation changes retain their separate completed-draft PO approval gate. Codex must not independently change governance documentation. Only ChatGPT may commit documentation after PO review and explicit approval.

## 3. Safety and scope safeguards

- Before any merge, distinguish verified GitHub content from Codex's textual claims; no inferred green tests, compatibility, or live brokerage results.
- Do not commit credentials, cookies, tokens, brokerage records, private workbooks, generated binaries, or unrelated changes.
- Do not execute, import, or modify `POC/easytrader_poc.py` under D-028.
- A reviewable source commit is not production or live-trading acceptance. Only the PO initiates and approves real-account testing.
- Branch naming should identify the bounded feature, for example `feature/d028-mofid-opening-orders`.
- This decision supersedes only conflicting **source Git commit/push and merge-authority provisions** of earlier role/workflow documents. It preserves ChatGPT's source-edit restrictions, PO-owned acceptance, and all implementation, testing, and security boundaries.
