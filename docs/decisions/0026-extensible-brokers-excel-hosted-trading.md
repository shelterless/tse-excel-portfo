# D-026 — Extensible Broker Integration and Excel-Hosted Order Execution

- **Status:** Accepted
- **Date accepted:** 2026-10-28
- **Implementation status:** Deferred

## Context

The product will initially target Mofid (EasyTrader), while retaining the architectural ability to integrate additional brokerages in the future.

The PO intends to support manually initiated order placement, modification, and cancellation, and later preconfigured automated order submission, including opening-session queue-order attempts.

The most recent PO decision is that automated execution runs only while Excel and the add-in are active. Execution with Excel closed or the user's computer turned off is not a current requirement.

## Decision

### Broker independence

- Define broker-facing application contracts independent of Mofid-specific APIs and response models.
- Implement the initial Mofid integration within `Infrastructure/Brokers/Mofid/`.
- Additional broker adapters may be introduced under `Infrastructure/Brokers/` without requiring separate C# projects.
- Keep broker-specific authentication, request mapping, error handling, and API details inside their adapters.
- Do not build a multi-broker selection framework before a real second broker is required.
- Actual contract signatures and broker capabilities must be designed after verifying the relevant APIs.

### Manual trading

- Order placement, modification, and cancellation require a deliberate user action and explicit confirmation.
- Separate the user's requested operation from the broker's acknowledged order state.
- Do not interpret request submission as confirmed order acceptance or trade execution.

### Future automated trading

- Support the future concept of user-defined, preapproved order plans.
- Automated execution requires explicit user activation and bounded authorization.
- The execution engine belongs to application logic, not Ribbon callbacks.
- The engine must support cancellation, explicit operational states, risk limits, and prevention of unintended duplicate submissions.
- Ambiguous broker responses must not trigger blind resubmission.
- Reconcile order states with the broker when needed and supported.
- Execution must stop submitting new requests when the Excel-hosted execution environment is no longer active.
- Orders already accepted by a broker may remain active after Excel closes; closing Excel does not imply broker-side cancellation.
- Do not introduce a standalone service, cloud executor, or unattended machine-off execution under this decision.

### Security and operational safety

- Do not store brokerage credentials or access tokens in workbook-adjacent business JSON.
- Protect sensitive information and avoid exposing trading-account data in repository fixtures or diagnostic logs.
- Preserve an auditable distinction between planned, authorized, submitted, acknowledged, rejected, executed, cancelled, and uncertain operations, with exact states finalized against verified broker contracts.
- Automated trading must comply with applicable broker permissions, market rules, and permitted API usage.
- No order-priority, execution-time, or trade-fill guarantee is implied by the proposed queue-order feature.

## Deferred decisions

- Verified Mofid and future broker API contracts, authentication, and legal access.
- Order model, broker capabilities, amendment semantics, and order-status reconciliation.
- Automated order authorization limits, persistence, restart behavior, safety controls, and scheduling precision.
- Appropriate credential storage and audit storage mechanisms.
- Performance and reliability requirements for opening-session orders.

## Consequences

The architecture preserves future brokerage extensibility and automated trading without requiring their immediate implementation.

No live broker integration, order execution, or automated trading is authorized by this architectural decision alone. Each capability requires separate PO-approved scope, verification, and acceptance tests.
