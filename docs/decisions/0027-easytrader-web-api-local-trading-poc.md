# D-027 — EasyTrader Web API Integration and Local Trading Proof of Concept

**Status:** Accepted
**Date accepted:** 2026-11-03
**Related decisions:** D-025, D-026

## Context

TSE Excel is intended to provide an Excel-based trading and analytics client that integrates selected brokerage capabilities with independent public market-data sources.

The Product Owner has clarified that the intended initial Mofid integration uses the same private, undocumented web APIs consumed by the EasyTrader frontend, rather than requiring an officially published brokerage API.

The desktop EasyTrader experience at `d.easytrader.ir` is the preferred starting point for investigation. Whether desktop and mobile clients share the same backend remains unverified.

## Decision

1. **Integration approach:** Investigate and reproduce the necessary first-party EasyTrader web-client API interactions in a dedicated Mofid adapter. Do not replicate the entire browser interface unless technically necessary.

2. **Authentication:** Implement the observed legitimate authentication flow, including username/password, session establishment, and actual second-factor verification. Require interactive user input when necessary. Do not bypass CAPTCHA, MFA, or access controls.

3. **Data ownership:** Obtain brokerage-specific account, balance, portfolio, and order information from the Mofid integration. Obtain suitable public market data independently from TSETMC where appropriate.

4. **Initial validation:** Prioritize a minimal, local C# Console proof of concept before implementing trading capabilities in Excel. The initial experiment targets one explicitly approved, limited real order and measures submission, acknowledgement, and execution outcomes separately.

5. **Execution safety:** Enforce a bounded order value, explicit pre-authorization, one submission attempt, cancellation before submission, and no blind retries after uncertain responses. Respect verified market-session rules and applicable access restrictions.

6. **Credentials:** Keep credentials and session tokens outside source control and workbook business JSON. Protect local storage, avoid secret-bearing logs, and never store OTP values unnecessarily.

7. **Architecture:** Preserve D-025's four-project architecture and D-026's broker-independent application contracts. The Console experiment is temporary validation, not a permanent fifth production project or a change to the future Excel-hosted execution model.

8. **API uncertainty:** Treat all unofficial API contracts as unverified and subject to change. Public repositories are research references, not authoritative specifications. Confirm behavior against observed current EasyTrader traffic before implementation.

9. **Authorization:** This decision records the intended technical integration approach. It does not assert that Mofid has approved third-party API usage or resolve applicable contractual and regulatory restrictions.

## Initial Success Criteria

- Complete legitimate authentication with actual second-factor verification.
- Establish an authenticated session and perform a non-trading account request.
- Submit one explicitly authorized order through a verified supported request flow.
- Reconcile the broker response with the resulting order status where available.
- Capture meaningful timestamped performance measurements.
- Compare results with manual EasyTrader submission without claiming guaranteed queue priority or faster execution.

## Deferred

Excel trading UI, multi-order execution, advanced scheduling, credential-management infrastructure, multi-broker functionality, and production deployment security.
