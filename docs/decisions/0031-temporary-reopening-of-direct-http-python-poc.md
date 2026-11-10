# D-031 — Temporary Reopening of Direct HTTP Python POC for Reliability Validation

- **Status:** Accepted
- **Date accepted:** 2026-11-10
- **Related decisions:** D-028, D-029, D-030
- **Authority:** This decision grants a narrow, temporary exception to D-030 for independent Python POC reliability validation. It does not change the approved Excel/C# architecture or production scope.

## 1. Context

The Product Owner has successfully executed the direct HTTP Python POC against Mofid, including real order submissions and purchases.

However, observed live runs have exposed discrepancies between the application's final acknowledgement summary and the actual orders visible in Mofid. The current POC does not persist a per-run technical trace, making these discrepancies difficult to investigate.

The PO has approved a staged effort to establish reliable observability, response handling, and test evidence before proceeding with the Excel add-in implementation.

## 2. Temporarily Authorized Python Assets

The following files are temporarily reopened for implementation, execution, and automated testing within this validation program:

- `POC/easytrader_direct_http_poc.py`
- `POC/test_easytrader_direct_http_poc.py`

The following historical reference remains strictly read-only:

- `POC/easytrader_poc.py`

No other Python implementation or historical reference is reopened by this decision.

The PO maintains independent local backups of both existing Python implementations. Backup copies must remain outside the repository and must never be committed.

## 3. Approved Validation Program

The work is divided into four controlled stages:

1. Add sanitized, per-run trace logging without changing dispatch behavior.
2. Correct request lifecycle management, asynchronous response observation, and final outcome reporting.
3. Expand deterministic automated tests and perform PO-controlled live acceptance.
4. Freeze and document the validated Python reference before starting further Excel/C# implementation work.

Each implementation stage requires a bounded work package and PO approval. Approval of this decision does not authorize unrelated refactoring or unrestricted changes.

## 4. Preserved Invariants

Unless the PO explicitly approves a separate decision, preserve:

- Existing authentication and native HTTP transport behavior.
- Existing endpoints, request payloads, and decimal serialization.
- BUY-only live execution.
- The 50,000,000 IRR per-order safety cap (5,000,000 IRT).
- No aggregate order cap implied by the per-order limit.
- The 300 ms live minimum interval and 350 ms default.
- Existing bounded worker capacity and exclusive dispatch cutoff.
- No automatic retries or replay of ambiguous requests.
- No inference of broker acceptance or execution from local dispatch.
- Existing security and credential-handling restrictions.

Any proposed change to these invariants must be submitted to the PO before implementation.

## 5. Security and Operational Boundaries

- Trace files must contain sanitized technical events only.
- Never persist authentication material, credentials, cookies, tokens, raw payloads, raw response bodies, account balances, or broker order IDs.
- Runtime traces and local backups must not enter source control.
- Codex must not execute live brokerage operations or use real brokerage credentials.
- Only the PO performs live-account acceptance.
- No new undocumented broker endpoint or API behavior may be assumed.

## 6. Git and Delivery

Codex works on a dedicated feature branch based on current `main`, runs automated tests, and commits and pushes only that branch.

The PO retains explicit merge authorization and local acceptance authority under D-029.

Codex must not modify governance documentation, merge branches, or push directly to `main`.

## 7. Scope and Expiry

This decision supersedes only the conflicting read-only restriction in D-030 Section 2 for the two explicitly authorized direct HTTP Python files.

D-028's historical Python reference restrictions remain intact. D-030 continues to govern the Excel/C# implementation.

This temporary exception expires when the PO accepts the final Python validation stage and explicitly declares the Python reference frozen again, or when the PO withdraws this authorization.

Python remains a standalone validation/reference implementation, not a production dependency of the Excel add-in.
