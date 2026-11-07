# D-028 — Excel-Hosted Mofid Opening-Order Proof of Concept

- **Status:** Accepted
- **Date accepted:** 2026-11-07
- **Related decisions:** D-025, D-026, D-027
- **Authority:** This record is the authoritative functional and architectural scope for the Excel-hosted opening-order POC.

## 1. Context

The Product Owner has manually validated a Python-based EasyTrader opening-order proof of concept. The current repository records the last tested invocation in the frozen reference at `POC/easytrader_poc.py`:

```powershell
python POC/easytrader_poc.py --browser-single-order --live
```

The Python implementation is a behavioral and technical reference only. The next implementation milestone reproduces the approved workflow in the existing C#/.NET Excel-DNA add-in. Python is not part of the production runtime.

The existing four-project architecture in D-025 remains authoritative. This POC is a bounded, local, Excel-hosted experiment, not a production trading platform or a replacement for the separate market-data MVP.

## 2. Scope and relationship to earlier decisions

Implement a minimal Mofid opening-order workflow hosted by the existing Excel add-in, using Persian Windows Forms UI.

D-028 supersedes D-027 only where the earlier one-order Console-first validation sequence and single-submission scope conflict with this specifically approved Excel-hosted POC. It does not supersede D-027's requirements to use observed authentication behavior, treat private API contracts as unverified until evidenced, protect credentials, avoid authentication bypasses, or acknowledge that this project decision does not establish broker authorization or resolve legal/contractual permissions.

D-026 remains the general future broker architecture and trading direction. D-028 authorizes only the bounded functionality described here.

## 3. Frozen Python reference — strict read-only boundary

The reference file is:

`POC/easytrader_poc.py`

Codex may inspect and read this file to understand and compare existing behavior, defaults, calculations, request construction and observed API interactions.

**The file is strictly read-only.** Codex must not:

- Edit, format, refactor, rename, move, delete, replace or regenerate it.
- Execute, import, invoke or otherwise run the Python script.
- Add Python as a runtime, build, test or deployment dependency.
- Copy the script into the C# implementation or call it as a subprocess.
- Change Python files or Python-related project assets as part of this task.

Use the reference only to inform an independent C# implementation. If observed behavior is ambiguous or conflicts with this decision, stop and ask the PO. Verify that the reference file remains unchanged before delivery.

## 4. Ribbon entry points

Provide two Persian Ribbon actions:

- `ورود به مفید`
- `ارسال سرخطی`

The login action establishes or refreshes an authenticated session. The opening-order action reuses a valid session where possible and requires interactive authentication when the session is expired or invalid.

All user-facing labels, buttons, dialogs, validation messages and operational text must be Persian. Source identifiers, comments, XML documentation, tests and developer diagnostics remain English.

## 5. Authentication and session management

- Reproduce the observed legitimate Mofid authentication flow.
- Preserve actual MFA/CAPTCHA interaction and require user input when necessary.
- Never bypass authentication challenges or access controls.
- Close the authentication window opened by the add-in after successful authentication.
- Reuse a valid session for later operations; reauthenticate when expired or invalid.
- Keep credentials and reusable session material outside workbook-adjacent business JSON and source control.
- Protect persistent local secrets with an operating-system-backed mechanism, such as Windows Credential Manager or DPAPI. Do not implement custom cryptography.
- Do not persist OTP values or one-time authorization codes.
- Never expose credentials, tokens or cookies in logs, fixtures, exceptions or UI diagnostics.

Verify the actual browser integration and authentication contract against available evidence. Do not assume OAuth, authorization-code/PKCE, or any other flow without evidence. If the current flow cannot be established reliably, stop and ask the PO rather than inventing it.

## 6. Opening-order workflow

The workflow has six sequential stages.

### Stage 1 — Draft selection

- Retrieve the current draft list from Mofid.
- Display drafts in a separate selection window.
- Select a draft by clicking its actual row; do not require manual identifier entry.
- Support vertical scrolling for long draft lists.
- Show symbol, instrument name, side, quantity and unit price.
- Select exactly one draft for each execution workflow.
- Treat the selected draft as read-only input.
- Never edit, delete or submit the source draft itself.

### Stage 2 — Order details

Display a compact order-entry form inspired by the first EasyTrader reference screenshot. Identify the selected instrument in the form title.

Show:

- Instrument name and symbol.
- BUY or SELL direction inherited from the selected draft.
- Quantity.
- Unit price.
- Commission.
- Total order value for one order.

Quantity and unit price are editable numeric inputs. Initialize them from the selected draft. Recalculate commission and total immediately whenever either value changes.

Use decimal-safe financial arithmetic and reproduce the verified Python reference calculation, including its rounding behavior and required instrument metadata. The recorded calculation is:

`Ceiling(quantity × (price × (1 + commission) + hidePrice) × (csize ?? 1))`

Do not replace instrument-specific commission or metadata with guessed or hardcoded values. If required metadata or the reference calculation cannot be verified, do not silently substitute a value; ask the PO.

The displayed total is for **one order only**. Do not calculate or display aggregate financial exposure across repeated attempts.

Explicitly exclude these controls and displays from this form:

- Current account assets or balance.
- Trading-validity selector.
- Quantity minimum/maximum controls.
- Price minimum/maximum controls.

The reference's fixed order-validity behavior remains an internal request-construction detail, not a user-editable field.

Break-even price is optional and is not required for this POC.

BUY is the initially validated live path. SELL drafts may be displayed with their inherited direction, but live SELL execution must remain disabled until its request contract is independently verified and the PO approves it.

Create a new order using the selected draft's data. Never submit, modify or delete the draft itself.

### Stage 3 — Dispatch timing

Provide editable inputs for:

- Start hour.
- Start minute.
- Start second.
- Dispatch duration in seconds.
- Minimum dispatch interval in microseconds.

Use these defaults:

| Setting | Default |
|---|---:|
| Start time | 08:44:58 |
| Duration | 5 seconds |
| Minimum interval | 350 microseconds |

Use the local Windows system clock. Do not require the user to enter Tehran time or manually synchronize another clock.

Show an approximate dispatch-attempt estimate derived from the configured duration and minimum interval. Label it clearly as an estimate. It is not a promise of throughput and must never be presented as the number of broker-accepted orders.

### Stage 4 — Final confirmation

Before dispatch, show a concise confirmation summary containing:

- Instrument.
- BUY/SELL direction.
- Quantity.
- Unit price.
- Commission.
- Total value per order.
- Local start time.
- Dispatch duration.
- Minimum interval.
- Approximate attempt count.

Provide the primary actions:

- `تأیید و شروع`
- `انصراف`

Explicitly warn that each dispatch is an independent order request and that multiple orders may be accepted or executed. Require deliberate user confirmation for every execution.

### Stage 5 — Countdown and dispatch

The execution engine must run independently of the Windows Forms UI. Ribbon callbacks and forms must not contain the dispatch loop or block on network operations.

- Use a high-resolution monotonic timing source for elapsed time and dispatch intervals.
- Use local system time to calculate the requested wall-clock start time.
- Display a live elapsed stopwatch and remaining-time countdown.
- Display the actual local dispatch-attempt count.
- Do not wait for a previous broker response before initiating the next scheduled request.
- Treat each scheduled POST as a separate independent order request, not a response-driven retry.
- Do not parse broker response bodies, classify broker acceptance/rejection, or reconcile broker order IDs in this POC.
- Do not automatically retry an individual attempt after a transport or ambiguous outcome.
- Stop initiating new requests when the configured dispatch window ends.
- User cancellation stops future dispatch attempts. It cannot recall requests already transmitted or orders already accepted by the broker.

#### Compact dispatch-log contract

The dispatch window must have fixed dimensions. Its height must not grow as records accumulate.

The log must:

- Render one compact line per locally initiated attempt.
- Show the local dispatch timestamp and sequential attempt number.
- Support vertical scrolling through all records.
- Avoid individual cards, record containers, multi-line panels and decorative boxes.
- Avoid verbose repeated text such as “dispatch number N started; broker response is not checked.”
- Avoid repeated explanatory messages for every attempt.
- Show locally detectable initiation failures, if any, as compact one-line records.

Example:

```text
08:44:58.000124 | #000001
08:44:58.000482 | #000002
08:44:58.000831 | #000003
08:44:58.001176 | #000004
```

The timestamp must represent the local dispatch event, not the time at which the UI happens to render the record.

The dispatch engine owns attempt numbers, timestamps and log records. The UI is a presentation consumer only. Collect records independently and update the UI in batches. Rendering, scrolling and text formatting must not throttle the dispatch schedule. Do not create one UI control per attempt.

The attempt counter represents locally initiated dispatch attempts only. It does not represent broker acceptance, execution or filled quantity.

### Stage 6 — Completion

When the configured dispatch window ends:

- Stop initiating new requests.
- Stop the countdown.
- Display final elapsed time.
- Display the actual locally initiated attempt count.
- Display locally detected initiation failures, when available.
- Do not invent broker acceptance, rejection or execution statistics.
- Freeze the completion window; only the Persian Close action remains enabled.
- Release local operation resources when the user closes the window.

Closing the local window does not cancel orders already accepted by Mofid.

## 7. Operational-state distinctions

Keep these concepts separate:

1. **Dispatch initiated:** the local application initiated an order transport request.
2. **Broker accepted:** the broker acknowledged acceptance.
3. **Executed:** a trade was actually filled.
4. **Unknown:** broker outcome was not inspected or reconciled.

This POC reports local dispatch activity only. Never label a locally initiated POST as a successful broker order, infer acceptance from HTTP initiation, or infer fills from the local attempt count.

## 8. Architecture and project ownership

Preserve D-025's existing four-project modular monolith. Do not create a fifth production project.

| Project | Responsibility for this feature |
|---|---|
| `Domain` | Pure trading concepts, order terms, invariants and financial calculations. No Excel, UI, HTTP or broker transport dependencies. |
| `Application` | Opening-order workflow, orchestration, dispatch scheduling, application-owned contracts, configuration and progress. No Mofid-specific transport implementation. |
| `Infrastructure` | Mofid authentication, session management, draft retrieval, instrument metadata, request construction, broker DTOs and HTTP transport. |
| `AddIn` | Excel-DNA Ribbon entry points, Persian Windows Forms, UI presentation and application composition. No trading calculations or dispatch scheduling loops. |

Preserve D-025's dependency direction:

- Domain references no other production project.
- Application may reference Domain.
- Infrastructure may reference Application and Domain.
- AddIn may reference Application and Infrastructure; direct Infrastructure use is restricted to composition/bootstrap.

Keep broker-specific DTOs and API details inside the Mofid adapter. Keep application contracts in the layer/use case that owns them. `AddInComposition` remains the composition root.

## 9. Implementation constraints

- Use the existing C#/.NET and Excel-DNA solution.
- Use the Windows Forms capability already enabled by the existing AddIn project. Do not introduce WPF or another UI framework without PO approval.
- Organize code feature-first within the four existing projects.
- Create folders and abstractions only when they contain meaningful implementation.
- Do not create global `Services`, `DTOs`, `Interfaces` or `Helpers` buckets.
- Do not create empty future-provider scaffolding.
- Do not move or rewrite the existing WorkbookJson feature.
- Keep all application logic independent of Excel COM.
- Never access Excel COM objects from background dispatch workers.
- Do not perform network calls or timing loops inside Ribbon callbacks or forms.
- Preserve existing workbook JSON behavior and existing tests.
- Use OOP, SOLID, type safety, nullable-reference safety and design patterns only where justified.
- Keep comments, identifiers, tests and developer diagnostics in English; keep user-facing UI in Persian.
- Do not add dependencies or change project boundaries without a concrete reason and PO approval.

## 10. Testing and verification

Automated tests are mandatory for every source change. Use deterministic fakes, mocks and sanitized fixtures. Tests must not send real orders or require live brokerage credentials.

Cover, as applicable:

- Draft mapping, row selection model and side preservation.
- Draft immutability and creation of a separate order request.
- Quantity/price editing and immediate recalculation.
- Commission, metadata, decimal precision and rounding.
- Missing or invalid instrument metadata.
- Request payload construction and BUY/SELL gating.
- Session reuse, expiry and reauthentication decisions.
- Timing defaults, local start-time calculation and configured dispatch window.
- Monotonic scheduling behavior and attempt counting.
- Cancellation and prevention of new attempts after cancellation/end time.
- Nonblocking dispatch initiation; a slow response must not serialize subsequent attempts.
- Compact log record formatting, ordering and timestamp semantics.
- UI batching, fixed-height log and vertical scrolling where testable.
- Separation of local dispatch from broker acceptance/execution.

Run the repository's actual build and test commands after inspecting the current solution and test projects. Report exact commands and observed results. Do not claim that environment-dependent Excel checks or live-account acceptance passed unless actually performed.

The PO performs the final local Excel and live-account acceptance separately.

## 11. Implementation sequence

1. Inspect current `main`, the existing source/test tree and relevant project files. Record the baseline and existing working-tree state.
2. Read the frozen Python reference without executing or modifying it. Verify its behavior against D-028 and identify unresolved details.
3. Verify the available Mofid authentication, draft, metadata and order-request contracts from evidence. Do not invent endpoints, payload fields or authentication behavior.
4. If a material API or product detail cannot be verified, stop and ask the PO before implementing that part.
5. Implement the smallest complete Domain/Application models and their tests.
6. Implement Mofid adapters, authentication/session handling and deterministic adapter tests.
7. Implement the Persian Windows Forms workflow and Ribbon entry points.
8. Implement the independent dispatch engine, countdown, attempt counter and compact scrollable log.
9. Run build and automated tests; inspect the final diff and verify the Python reference is unchanged.
10. Deliver all source changes uncommitted to the PO for local Excel and live-account acceptance.

## 12. Security, risks and limitations

- EasyTrader web APIs are private and undocumented; observed contracts may change.
- This decision does not establish Mofid's authorization of third-party API use or resolve applicable terms, legal or regulatory restrictions.
- Windows scheduling, operating-system load, network latency and broker processing cannot guarantee microsecond delivery, exact throughput or queue priority.
- Multiple independent requests may be accepted or executed and may create material financial exposure.
- Cancelling the local dispatch engine does not cancel broker-side orders.
- Do not expose credentials, account details, session tokens or private order data in repository fixtures or logs.
- The PO must independently review the broker's actual order list and remove unnecessary open orders after live acceptance testing.

## 13. Definition of done

- The Python reference is unchanged and has not been executed by Codex.
- Login and valid-session reuse work against the verified flow.
- Drafts can be selected by clicking and are not modified.
- The order form is initialized from the draft and recalculates totals correctly.
- Approved timing defaults and explicit final confirmation are present.
- Repeated dispatch does not wait for previous broker responses.
- Attempt counters represent locally initiated requests only.
- The log has one compact line per attempt, a fixed-height window and vertical scrolling.
- Log rendering does not throttle the dispatch engine.
- Completion freezes the window except for Close.
- Automated tests and build checks pass, or any environment limitation is reported accurately.
- The PO completes and accepts the local Excel/live-account E2E test before committing source.
