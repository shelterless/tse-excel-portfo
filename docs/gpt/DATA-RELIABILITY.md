# TSETMC Data Reliability and Failure Semantics

## Invariants

**No record**, **halted security**, **stale snapshot**, **valid zero** and **failed API request** are not interchangeable. Never erase a useful prior value merely because the current API response is incomplete, and never describe old data as live without evidence.

## Evidence from the prior workbook prototype

- One successful bulk MarketWatch test returned approximately 3,375 records, while ClientType returned approximately 2,401. These are **historical observations**, not stable coverage guarantees.
- SHPNA and FGOSTAR were missing in the bulk snapshot, while individual `GetClosingPriceInfo` responses returned valid prices and halted status `IS`.
- The ClientType DTO checked in the earlier test did not expose an independent verified `recDate`. Matching price timestamps **cannot establish** the freshness of ClientType metrics.
- A preflight check later reported `ClientType coverage below safe threshold: 2.9%`. Data-publication timing is a hypothesis, not a verified root cause.

## Recommended safety behavior for the MVP

1. Validate HTTP status, JSON structure, mandatory fields, units, instrument identity, ranges and available timestamps before mapping response data to workbook fields.
2. Build a coherent in-memory refresh result before writing where practical. Treat a sudden collapse in bulk coverage as a data-quality warning, not proof that all missing symbols are invalid.
3. If a security is absent from MarketWatch, consult a reliable individual instrument endpoint; do **not** infer `HALTED` or `NOT_FOUND` solely from bulk absence.
4. For `HALTED` securities, show state and last known valid quotes with their actual trading timestamp. Do **not** present obsolete order-book queues as current.
5. Handle ClientType availability **independently** of valid price refreshes. When participant data is absent, keep prior metrics labeled as stale/unavailable rather than writing fabricated zeroes.
6. On network, timeout, malformed response or mapping error, preserve existing user data and report the failure and affected fields. Distinguish partial success from total success.
7. Map confirmed API status codes only. Earlier verified values were `A` → `ACTIVE` and `IS` → `HALTED`; any new code is `UNKNOWN` pending verification. `UnderSupervision` is not a trading-state substitute.
8. Market-day freshness must account for holidays, weekends, closed hours and securities without trades. The computer's calendar date alone is not a reliable trading-day oracle.
9. Validate all financial units: quote prices, volumes, estimated retail value in IRR and exchange-reported turnover. Avoid silently interpreting IRR as IRT.
10. Provide explicit diagnostics for successful, partial, stale, halted, unavailable and failed results. `Refresh completed` does **not** prove all fields current or tradable.

## Test matrix

Automated unit tests must cover active/halted/unknown instruments, long exact IDs, invalid IDs, empty/partial MarketWatch, missing ClientType, unknown status codes, bad JSON, HTTP errors, date and queue mismatch, zero versus null, formula protection and multi-source inconsistency. Contract/integration tests should target external adapters; Excel-dependent end-to-end checks should be handed to the PO for local execution.

## Open decisions

The official API's availability, rate limits, legal/commercial terms, latency guarantees, caching, acceptable coverage thresholds and production freshness SLA remain **unresolved** until independently verified and approved. Prior successful prototype calls do not constitute a formal API contract.
