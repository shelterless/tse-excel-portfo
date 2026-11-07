# Open Questions and Historical Technical Evidence

The unresolved issues and evidence below are carried forward from the verbatim [historical decision log](HISTORICAL-DECISIONS.md), without implying resolution. D-028 resolves the product-level workflow and UI requirements for one bounded POC; it does not turn private broker API observations into verified contracts.

## Unresolved decisions — do not guess

| Topic | Status |
|---|---|
| Minimum supported Excel and Windows versions, Office bitness and exact .NET/Excel-DNA compatibility | Open |
| Workbook schema, migration from the VBA prototype and JSON locking/Save As/concurrent-workbook behavior | Requires current workbook inspection and PO approval |
| Market-data freshness, ClientType publication timing, bulk coverage thresholds and TSETMC rate limits | Open; needs evidence |
| TSETMC terms of use and rights for commercial redistribution | Open |
| Public versus private repository for proprietary source code | Open; repository was public when these documents were drafted |
| Source build automation, signing, packaging and release distribution | Future decisions |
| Mofid authentication/browser integration, session lifecycle, draft retrieval, instrument metadata, commission values and order request/response contracts | D-027/D-028 authorize investigation and a bounded POC; exact current contracts remain private, undocumented and must be verified from evidence |
| Permitted third-party use of EasyTrader/Mofid private APIs and applicable broker terms | Unresolved; neither D-027 nor D-028 asserts broker authorization or legal permission |
| Secure session persistence implementation and recovery behavior | D-028 requires OS-backed protection; exact adapter and operational details must be verified during implementation |
| Live SELL request contract and execution | Explicitly disabled in D-028 until independently verified and approved |
| Broker response inspection, acceptance/rejection classification and order reconciliation | Deferred by D-028; the POC reports local dispatch activity only |
| Production trading safeguards, restart/persistence behavior, unattended scheduling, risk limits and audit storage | Deferred beyond D-028 |

## D-028 operational clarifications

- The dispatch window is locally bounded by the configured start time and duration.
- The default start time is 08:44:58 local Windows time, duration is 5 seconds and minimum dispatch interval is 350 microseconds.
- The displayed attempt estimate is approximate and is not a broker-acceptance estimate.
- The compact log has fixed dimensions, one line per locally initiated attempt, and vertical scrolling.
- Local attempt counts must not be described as accepted orders or executed trades.
- Cancelling local dispatch does not cancel requests already transmitted or broker-side orders.
- The Python reference `POC/easytrader_poc.py` is read-only and must not be executed, imported, modified or used as a runtime dependency.

If a material edge case is not defined by D-028 or verified reference behavior (including an already-passed start time, an incomplete authentication flow or missing required instrument metadata), Codex must stop and ask the PO rather than silently inventing behavior.

## Technical evidence — not binding API contracts

- Earlier tests observed `instrumentState.cEtaval` values `A` (permitted) and `IS` (halted).
- SHPNA and FGOSTAR were missing in a bulk API snapshot but returned valid individual endpoint data and `IS` state.
- ClientType snapshot coverage varied significantly across observed tests.

For technical interpretation, consult [WORKBOOK-CONTRACT](../contracts/WORKBOOK-CONTRACT.md) and [DATA-RELIABILITY](../contracts/DATA-RELIABILITY.md). For role authority, consult [OPERATING-CONTRACT](../project/OPERATING-CONTRACT.md).
