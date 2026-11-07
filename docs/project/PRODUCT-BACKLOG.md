# Product Backlog — Trading Enhancements

This document records future product directions related to the opening-order POC. Inclusion here is not implementation authorization. Each item requires a separately discussed and PO-approved scope, decision record where material, and objective acceptance criteria.

D-028 is the authoritative scope for the current Excel-hosted opening-order POC. Do not pull deferred items into that implementation.

## BL-001 — Expanded Trading Ticket

Revisit the expanded trading interface represented by the Product Owner's second EasyTrader reference screenshot.

Potential information includes:

- Last price and percentage change.
- Trading volume and relevant market statistics.
- Buy and sell price levels.
- Buy and sell queue quantities.
- Multiple levels of the order book.

The D-028 MVP deliberately uses a compact order-entry form.

## BL-002 — Price Floor and Ceiling

Consider optional minimum and maximum permitted price fields, using verified current instrument metadata and market rules. Do not introduce manually guessed bounds.

## BL-003 — Optional Break-Even Price

Consider displaying break-even price after a verified calculation model is available. The model must account for applicable fees and commissions. This is not an MVP requirement.

## BL-004 — Broker Response Inspection

Consider inspecting individual transport responses and distinguishing:

- Dispatch initiated.
- HTTP response received.
- Broker accepted.
- Broker rejected.
- Unknown outcome.

HTTP transport success must never be treated as broker order acceptance. Any response-inspection work must be designed against verified broker contracts.

## BL-005 — Broker Reconciliation and Completion Summary

Consider a later completion view showing accepted, rejected and unresolved orders, plus broker order identifiers where verified. This requires broker-side reconciliation and is excluded from D-028.

## BL-006 — Live Market-Depth Integration

Consider integrating suitable Mofid and/or TSETMC market-depth data. Verify source, timestamp, freshness and completeness before presentation.

## BL-007 — Verified Live SELL Execution

SELL drafts may be displayed in D-028, but live SELL dispatch remains disabled until its request contract and broker behavior are independently verified and the PO approves the capability.

## Explicit D-028 exclusions

- Current account assets or available buying-power display.
- Aggregate financial exposure across repeated attempts.
- User-editable trading-validity selector.
- Quantity minimum/maximum controls.
- Price floor/ceiling controls.
- Mandatory break-even calculation.
- Broker acceptance/rejection inspection or order reconciliation.
- Full market-depth visualization.
- Live SELL execution before separate verification and approval.
- Automated unattended execution outside the active Excel/add-in session.
