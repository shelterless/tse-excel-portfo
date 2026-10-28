# Open Questions and Historical Technical Evidence

The unresolved issues and evidence below are carried forward from the verbatim [historical decision log](HISTORICAL-DECISIONS.md), without implying resolution.

## Unresolved decisions (do not guess)

| Topic | Status |
|---|---|
| Minimum supported Excel and Windows versions, x86/x64 and exact .NET/Excel-DNA versions | Open |
| `.sln`/project structure, NuGet versions, Ribbon UX and local add-in installation | Four-project target and naming approved by D-025; source migration pending. The local Ribbon/JSON prototype was validated; broader version compatibility and deployment choices remain open. |
| Workbook schema versioning and migration from the VBA prototype | Requires current workbook inspection and PO approval |
| Market-data freshness, ClientType publication timing, bulk coverage thresholds | Open; needs evidence |
| TSETMC terms of use, scaling/rate limits and rights for commercial redistribution | Open |
| Public versus private repository for proprietary source code | Open; currently observed as public |
| Source build automation, signing and release distribution | Future decisions |
| Business JSON schema, locking mechanism, Save As behavior and concurrent-workbook policy | Deferred; requires future design and PO approval |
| Mofid and future broker API contracts, authentication, supported order operations, and permitted usage | Open; architectural direction only in D-026 |
| Automated order authorization limits, persistence/restart behavior, reconciliation, scheduling precision, credential and audit storage | Deferred; D-026 does not authorize implementation |

## Technical evidence — not binding API contracts

- Earlier tests observed `instrumentState.cEtaval` values `A` (permitted) and `IS` (halted).
- SHPNA and FGOSTAR were missing in a bulk API snapshot but returned valid individual endpoint data and `IS` state.
- ClientType snapshot coverage varied significantly across observed tests.

For technical interpretation, consult [WORKBOOK-CONTRACT](../contracts/WORKBOOK-CONTRACT.md) and [DATA-RELIABILITY](../contracts/DATA-RELIABILITY.md). For role authority, consult [OPERATING-CONTRACT](../project/OPERATING-CONTRACT.md).
