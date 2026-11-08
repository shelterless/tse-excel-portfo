# D-030 — Native HTTP Opening-Order Reference and Excel Port Alignment

- **Status:** Accepted
- **Date accepted:** 2026-11-08
- **Related decisions:** D-027, D-028, D-029
- **Authority:** This decision supplements D-028 for the Excel-hosted native-HTTP opening-order implementation. D-028 remains authoritative for the approved user workflow, order scope, financial safeguards, and four-project architecture.

## 1. Context and acceptance boundary

The Product Owner selected the reviewed native-HTTP Python POC in PR [#4](https://github.com/shelterless/tse-excel-portfo/pull/4), branch `codex/python-direct-http-transport`, reviewed head `3ce3729994f67b502ee765c0cb7b2da2740a2e29`, as the current behavioral reference for the Excel port.

The PO exercised its real live-request path. The supplied run observed nine HTTP 200 responses, all classified by the broker response as rejected, and no resulting orders appeared in Mofid. This exercises the live transport path but **does not establish broker acceptance, real-market opening-time acceptance, or queue priority**. The PO alone performs the later live-market acceptance.

## 2. Frozen Python reference assets

After PR #4 is merged, the current read-only behavioral reference is:

- `POC/easytrader_direct_http_poc.py`
- `POC/test_easytrader_direct_http_poc.py` (companion offline tests)

Codex may inspect these files but must not edit, format, rename, move, delete, execute, import, invoke, or copy them into the C# implementation. Do not run the Python script or its tests as part of the Excel port. Python is not a production, build, test, or deployment dependency.

The earlier `POC/easytrader_poc.py` remains an unchanged, read-only historical reference under D-028. Neither Python implementation may be modified as part of the Excel work.

## 3. Product objective

The objective is to make a valid order request reach Mofid at the earliest useful moment that the client can control, improving the chance of being near the front of the broker's queue.

The objective is **not** to maximize POST count, reproduce EasyTrader's UI, or build an EasyTrader replacement. More independent POSTs do not themselves improve queue position. The client cannot guarantee network arrival time, broker processing order, acceptance, or first place in the queue.

All D-028 scope and safety rules remain: one explicitly confirmed ordinary DAY BUY draft-derived order, immutable source draft, exact financial calculation and metadata validation, the existing per-order safety cap, and no live SELL.

## 4. Authentication boundary

- Use the existing legitimate, visible Chrome/Playwright interaction only to complete manual Mofid login, including MFA/CAPTCHA when requested.
- Observe the real authenticated API request and capture only the allowlisted authentication headers and applicable cookies evidenced by the Python reference.
- Do not bypass authentication, automate challenges, exchange tokens, copy browser fingerprints, export local/session storage, or persist a browser profile.
- Close the owned browser context, browser process, and Playwright runtime, and verify teardown before constructing/using the native API transport.
- **After login, no Chrome, Playwright, page, browser JavaScript, or browser `fetch` may be used for API reads, preflight, connection preparation, or order dispatch.**
- Keep the observed session material in memory only. Never put credentials, cookies, tokens, or authentication headers in workbook JSON or logs.

## 5. Native Mofid HTTP transport

All post-login Mofid API reads and order requests must use a native .NET HTTP transport against the fixed API origin evidenced by the reference:

`https://api-mts.orbis.easytrader.ir`

The observed read contracts are:

- `GET /easy/api/money`
- `GET /easy/api/draft`
- `POST /symbols/api/symbols/all` with the observed null-hash body
- `POST /symbols/api/marketdata/v2` with the selected ISIN

The independent order operation is:

- `POST /core/api/v2/order`

Preserve the observed request payload, exact decimal serialization, client origin/referer, allowlisted authentication headers, and applicable cookies. Verify every endpoint and field against the frozen reference and existing evidence; do not invent API behavior.

Use normal TLS certificate validation, a fixed-origin/path allowlist, bounded timeouts and connection capacity. Disable redirects and proxy fallback. Do not add automatic retries or hidden resilience retries. HTTP 200 alone is not broker acceptance.

## 6. Dispatch timing and concurrency

Use the D-028 defaults unless the PO changes them:

| Setting | Default |
|---|---:|
| Local Windows start time | 08:44:58 |
| Dispatch duration | 5 seconds |
| Minimum interval | 350 ms |
| Hard live minimum | 300 ms |

The live path must reject intervals below 300 ms. Do not silently clamp an invalid value.

- Use a monotonic high-resolution clock for dispatch spacing, elapsed time, and the exclusive cutoff. Use the local Windows clock only to resolve the requested wall-clock start.
- The next request is paced from the previous actual local native-HTTP handoff plus the configured interval. The interval is the only intentional inter-request delay; do not add response-driven waiting, browser-bridge round trips, arbitrary sleeps, or another scheduler delay.
- Initiate each request independently. A slow or unresolved response must not serialize the next eligible request.
- Observe HTTP and broker outcomes asynchronously, independently of the scheduler. Collect outstanding results after the initiation window; never wait for them before initiating the next scheduled request.
- Use bounded concurrency sized to the configured timeout, interval, and planned attempts, following the reference's bounded policy (maximum 16). Do not create an unbounded task/thread per attempt, an accumulating request backlog, or catch-up bursts. If no worker/connection is available at a scheduled instant, record a capacity skip rather than queueing a late request.
- Stop initiating at the exclusive cutoff, on user cancellation, authentication rejection, or broker throttling. Already handed-off requests cannot be recalled. Unknown outcomes must never be replayed automatically.
- Operating-system scheduling and network latency can overshoot requested times. Do not claim exact millisecond arrival or queue priority.

## 7. Connection preparation and final preflight order

Immediately before the requested dispatch window, use this order:

1. Warm the bounded native TCP/TLS connections in parallel, without sending an order or dummy HTTP request.
2. Run the final fresh read-only preflight using the native HTTP client.
3. Start order dispatch at the requested local target.

Keep the warmed dispatch capacity available through preflight. If preflight uses a connection that would otherwise be reserved for dispatch, ensure it is safely reusable or use a separate preflight connection/pool. A server-closed connection must not silently leave the dispatch pool cold. Test warmup failures, timeouts, connection closure, and pool capacity. If connection preparation or final preflight fails or finishes too late, fail closed and send no order POSTs.

The final preflight must retain D-028's verified draft, symbol identity/status, market price/quantity constraints, commission, minimum notional, buying-power, per-order safety-cap, and freshness checks. Do not add symbol trading-hour, trading-calendar, weekday, broker-session-date, or trading-window-overlap gates: these are explicitly excluded by the PO for this POC. The selected local start must still be valid and in the future, and the instrument must pass the verified buyability/market-state and financial checks.

## 8. Response observation and outcome semantics

The scheduler must not await a response. Each request may be observed in the background:

1. Local initiation is recorded when the native transport hands the request to the HTTP stack.
2. HTTP status and response timing are recorded when available.
3. A broker acknowledgement is classified only from the verified response shape. `isSuccessful=true` is accepted only with the expected valid acknowledgement identifier; `false` is rejected.
4. Timeout, transport failure, malformed acknowledgement, or missing response is unknown unless the verified contract proves otherwise.
5. Execution/fill remains unknown; do not infer it from acceptance.

Recognize only explicitly allowlisted, evidenced rejection categories. Never log raw broker messages or response bodies. HTTP 200 is not equivalent to acceptance. A 401/403 or 429 stops future dispatch; no automatic authentication fallback or replay occurs inside the dispatch window.

The existing in-app UI continues to report local dispatch attempts, not broker acceptance or fills. More detailed asynchronous outcomes belong in the local trace log, not a redesigned UI.

## 9. Workbook-adjacent trace logging

For the Excel implementation, create a separate, timestamped log file for each run in the same directory as the active workbook. Logging is **always enabled** in this phase.

- Resolve the active workbook's full path on Excel's UI thread and pass only the resulting path string into the workflow. Do not access Excel COM from background workers.
- Create and verify the log file before the first order POST. If the workbook is unsaved, the directory is unavailable, or the log cannot be created/written, stop before dispatch. Do not silently fall back to another directory.
- Record a run ID and timestamped stage events, authentication teardown, native read verification, TCP/TLS warmup, final preflight, requested start/cutoff, and completion/cancellation.
- For each scheduled attempt, record its sequence, target and actual local initiation timestamps, monotonic timestamp, actual gap from the previous initiation, local initiation/transport result, HTTP status, response duration, broker accepted/rejected/unknown classification when observed, and capacity skips.
- Use a background buffered writer so disk I/O and formatting never run on the dispatch scheduler or UI thread. Do not silently drop records. A logging failure stops future initiations; already initiated requests remain unresolved/owned and must not be replayed.
- Never write authentication headers, cookies, tokens, credentials, raw order payloads, raw response bodies/messages, account balances, or broker order IDs. Log only sanitized categories and timing/transport facts.
- Keep the existing compact in-app dispatch list as-is; the file log supplements it.
- A future JSON configuration option to enable/disable logging is deferred. Do not add that setting or change the existing workbook JSON schema in this task.

## 10. Excel UI and architecture constraints

- Preserve the existing Persian forms, controls, labels, dimensions, step sequence, and confirmation UX. No UI/UX redesign or new controls unless a safety-critical behavior cannot be delivered otherwise.
- Keep the current fixed-height, scrollable, batched in-app attempt list. Do not create one UI control per attempt.
- Keep the existing four-project architecture and dependency direction. Domain remains independent; Application owns workflow/scheduling contracts; Infrastructure owns Mofid authentication/native HTTP and file logging; AddIn owns Ribbon, forms, path capture, and composition.
- Keep Playwright and its packaged driver only because it is still used for legitimate interactive login. Remove its use from all post-login API reads and dispatch. Do not remove the login capability.
- Do not introduce a fifth project, VBA, WPF, a new dependency, broad refactoring, or changes to the existing WorkbookJson feature.
- Do not access Excel COM from HTTP, dispatch, or log-writer workers.

## 11. Required automated verification

Use deterministic fakes and loopback HTTP fixtures only. Never use live brokerage credentials or send real orders from automated tests.

At minimum test:

- Login capture of only allowlisted headers/cookies; complete browser/context/Playwright teardown before any native API request.
- No browser or Playwright use after authentication; all reads and order POSTs use native HTTP.
- Cookie/header propagation, fixed origin, TLS validation, no redirects/proxy fallback/retries, response-size and timeout handling, and sanitized failures.
- Exact draft, symbol, market, financial and payload validation; draft immutability; BUY-only behavior; no calendar/session/weekday/trading-time gate.
- 300 ms hard floor, 350 ms default, theoretical count, monotonic spacing, exclusive cutoff, cancellation, no catch-up, no backlog, and no response-driven serialization.
- Slow responses overlapping later request initiations; bounded concurrency and capacity skips; 401/403/429 stop behavior; unknown outcomes are never retried.
- TCP/TLS warmup occurs before final preflight and dispatch; no warmup HTTP request; warmed capacity survives preflight or a closed connection is detected and replaced before dispatch.
- Log path is beside the workbook; unsaved workbook/unwritable path fails before the first order POST; all required records are written; slow disk/UI rendering does not throttle dispatch; secrets and payloads are absent.
- Existing forms and UI contract tests remain unchanged or are updated only for necessary validation such as the 300 ms floor.

Run the actual .NET build and test projects available in the repository. Report exact commands/results and unrun checks. Tests must never call the Python reference. The PO alone performs local Excel and real-market acceptance after pulling the reviewed source.

## 12. Relationship to D-028

D-030 supplements D-028 and supersedes only the conflicting implementation details for this native-HTTP port: browser-backed API reads/dispatch after login, sequential browser-bridge initiation, the prohibition on observing broker acknowledgements in the background, and the absence of a workbook-adjacent trace file. All other D-028 product scope, Persian UI, draft immutability, BUY-only safeguards, exact financial rules, architecture, and PO-owned live acceptance remain in force.
