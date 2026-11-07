"""Disposable EasyTrader POC. Python 3.10+; no required packages for offline use.


Last Tested-OK: 

python POC/easytrader_poc.py --browser-single-order --live

Run in VS Code's terminal:
    python POC/easytrader_poc.py --self-test
    python POC/easytrader_poc.py
    python POC/easytrader_poc.py --login
    python POC/easytrader_poc.py --browser-login
    python POC/easytrader_poc.py --browser-login --mobile
    python POC/easytrader_poc.py --browser-login --mobile --open-chrome
    python POC/easytrader_poc.py --browser-token --mobile
    python POC/easytrader_poc.py --browser-read
    python POC/easytrader_poc.py --browser-drafts
    python POC/easytrader_poc.py --browser-draft-preview
    python POC/easytrader_poc.py --browser-draft-schedule 08:45:00
    python POC/easytrader_poc.py --browser-single-order 08:45:00
    python POC/easytrader_poc.py --browser-single-order --live
    python POC/easytrader_poc.py --live 08:45:00
    python POC/easytrader_poc.py --live 08:45:00 --mobile
    python POC/easytrader_poc.py --browser-order-contract
Leave credentials below unchanged to enter them interactively with --login.
Never commit real credentials. Cookies and tokens are held only in memory.
With --browser-login, use the generated URL in a separate private browser
window. Complete login and any challenge there. If the browser changes the
callback address, use DevTools Network with Preserve log enabled before login.
Paste the exact EasyTrader callback URL only into the masked local prompt.
Use --mobile to start the flow with the observed mobile callback. The
authorization request, callback and token exchange must use the same URI.
On Windows, --open-chrome opens the generated URL in a private Chrome window.
Use --browser-token [--mobile] to test the same read-only money request with
a token from the matching signed-in browser page. Paste it at the hidden
terminal prompt. The token is never logged or written to disk.
Append --compare-browser-token to --browser-login options to compare selected
JWT claims locally after an account HTTP 403. Only match results are reported.
The optional --browser-read mode uses Playwright and installed Chrome.
Sign in manually. The POC observes the mobile site's own money response.
With --browser-drafts, sign in to the desktop site and open Drafts if needed.
The report contains only draft response metadata and selected field names.
With --browser-draft-preview, select one or more listed drafts by number.
The terminal shows the selected details. The final report contains counts only.
With --browser-draft-schedule HH:MM:SS, enter today's Tehran time before
sign-in. The POC reads the desktop draft list and previews the whole snapshot
at the target time without asking for a selection.
With --browser-single-order [HH:MM:SS] [--mobile], preview ordinary BUY orders
from one saved draft and fresh symbol, market, calendar and money data.
Add --live to authorize repeated independent POSTs after Enter confirmation;
Esc cancels before dispatch. Default invocation remains read-only.
After verified login, the private window closes. Its session is transferred
only in memory to headless Chrome; subsequent requests retain Chrome's fetch
transport. No token, cookie or authentication state is written to a file.
Select a draft and confirm quantity/price, then enter local hour/minute/second
(defaults 08:44:58), duration (5 seconds) and dispatch gap (350 microseconds).
The countdown displays six fractional digits. Windows/Chrome/network timing
does not guarantee microsecond precision or broker arrival times.
At the target, each POST starts without awaiting/checking any response.
Each log line means a browser fetch was initiated, not broker acceptance.
At the cutoff queued HTTP work is aborted and the browser exits; accepted
orders are never cancelled. There is no automatic replay of a failed window.
The user checks outcomes and manages any extra orders in the real panel.
The draft is never changed/deleted. Reconciliation/fill tracking is omitted.
With --browser-order-contract, sign in manually to the desktop site. The POC
reports sanitized shapes of the site's order-list and server-time GETs.

Evidence from 2026-11-03 (observations, not an authenticated contract test):
* d.easytrader.ir main-ASDB7OPN.js and chunks CzUVj6D8 / Dgv-m_Jw:
  OIDC code + S256 PKCE; easy_pkce; scope and callback used below;
  GET /easy/api/money; GET /core/api/order; POST /core/api/v2/order.
* Public discovery and anonymous authorization returned HTTP 200 and /Login
  with POST primary_form, Username, Password, __RequestVerificationToken.
* The existing authenticated Chrome page exposed money/order/symbol requests
  and /symbols/api/TradingTime in its resource inventory. Response bodies,
  request headers and the MFA challenge were NOT available for inspection.
* Anonymous money GET returned HTTP 200 HTML titled WAF; symbols returned 401.
  HTML/200 is never accepted as an authenticated account response here.
* money.buyPowerT2 is consumed by the current frontend. Its runtime schema and
  this script's complete login flow still require the PO's local verification.

Public references inspected (not copied or treated as verified contracts):
https://github.com/Mahdi-mghs/AutoBuy-MofidBroker/blob/main/easy_api.py
https://github.com/RezaMahdaviiDev/mofid/tree/main/src/brokerages/easy/api
https://github.com/m-fazel/Sarkhati/blob/main/src/easy_trader.rs

The legacy login/read/rehearsal modes do not submit orders. The explicit --live
single-order workflow below implements the 2026-11-07 first-party contract:
POST symbols/all with {"hash":"null"} returns {symbols: [...], hash: ...} and
supplies buyCommission, hidePrice and csize; ordinary orderModelType
is 1, desktop orderFrom is 34 and mobile is 33. The frontend BUY formula is
ceil(quantity * (price * (1 + commission) + hidePrice) * (csize ?? 1)).
Fresh marketdata/v2, TradingTime and startsession reads validate price, state
and calendar. No live order is sent by self-tests, and no fill/status tracking
or broker-clock precision is claimed by this disposable single-order workflow.

RESUME CHECKPOINT -- 2026-11-03, PO requested continuation tomorrow:
* Only this file was created; no existing project files were changed. No Git
  commit/push/tag/PR, real credential test or order action was performed.
* Chrome access was recovered through the extension's exact tab binding:
  browser 2, tab 1844207140, URL https://d.easytrader.ir/. Reverify the current
  tab URL on resumption; do not assume these identifiers remain valid.
* The native Windows window path failed URL identification. The extension
  supports DOM/resource inventory but exposes no network headers/bodies.
  Do not use a native-window workaround without reliable URL identification.
* No frontend, custom login page, browser automation dependency, or persisted
  session is implemented. Default invocation is offline; --login is for PO use.
* Verification: --self-test passed all 9 isolated tests in 0.101s. The offline
  default stopped safely with placeholders, an empty request report and zero
  orders. No live authentication was tested. Network calls in tests are mocked.
* NEXT: continue from these findings, not a repeated public repository search.
  Obtain permitted, sanitized first-party login/MFA and read-only response
  shapes; keep tokens/cookies/credentials out of tool output and Git. The PO
  performs credential entry/testing locally. Do not log out the open session.
* Establish whether OTP has autocomplete=one-time-code and an anti-forgery
  field; otherwise the script deliberately stops. Confirm money response and
  any required startsession/same-login request before implementing it.
* Verify symbol-to-ISIN mapping, price/quantity steps/bounds, money units,
  current instrument/session/calendar rules, order payload, broker acceptance
  and status semantics. Submission stays unavailable until those are verified.
  Do not submit, edit or cancel orders during investigation. Any later live
  run belongs to the PO and requires the original explicit one-order controls.

2026-11-04: The actual console entry point reached the observed password form
anonymously (discovery 200, authorize 303, login HTML 200) and stopped before
reading credentials. Next, the PO runs --login in a local terminal and shares
only the STOP line, if present, and the final JSON request summary.
The PO's repeat run got HTML/200 with a CAPTCHA markup signal after posting
the password. The protection guard stopped before OTP or the money request.
The browser handoff keeps all login challenges in the official browser.
The official mobile flow reached m.easytrader.ir/auth-callback after MFA.
The PO observed that mobile redirect URI on the authorization request.
Use --browser-login --mobile for a fresh POC run with that URI. A callback
issued for the browser application's own login cannot be reused by the POC.
The PO's live mobile POC run passed discovery and token exchange (200 JSON).
The money GET returned 403 with response_kind "other". No order was attempted.
The mobile page's resource inventory showed the same money host and path.
The browser's money request returned 200 with the mobile Origin and Referer.
The POC now uses the selected callback's origin for both account headers.
The mobile page can show another sign-in form after the POC callback.
Use the first callback from the POC flow. Invalid pastes can be replaced
in the same terminal run before any token request is made.
The PO's 2026-11-04 live --browser-token --mobile run made one account GET.
It returned 200 JSON and passed the numeric buyPowerT2 check. Zero order
requests were sent. This verifies the money read with a browser-issued token.
The live PKCE run with the updated mobile headers exchanged its code
successfully, then got 403 (response_kind "other") on the same money GET.
The browser can show a second sign-in even when the first callback is valid.
The live comparison run reproduced the 403 after a 200 JSON token exchange.
The selected amr, aud, client_id, iss and scope claims matched. There were
no differences among the selected claims present in either token.
The reason for the different account results remains undetermined.
The PO's 2026-11-04 live --browser-read run observed the mobile application's
money response after manual sign-in. It returned HTTP 200 JSON and passed
the numeric buyPowerT2 check without a callback or token paste. Zero order
requests were sent.
The draft-only scope uses existing EasyTrader drafts selected by the user,
individually or as a group. The desktop Drafts tab and its order grid were
observed along with the /easy/api/draft resource path.
The PO prepared one test draft. A read-only check of the signed-in desktop
grid found exactly one row and matched its symbol, quantity and unit price
to the PO's input. No draft or order action was taken.
The PO's live draft read confirmed GET /easy/api/draft returned HTTP 200
JSON with a root array containing one draft. Its item exposed id, price,
quantity, side, symbolIsin, symbolName and validityType. The selection
preview uses that array and never submits the selected drafts.
The PO's live desktop group preview read two drafts and previewed exactly
those two selections with order_requests equal to zero. The browser grid
and API listed the two drafts in different orders, so row position is local
to each view. Group submission and per-draft outcomes remain unverified.
The scheduled rehearsal takes the target before sign-in and previews the
whole draft snapshot without a post-login prompt. It records the target
and actual preview times. It does not re-read the snapshot at the target.
The PO's live 2026-11-04 rehearsal selected two drafts as a group. Its
12:09:00 Tehran target and preview timestamps matched to the reported
millisecond, with zero order requests.
The intended group send uses a direct API call. The desktop UI click path
was removed. In the mobile Orders view, the PO identified the More menu,
Group Send dialog, and Select All. The final request contract is unverified.
"""

USERNAME = "xxxx"
PASSWORD = "xxxx"

SYMBOL = "xxxx"
QUANTITY = 0
PRICE = 0

TARGET_TIME = "08:45:00"
LIVE_ORDER_ENABLED = False  # Legacy toggle stays off; --live plus per-order approval is the explicit gate.
MAX_ORDER_VALUE_IRR = 5_000_000  # The new ordinary-order workflow caps the final value including fees.
NETWORK_TIMEOUT_SECONDS = 15

import base64
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_CEILING, localcontext
from dataclasses import dataclass
import getpass
import hashlib
from html.parser import HTMLParser
import http.cookiejar
import contextlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import warnings
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


LOGIN_ORIGIN = "https://login.emofid.com"
DESKTOP_ORIGIN = "https://d.easytrader.ir"
CALLBACK = DESKTOP_ORIGIN + "/auth-callback"
MOBILE_ORIGIN = "https://m.easytrader.ir"
MOBILE_CALLBACK = MOBILE_ORIGIN + "/auth-callback"
ACCOUNT_API_ORIGIN = "https://api-mts.orbis.easytrader.ir"
MONEY_URL = ACCOUNT_API_ORIGIN + "/easy/api/money"
DRAFT_URL = ACCOUNT_API_ORIGIN + "/easy/api/draft"
SYMBOLS_URL = ACCOUNT_API_ORIGIN + "/symbols/api/symbols/all"
# main-RMHHQAO7.jl/ei: POST {hash: "null"} for the uncached full symbol response.
# "null" is the frontend's literal string, not JSON null. The response is {symbols: [...], hash: ...}.
SYMBOLS_REQUEST_BODY = '{"hash":"null"}'
# First-party nV.GetMarketData: POST an ISIN array; this is a data read, not an order.
MARKET_DATA_URL = ACCOUNT_API_ORIGIN + "/symbols/api/marketdata/v2"
TRADING_TIME_URL = ACCOUNT_API_ORIGIN + "/symbols/api/TradingTime"
START_SESSION_URL = ACCOUNT_API_ORIGIN + "/easy/api/startsession"
ORDER_URL = ACCOUNT_API_ORIGIN + "/core/api/v2/order"
ORDERS_URL = ACCOUNT_API_ORIGIN + "/core/api/order"
LIVE_BLOCKER = "The global live toggle is unsupported. Use --live and confirm the displayed order window."
MAX_SYMBOL_RESPONSE_BYTES = 12_000_000
PREFLIGHT_LEAD_SECONDS = 5
MAX_PREFLIGHT_AGE_SECONDS = 15
MAX_SUBMISSION_LATENESS_SECONDS = 2
ORDER_RECONCILE_ATTEMPTS = 12  # Cover the frontend's five-second order refresh interval without another POST.
SCOPE = "easy2_api mts_api openid profile login_delegation-api"
MAX_RESPONSE_BYTES = 1_000_000
BROWSER_READ_TIMEOUT_MS = 300_000


class Blocked(Exception):
    """A safe, non-secret diagnostic suitable for printing."""


class BrowserTransportFailure(Blocked):
    """The authenticated browser did not produce an HTTP response."""


class DraftObservationTimeout(Blocked):
    """No matching first-party draft response arrived after manual login/navigation."""


class HttpResponseFailure(Blocked):
    """An actual HTTP response has a failing status or unexpected media type."""


def tehran_zone():
    try:
        return ZoneInfo("Asia/Tehran")
    except ZoneInfoNotFoundError:
        raise Blocked("Timezone data missing: run python -m pip install tzdata.") from None


def validate_order(symbol, quantity, price, limit):
    """Validate local intent only; never claim instrument identity is verified."""
    if not isinstance(symbol, str) or not symbol.strip() or symbol.strip() == "xxxx":
        raise Blocked("Set a non-placeholder SYMBOL for a local preview.")
    if len(symbol) > 40 or any(ord(c) < 32 for c in symbol):
        raise Blocked("Invalid symbol text.")
    if any(type(v) is not int or v <= 0 for v in (quantity, price, limit)):
        raise Blocked("QUANTITY, PRICE and value limit must be positive integers (IRR).")
    value = quantity * price
    if value > limit:
        raise Blocked("Order notional exceeds MAX_ORDER_VALUE_IRR.")
    return value


def tehran_target(now, target):
    """Today's Tehran target only: never silently roll into the next day."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise Blocked("An aware timestamp is required.")
    if not isinstance(target, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d", target):
        raise Blocked("TARGET_TIME must be HH:MM:SS in Asia/Tehran.")
    local = now.astimezone(tehran_zone())
    hour, minute, second = map(int, target.split(":"))
    scheduled = local.replace(hour=hour, minute=minute, second=second, microsecond=0)
    if scheduled < local:
        raise Blocked("Today's target time has passed; no next-day scheduling.")
    return scheduled


def seconds_until_target(now, target):
    return (tehran_target(now, target) - now).total_seconds()


def require_read_only_mode():
    if LIVE_ORDER_ENABLED is not False:
        raise Blocked(LIVE_BLOCKER)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Forms(HTMLParser):
    """Read actual server forms; never synthesize an MFA endpoint or field name."""

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.forms = []
        self.current = None
        self.captcha_markup = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("input", "iframe", "div", "textarea"):
            labels = " ".join(attrs.get(key) or "" for key in ("id", "name", "class", "title"))
            if "data-sitekey" in attrs or re.search(r"captcha|turnstile", labels, re.I):
                self.captcha_markup = True
        if tag == "form":
            self.current = {"attrs": attrs, "inputs": [], "unsupported": False}
            self.forms.append(self.current)
        elif self.current is not None:
            if tag == "input":
                self.current["inputs"].append(attrs)
            elif tag in ("select", "textarea") or (tag == "button" and attrs.get("name")):
                self.current["unsupported"] = True

    def handle_endtag(self, tag):
        if tag == "form":
            self.current = None


def parse_login_form(html, url, *, otp=False, report=None):
    page = Forms(html)
    signals = []
    if re.search(r"<title>\s*WAF\s*</title>", html, re.I):
        signals.append("waf_title")
    if page.captcha_markup:
        signals.append("captcha_markup")
    elif re.search(r"captcha|turnstile", html, re.I):
        signals.append("captcha_reference")
    if signals:
        if report:
            report[-1]["protection_signals"] = signals
        raise Blocked("Authentication protection signal (" + ", ".join(signals) + "). Continue in the official browser.")
    candidates = []
    password_form_seen = False
    for form in page.forms:
        inputs = form["inputs"]
        visible = [i for i in inputs if i.get("type", "text").lower() not in ("hidden", "submit", "button")]
        names = [i.get("name") for i in visible]
        password_form = (
            form["attrs"].get("id") == "primary_form"
            and len(names) == 2
            and set(names) == {"Username", "Password"}
        )
        password_form_seen = password_form_seen or password_form
        if otp:
            # Only a challenge explicitly marked by the server as one-time-code.
            matches = len(visible) == 1 and visible[0].get("autocomplete") == "one-time-code"
        else:
            matches = password_form
        if matches:
            candidates.append((form, visible))
    if otp and not candidates and password_form_seen:
        raise Blocked("The server returned the password form again after submission. Check the result in the official login flow.")
    if len(candidates) != 1:
        raise Blocked("Expected login/OTP form not observed. MFA field, action and response contract remain unverified.")
    form, visible = candidates[0]
    if any(not field.get("name") for field in visible):
        raise Blocked("Authentication input has no server-supplied name.")
    action = urllib.parse.urljoin(url, form["attrs"].get("action", url))
    parsed = urllib.parse.urlsplit(action)
    if (parsed.scheme, parsed.netloc) != ("https", "login.emofid.com") or parsed.fragment:
        raise Blocked("Login form action is not on the verified HTTPS login origin.")
    if form["attrs"].get("method", "get").lower() != "post" or form["unsupported"]:
        raise Blocked("Unsupported authentication form; refusing to guess its submission contract.")
    fields = {}
    for field in form["inputs"]:
        name = field.get("name")
        if not name:
            continue
        if name in fields or "disabled" in field or field.get("type", "text") in ("submit", "button"):
            raise Blocked("Ambiguous authentication form fields.")
        fields[name] = field.get("value", "")
    if not fields.get("__RequestVerificationToken"):
        raise Blocked("Expected anti-forgery field missing; authentication stopped.")
    return action, fields, visible


def check_request_target(url, method, bearer):
    parsed = urllib.parse.urlsplit(url)
    login = parsed.scheme == "https" and parsed.netloc == "login.emofid.com"
    account = url == MONEY_URL and method == "GET"
    if parsed.fragment or not (login or account) or (bearer is not None and not account):
        raise Blocked("Request blocked by the read-only endpoint allowlist.")


def request(opener, url, report, stage, *, fields=None, bearer=None, account_origin=DESKTOP_ORIGIN):
    method = "GET" if fields is None else "POST"
    check_request_target(url, method, bearer)
    headers = {"Accept": "application/json, text/html;q=0.9"}
    body = None
    if fields is not None:
        body = urllib.parse.urlencode(fields).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if bearer is not None:
        headers.update({"Authorization": "Bearer " + bearer,
                        "Origin": account_origin, "Referer": account_origin + "/"})
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    entry = {"stage": stage, "request_start": datetime.now(tehran_zone()).isoformat(timespec="milliseconds"),
             "response_arrival": None, "http_status": None, "response_kind": None}
    report.append(entry)
    started = time.perf_counter()
    try:
        try:
            response = opener.open(req, timeout=NETWORK_TIMEOUT_SECONDS)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            entry["response_arrival"] = datetime.now(tehran_zone()).isoformat(timespec="milliseconds")
            entry["http_status"] = response.code
            media_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            entry["response_kind"] = {"application/json": "json", "text/html": "html"}.get(media_type, "other")
            data = response.read(MAX_RESPONSE_BYTES + 1)
            if len(data) > MAX_RESPONSE_BYTES:
                raise Blocked("Response exceeded the size limit.")
            return response.code, response.headers, data
    except (OSError, urllib.error.URLError, TimeoutError):
        # Exception strings may contain callback URLs or other sensitive data.
        raise Blocked("Network/TLS/timeout failure; no retries were attempted.") from None
    finally:
        entry["total_ms"] = round((time.perf_counter() - started) * 1000, 2)


def follow_auth(opener, url, report, stage, *, fields=None):
    for _ in range(10):
        if urllib.parse.urlsplit(url)[:2] == urllib.parse.urlsplit(CALLBACK)[:2] and urllib.parse.urlsplit(url).path == "/auth-callback":
            return url, None
        status, headers, body = request(opener, url, report, stage, fields=fields)
        if status in (301, 302, 303):
            location = headers.get("Location")
            if not location:
                raise Blocked("Authentication redirect has no Location.")
            url = urllib.parse.urljoin(url, location)
            fields = None  # Never replay credentials on redirects.
            continue
        if status != 200 or "text/html" not in headers.get("Content-Type", "").lower():
            raise Blocked("Unexpected authentication HTTP status or content type.")
        return url, body.decode("utf-8", errors="strict")
    raise Blocked("Authentication redirect limit reached.")


def json_response(status, headers, body):
    if status != 200 or "application/json" not in headers.get("Content-Type", "").lower():
        raise Blocked("Expected HTTP 200 with an application/json response.")
    try:
        data = json.loads(body, parse_float=Decimal)
    except (ValueError, UnicodeError):
        raise Blocked("Invalid JSON response.") from None
    if not isinstance(data, dict) or not data or "error" in data or data.get("isSuccessful") is False:
        raise Blocked("Unexpected/error JSON response.")
    return data


def password_login(opener, authorize_url, report):
    url, html = follow_auth(opener, authorize_url, report, "authorize")
    if html is None:
        raise Blocked("Unexpected existing login in a fresh in-memory session.")
    action, fields, _ = parse_login_form(html, url, report=report)
    fields["Username"] = input("Username (not saved): ").strip() if USERNAME == "xxxx" else USERNAME
    fields["Password"] = getpass.getpass("Password (not saved): ") if PASSWORD == "xxxx" else PASSWORD
    if not fields["Username"] or not fields["Password"]:
        raise Blocked("Empty credentials; no login submission.")
    url, html = follow_auth(opener, action, report, "password", fields=fields)
    fields.clear()
    if html is None:
        return url

    action, fields, visible = parse_login_form(html, url, otp=True, report=report)
    print("Server supplied an OTP form; this branch has not been verified with a real account.")
    otp = input("Actual OTP for this challenge (not saved): ").strip()
    if not re.fullmatch(r"[0-9]{6}", otp):
        raise Blocked("Expected one actual six-digit OTP. No retry.")
    fields[visible[0]["name"]] = otp
    url, html = follow_auth(opener, action, report, "otp", fields=fields)
    if html is not None:
        raise Blocked("MFA did not reach the callback; no retry or additional challenge is attempted.")
    return url


def open_private_chrome(authorize_url):
    for root_name in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        root = os.environ.get(root_name)
        if not root:
            continue
        executable = Path(root) / "Google" / "Chrome" / "Application" / "chrome.exe"
        if executable.is_file():
            try:
                subprocess.Popen(
                    [str(executable), "--incognito", "--new-window", authorize_url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except OSError:
                continue
            return True
    return False


def callback_code(url, redirect_uri, state):
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        raise Blocked("Malformed callback URL.") from None
    if parsed._replace(query="", fragment="").geturl() != redirect_uri or parsed.fragment:
        raise Blocked(f"Expected the callback for this run: {redirect_uri}")
    query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    if query.get("state") != [state]:
        raise Blocked("The callback state does not match this run.")
    if "error" in query:
        raise Blocked("The login server returned an authorization error.")
    codes = query.get("code", [])
    if len(codes) != 1 or not codes[0]:
        raise Blocked("The callback is missing a single authorization code.")
    return codes[0]


def read_hidden(prompt):
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        try:
            return getpass.getpass(prompt).strip()
        except getpass.GetPassWarning:
            raise Blocked("A terminal with hidden input is required. Run in the VS Code terminal.") from None


def browser_callback(authorize_url, redirect_uri, state, *, open_chrome=False):
    if open_chrome and open_private_chrome(authorize_url):
        print("Opened this run's authorization URL in a private Chrome window.")
    else:
        if open_chrome:
            print("Chrome could not be launched automatically.")
        print("Open this authorization URL in a separate private Chrome window:")
        print(authorize_url)
    print("Complete the official sign-in and any CAPTCHA or OTP in Chrome.")
    print("Enable Network > Preserve log before sign-in to find the auth-callback request if the address changes.")
    print(f"Expected callback: {redirect_uri}")
    print("If Chrome shows another sign-in form after MFA, use the first callback from Network.")
    print("The callback contains a one-time code. Paste it only into the masked local prompt.")
    print("The paste is hidden. Press Enter after pasting.")
    while True:
        url = read_hidden("Full EasyTrader callback URL (hidden): ")
        try:
            return callback_code(url, redirect_uri, state)
        except Blocked as exc:
            print(f"Callback rejected: {exc}")
            print("Copy the callback from this run's Chrome window and try again, or press Ctrl+C to cancel.")


def read_browser_access_token(account_origin):
    print(f"Use the Authorization header from a signed-in EasyTrader request on {account_origin}.")
    print("Paste only into this hidden prompt and press Enter.")
    access = read_hidden("Browser Bearer access token (hidden): ")
    if access.lower().startswith("bearer "):
        access = access[7:].strip()
    return access


def token_claims_for_comparison(access):
    # These unverified claims are for diagnostics only.
    if len(access) > 16384 or access.count(".") != 2:
        return None
    payload = access.split(".")[1]
    try:
        claims = json.loads(base64.b64decode(payload + "=" * (-len(payload) % 4), altchars=b"-_", validate=True))
    except (ValueError, RecursionError):
        return None
    if not isinstance(claims, dict):
        return None
    selected = {}
    for name in ("iss", "aud", "scope", "client_id", "azp", "amr", "acr"):
        value = claims.get(name)
        if isinstance(value, str):
            selected[name] = frozenset(value.split()) if name == "scope" else frozenset((value,))
        elif isinstance(value, list) and all(isinstance(item, str) for item in value):
            selected[name] = frozenset(value)
    return selected


def compare_token_claims(pkce_access, browser_access):
    pkce = token_claims_for_comparison(pkce_access)
    browser = token_claims_for_comparison(browser_access)
    if pkce is None or browser is None:
        return {"status": "claims-unavailable"}
    return {
        "status": "compared",
        "same": sorted(key for key in pkce.keys() & browser.keys() if pkce[key] == browser[key]),
        "different": sorted(key for key in pkce.keys() & browser.keys() if pkce[key] != browser[key]),
        "pkce_only": sorted(pkce.keys() - browser.keys()),
        "browser_only": sorted(browser.keys() - pkce.keys()),
    }


def read_money(report, access, account_origin, *, compare_browser_token=False):
    require_read_only_mode()
    if not isinstance(access, str) or len(access) > 16384 or not re.fullmatch(r"[A-Za-z0-9._~+/-]+=*", access):
        raise Blocked("Expected Bearer access token missing or malformed.")
    # A fresh opener prevents login-origin cookies from being reused for API calls.
    account_opener = urllib.request.build_opener(NoRedirect())
    status, headers, body = request(account_opener, MONEY_URL, report, "account-read",
                                    bearer=access, account_origin=account_origin)
    if status == 403 and compare_browser_token:
        print("Account read returned HTTP 403. Paste a browser token for a local comparison, or press Enter to skip.")
        browser_access = read_browser_access_token(account_origin)
        if browser_access:
            report[-1]["token_claim_comparison"] = compare_token_claims(access, browser_access)
    check_money_response(status, headers, body)


def parse_buying_power(status, headers, body):
    try:
        account = json_response(status, headers, body)
    except Blocked as exc:
        raise Blocked(f"Account read failed (HTTP {status}): {exc}") from None
    buying_power = account.get("buyPowerT2")
    if type(buying_power) not in (int, Decimal) or not Decimal(buying_power).is_finite() or buying_power < 0:
        raise Blocked("Money JSON lacks the expected numeric buyPowerT2 field; account verification incomplete.")
    return buying_power


def check_money_response(status, headers, body):
    parse_buying_power(status, headers, body)
    print("Authenticated money read returned the expected field. No account values or tokens are printed.")
    print("OMS session readiness and all trading contracts remain unverified; trading remains unavailable.")


def observe_draft_reads(context, page, last_read, *, scheduled_at=None, manual_tab=False, session=None,
                        origin=DESKTOP_ORIGIN):
    def match_drafts(response):
        url = urllib.parse.urlsplit(response.url)
        if response.from_service_worker or url._replace(query="", fragment="").geturl() != DRAFT_URL:
            return False
        method = response.request.method
        if method not in ("GET", "POST"):
            return False
        media_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        last_read.update(stage="browser-draft-read", origin=ACCOUNT_API_ORIGIN, path="/easy/api/draft",
                         method=method, http_status=response.status,
                         response_kind={"application/json": "json", "text/html": "html"}.get(media_type, "other"))
        # Once authenticated, an HTTP error is a concrete response, not an observation timeout.
        if (session is not None and method == "GET" and session.authenticated and
                (response.status != 200 or media_type != "application/json")):
            return True
        return method == "GET" and response.status == 200 and media_type == "application/json"

    timeout_ms = BROWSER_READ_TIMEOUT_MS
    if scheduled_at is None or manual_tab:
        print("Complete login/MFA in Chrome, then open Orders > Drafts in that SAME window.")
        print("Waiting for the site's draft response automatically; do not press Enter in the terminal.")
    if scheduled_at is not None:
        remaining_ms = int((scheduled_at - datetime.now(tehran_zone())).total_seconds() * 1000)
        if remaining_ms <= 0:
            raise Blocked("Target time passed before the browser could observe drafts.")
        timeout_ms = min(timeout_ms, remaining_ms)
    try:
        with context.expect_event("response", predicate=match_drafts, timeout=timeout_ms) as observed:
            page.goto(origin + "/", wait_until="commit", timeout=min(30_000, timeout_ms))
            if scheduled_at is not None and not manual_tab:
                page.locator('[data-cy="order-grid-tab-draft-order"]').click(timeout=timeout_ms)
    except Exception as exc:
        if session is None:
            raise
        failure = session.last_failure("GET", DRAFT_URL)
        if failure:
            raise BrowserTransportFailure(f"Draft observation: {failure}") from None
        if last_read.get("http_status") not in (None, 200):
            raise HttpResponseFailure(f"Draft observation: HTTP {last_read['http_status']} from GET /easy/api/draft.") from None
        if type(exc).__name__ == "TimeoutError":
            raise DraftObservationTimeout("Draft observation timed out: no successful draft response after login/MFA and Orders > Drafts.") from None
        raise BrowserTransportFailure("Draft observation: " + sanitized_exception(exc)) from None
    if session is not None:
        session.capture_response_auth(observed.value)
        if (observed.value.status != 200 or
                observed.value.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json"):
            raise HttpResponseFailure(f"Draft observation: HTTP {observed.value.status} from GET /easy/api/draft.")
    body = observed.value.body()
    if len(body) > MAX_RESPONSE_BYTES:
        raise Blocked("Browser draft response exceeded the size limit.")
    try:
        payload = json.loads(body, parse_float=Decimal)
    except (ValueError, RecursionError):
        raise Blocked("The browser draft response contains invalid JSON.") from None
    known_fields = {"data", "result", "items", "orders", "drafts", "draftOrders", "isSuccessful",
                    "id", "draftId", "orderId", "symbolIsin", "symbolName", "side", "price",
                    "quantity", "status", "validityType"}
    if isinstance(payload, list):
        collections = {"root": payload}
        shape = {"root_type": "array"}
    elif isinstance(payload, dict):
        collections = {name: payload[name] for name in known_fields & payload.keys()
                       if isinstance(payload[name], list)}
        shape = {"root_type": "object", "known_fields": sorted(known_fields & payload.keys())}
    else:
        raise Blocked("The browser draft JSON is neither an object nor an array.")
    shape["collections"] = {
        name: {"count": len(items),
               "known_item_fields": sorted(known_fields & items[0].keys()) if items and isinstance(items[0], dict) else []}
        for name, items in collections.items()
    }
    last_read["json_shape"] = shape
    print("Browser draft response observed. The report contains only metadata and selected field names.")
    if session is not None:
        if not isinstance(payload, list):
            raise Blocked("Expected the proven root draft array.")
        session.seed_drafts(payload)
    return payload


def draft_details(payload):
    if not isinstance(payload, list):
        raise Blocked("Expected the observed draft array before previewing a selection.")
    details = []
    draft_ids = set()
    for draft in payload:
        if not isinstance(draft, dict):
            raise Blocked("Unexpected item in the draft array.")
        draft_id = draft.get("id")
        if (type(draft_id) not in (int, str) or not str(draft_id).strip()
                or str(draft_id) in draft_ids):
            raise Blocked("Draft identifiers are missing or ambiguous.")
        draft_ids.add(str(draft_id))
        symbol = draft.get("symbolName")
        quantity = draft.get("quantity")
        price = draft.get("price")
        side = draft.get("side")
        if (not isinstance(symbol, str) or len(symbol) > 80 or not symbol.strip()
                or not symbol.replace("\u200c", "").isprintable()
                or type(quantity) is not int or quantity <= 0
                or type(price) not in (int, Decimal) or not Decimal(price).is_finite() or price <= 0
                or type(side) not in (int, str) or len(str(side)) > 24 or not str(side).isprintable()):
            raise Blocked("Draft details do not match the expected preview fields.")
        details.append(f"{symbol} | Quantity: {quantity} | Unit price: {price} | Side (broker value): {side}")
    return details


def preview_draft_selection(payload, report, *, scheduled_at=None):
    details = draft_details(payload)
    if not details:
        print("No drafts are available to preview.")
        return
    entry = {"stage": "draft-preview"}
    if scheduled_at is None:
        print("Drafts available for a local preview:")
        for index, detail in enumerate(details, start=1):
            print(f"  {index}. {detail}")
        selection = input("Draft number(s), separated by commas. Enter alone cancels: ").strip()
        if not selection:
            print("Draft preview cancelled.")
            return
        entries = [part.strip() for part in selection.replace("،", ",").split(",")]
        if any(not part.isdecimal() or len(part) > 10 for part in entries):
            raise Blocked("Enter one or more listed draft numbers.")
        indexes = [int(part) for part in entries]
        if len(set(indexes)) != len(indexes) or any(index < 1 or index > len(details) for index in indexes):
            raise Blocked("Draft numbers must be distinct and within the displayed list.")
    else:
        now = datetime.now(tehran_zone())
        delay = (scheduled_at - now).total_seconds()
        if delay < 0:
            raise Blocked("Target time passed before drafts were ready.")
        indexes = range(1, len(details) + 1)
        print(f"Waiting until {scheduled_at.isoformat()} to preview all {len(details)} drafts.")
        while delay > 0:
            time.sleep(min(delay, 60))
            now = datetime.now(tehran_zone())
            delay = (scheduled_at - now).total_seconds()
        entry.update(target_time=scheduled_at.isoformat(timespec="milliseconds"),
                     preview_time=now.isoformat(timespec="milliseconds"))

    mode = "single" if scheduled_at is None and len(indexes) == 1 else "group"
    print(f"Dry-run {mode} preview ({len(indexes)} selected):")
    for index in indexes:
        print(f"  {index}. {details[index - 1]}")
    entry.update(mode=mode, selected_count=len(indexes))
    report.append(entry)


def rehearse_single_order(payload, buying_power, scheduled_at, report):
    if datetime.now(tehran_zone()) >= scheduled_at:
        raise Blocked("Target time passed before draft selection.")
    details = draft_details(payload)
    if not details:
        raise Blocked("No draft is available for a single-order rehearsal.")
    for index, detail in enumerate(details, start=1):
        print(f"  {index}. {detail}")
    selection = input("One draft number, or Enter to cancel: ").strip()
    if not selection:
        print("Single-order rehearsal cancelled.")
        return
    if len(selection) > 10 or not selection.isdecimal() or not 1 <= int(selection) <= len(details):
        raise Blocked("Select exactly one listed draft number.")
    draft = payload[int(selection) - 1]
    symbol, quantity, price = draft["symbolName"], draft["quantity"], draft["price"]
    correction = input(f"BUY quantity [{quantity}]. Enter keeps the draft quantity: ").strip()
    if correction:
        if len(correction) > 10 or not correction.isdecimal() or int(correction) <= 0:
            raise Blocked("Quantity must be a positive whole number of up to 10 digits.")
        quantity = int(correction)

    # Draft price units still require verification. Apply the IRR cap locally
    # under the rehearsal assumption that the draft price is in IRR.
    if price > MAX_ORDER_VALUE_IRR:
        raise Blocked("Order notional exceeds MAX_ORDER_VALUE_IRR under the rehearsal's draft-price assumption.")
    if price != int(price):
        raise Blocked("A whole-number draft price is required for the local IRR cap check.")
    price = int(price)
    notional = validate_order(symbol, quantity, price, MAX_ORDER_VALUE_IRR)
    print(f"Local BUY intent: {symbol} | Quantity: {quantity} | Draft price: {price} | "
          f"Notional: {notional} (assuming draft price is in IRR for the local cap).")
    print("Today's verified upper price is unavailable. The rehearsal keeps the draft price.")
    if buying_power is None:
        print("No valid money snapshot was observed alongside the draft read.")
    else:
        print("A numeric buying-power field was observed. Its units and applicable fees remain unverified.")
    print("Warning: Broker clock unverified. Offset and uncertainty are unavailable.")
    print("Live arming blocked. Instrument rules, funds including fees, broker time, "
          "and the order and status contracts require verification.")
    entry = {
        "stage": "single-order-rehearsal",
        "selected_count": 1,
        "target_time": scheduled_at.isoformat(),
        "funds_check": "UNVERIFIED",
        "broker_clock": {"status": "UNVERIFIED", "offset_ns": None, "uncertainty_ns": None},
        "live_armed": False,
    }
    report.append(entry)
    if buying_power == 0:
        entry["funds_check"] = "ZERO_REPORTED"
        raise Blocked("The observed buying-power field was zero.")

    if datetime.now(tehran_zone()) >= scheduled_at:
        raise Blocked("Target time passed before the rehearsal could be confirmed.")
    if input(f"Type REHEARSE to time this local BUY preview at {scheduled_at.isoformat()}: ").strip() != "REHEARSE":
        print("Single-order rehearsal cancelled.")
        return
    target_ns = int(scheduled_at.timestamp()) * 1_000_000_000
    started_ns = time.time_ns()
    started_counter_ns = time.perf_counter_ns()
    if started_ns >= target_ns:
        raise Blocked("Target time passed before confirmation completed.")
    delay_ns = target_ns - started_ns
    elapsed_ns = time.perf_counter_ns() - started_counter_ns
    while elapsed_ns < delay_ns:
        time.sleep(min((delay_ns - elapsed_ns) / 1_000_000_000, 60))
        elapsed_ns = time.perf_counter_ns() - started_counter_ns
    preview_ns = time.time_ns()
    entry.update(local_target_unix_ns=target_ns, local_start_unix_ns=started_ns, local_preview_unix_ns=preview_ns,
                 elapsed_monotonic_ns=elapsed_ns, local_target_delta_ns=preview_ns - target_ns)
    print(f"Dry-run BUY preview: {symbol} | Quantity: {quantity} | Draft price: {price}.")


def observe_order_contract(context, page, report, browser_error):
    snapshots = {}
    order_path = "/core/api/order"
    clock_path = "/easy/api/account/server-time/{client-ms}"

    def collect(response):
        if response.request.method != "GET" or response.from_service_worker:
            return False
        url = urllib.parse.urlsplit(response.url)
        if (url.scheme, url.netloc) != ("https", "api-mts.orbis.easytrader.ir"):
            return False
        path = url.path
        if re.fullmatch(r"/easy/api/account/server-time/[0-9]+", path):
            path = clock_path
        if path in (order_path, clock_path):
            snapshots.setdefault(path, response)
        return len(snapshots) == 2

    def field_types(data, fields):
        return {field: type(data[field]).__name__ for field in fields if field in data}

    print("Waiting for the desktop site's order list and server time. Open Orders if needed.")
    try:
        with context.expect_event("response", predicate=collect, timeout=BROWSER_READ_TIMEOUT_MS):
            page.goto(DESKTOP_ORIGIN + "/", wait_until="commit", timeout=30_000)
    finally:
        for path, response in snapshots.items():
            media_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
            entry = {"stage": "browser-order-contract", "method": "GET", "path": path,
                     "http_status": response.status, "json_object": False}
            report.append(entry)
            if response.status != 200 or media_type != "application/json":
                continue
            try:
                body = response.body()
                if len(body) > MAX_RESPONSE_BYTES:
                    continue
                data = json.loads(body, parse_float=Decimal)
            except (browser_error, ValueError, RecursionError):
                continue
            if not isinstance(data, dict):
                continue
            entry["json_object"] = True
            if path == clock_path:
                entry["field_types"] = field_types(data, ("serverTimestamp", "diff"))
            else:
                entry["field_types"] = field_types(data, ("orders", "algoSuffixCharacters"))
                orders = data.get("orders")
                if isinstance(orders, list) and orders and isinstance(orders[0], dict):
                    entry["first_order_field_types"] = field_types(
                        orders[0], ("id", "symbolIsin", "side", "price", "quantity", "orderState", "trades"))


def observe_browser(report, *, draft_discovery=False, scheduled_at=None, single_order=False, order_contract=False):
    require_read_only_mode()
    try:
        from playwright.sync_api import Error, TimeoutError as BrowserTimeout, sync_playwright
    except ImportError:
        raise Blocked("Browser read requires Playwright. Run: python -m pip install playwright") from None

    last_read = {}
    money_read = {}

    def match_money(response):
        if response.request.method != "GET" or response.from_service_worker:
            return False
        url = urllib.parse.urlsplit(response.url)
        if url._replace(query="", fragment="").geturl() != MONEY_URL:
            return False
        content_type = response.headers.get("content-type", "")
        media_type = content_type.split(";", 1)[0].strip().lower()
        money_read.update(
            stage="browser-account-read",
            response_arrival=datetime.now(tehran_zone()).isoformat(timespec="milliseconds"),
            http_status=response.status,
            response_kind={"application/json": "json", "text/html": "html"}.get(media_type, "other"),
        )
        return response.status == 200 and media_type == "application/json"

    money_snapshot = None

    def capture_money(response):
        nonlocal money_snapshot
        if money_snapshot is None and match_money(response):
            money_snapshot = response

    def money_response(response):
        body = response.body()
        if len(body) > MAX_RESPONSE_BYTES:
            raise Blocked("Browser money response exceeded the size limit.")
        return response.status, {"Content-Type": response.headers.get("content-type", "")}, body

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="chrome", headless=False)
            try:
                context = browser.new_context()
                page = context.new_page()
                print("Sign in manually in the Chrome window. Complete any Authenticator challenge there.")
                if order_contract:
                    return observe_order_contract(context, page, report, Error)
                if single_order:
                    context.on("response", capture_money)
                    payload = observe_draft_reads(context, page, last_read, scheduled_at=scheduled_at, manual_tab=True)
                    buying_power = None
                    if money_snapshot is not None:
                        try:
                            buying_power = parse_buying_power(*money_response(money_snapshot))
                        except (Blocked, Error, RecursionError):
                            money_read["money_field"] = "UNVERIFIED"
                        else:
                            money_read["money_field"] = "NUMERIC"
                    return payload, buying_power
                if draft_discovery:
                    return observe_draft_reads(context, page, last_read, scheduled_at=scheduled_at)
                print("Waiting up to five minutes for the mobile site's own money response.")
                with context.expect_event("response", predicate=match_money, timeout=BROWSER_READ_TIMEOUT_MS) as observed:
                    page.goto(MOBILE_ORIGIN + "/market-watch", wait_until="commit", timeout=30_000)
                check_money_response(*money_response(observed.value))
            finally:
                if browser.is_connected():
                    browser.close()
    except BrowserTimeout:
        if order_contract:
            raise Blocked("Timed out observing order-list and server-time GETs. See the sanitized report.") from None
        if draft_discovery or single_order:
            raise Blocked("Timed out waiting for a draft GET with HTTP 200 JSON. See the sanitized report.") from None
        if money_read:
            raise Blocked("Timed out waiting for HTTP 200 JSON from the browser money request.") from None
        raise Blocked("Timed out before a browser money response was observed.") from None
    except Error:
        raise Blocked("Chrome or browser observation failed. Check that Google Chrome is installed.") from None
    finally:
        if last_read:
            report.append(last_read)
        if money_read:
            report.append(money_read)


def authenticate_and_check(report, *, browser_redirect=None, open_chrome=False, compare_browser_token=False):
    require_read_only_mode()
    redirect_uri = browser_redirect or CALLBACK
    cookies = http.cookiejar.CookieJar()  # No disk storage or browser-cookie extraction.
    opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPCookieProcessor(cookies))
    try:
        discovery = json_response(*request(opener, LOGIN_ORIGIN + "/.well-known/openid-configuration", report, "discovery"))
        if any(discovery.get(k) != v for k, v in {
            "issuer": LOGIN_ORIGIN, "authorization_endpoint": LOGIN_ORIGIN + "/connect/authorize",
            "token_endpoint": LOGIN_ORIGIN + "/connect/token"}.items()):
            raise Blocked("OIDC discovery changed; review current first-party settings.")
        if "S256" not in discovery.get("code_challenge_methods_supported", []):
            raise Blocked("S256 PKCE not advertised.")
        verifier = secrets.token_urlsafe(48)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
        state = secrets.token_urlsafe(32)
        params = {"client_id": "easy_pkce", "redirect_uri": redirect_uri, "response_type": "code",
                  "scope": SCOPE, "state": state, "code_challenge": challenge, "code_challenge_method": "S256"}
        authorize_url = discovery["authorization_endpoint"] + "?" + urllib.parse.urlencode(params)
        if browser_redirect is None:
            url = password_login(opener, authorize_url, report)
            code = callback_code(url, redirect_uri, state)
        else:
            code = browser_callback(authorize_url, redirect_uri, state, open_chrome=open_chrome)
        # The ID token is intentionally unused; account verification uses the API.
        token = json_response(*request(opener, discovery["token_endpoint"], report, "token", fields={
            "grant_type": "authorization_code", "client_id": "easy_pkce", "redirect_uri": redirect_uri,
            "code": code, "code_verifier": verifier}))
        token_type = token.get("token_type")
        if not isinstance(token_type, str) or token_type.lower() != "bearer":
            raise Blocked("Expected Bearer token type.")
        account_origin = redirect_uri.rsplit("/", 1)[0]
        read_money(report, token.get("access_token"), account_origin, compare_browser_token=compare_browser_token)
    finally:
        cookies.clear()


def decimal_value(value, field, *, minimum=Decimal(0), positive=False):
    """Parse API decimal strings without float coercion, NaN or silent defaults."""
    if type(value) not in (int, str, Decimal):
        raise Blocked(f"Missing/invalid {field}.")
    try:
        text = str(value).strip()
        if len(text) > 50 or not re.fullmatch(r"[+-]?[0-9\u06f0-\u06f9\u0660-\u0669]+(?:\.[0-9\u06f0-\u06f9\u0660-\u0669]+)?", text):
            raise ValueError
        result = Decimal(text)
        if (not result.is_finite() or result < minimum or (positive and result <= 0) or
                result > Decimal("1e18") or result.as_tuple().exponent < -18):
            raise ValueError
        return result
    except (ValueError, InvalidOperation):
        raise Blocked(f"Missing/invalid {field}.") from None


def whole_number(value, field, *, positive=True):
    number = decimal_value(value, field, positive=positive)
    if number != number.to_integral_value():
        raise Blocked(f"{field} must be a whole number.")
    return int(number)


def is_decimal_multiple(number, step):
    with localcontext() as ctx:
        ctx.prec = 128
        return number % step == 0


def safe_text(value, limit=240):
    """Allow a bounded diagnostic, suppressing credential-like values and controls."""
    if not isinstance(value, str):
        return ""
    value = re.sub(r"(?i)bearer\s+\S+", "[redacted]", value)
    value = re.sub(r"[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}", "[redacted]", value)
    value = re.sub(r'''(?i)(?:access[_-]?token|refresh[_-]?token|token|password|cookie|authorization|client_secret|api[_-]?key|x-customheader|otp|code)["']?\s*[:=]\s*(?:"[^"]*"|'[^']*'|[^\s,;]+)''',
                   "[redacted]", value)
    value = re.sub(r"[A-Za-z0-9_+/=-]{40,}(?:\.[A-Za-z0-9_+/=-]+)*", "[redacted]", value)
    return "".join(c for c in value if c.isprintable())[:limit]


def sanitized_exception(exc):
    # Never include a traceback, request headers, cookies or a response body.
    text = str(exc).split("Call log:", 1)[0].split("\n", 1)[0]
    text = re.sub(r"https?://[^\s\"']+", "[url]", text)
    return safe_text(type(exc).__name__ + ": " + text, 320)


class BrowserFetchResponse:
    """Small response adapter for fetch executed by the signed-in Chrome page."""

    def __init__(self, result):
        if (not isinstance(result, dict) or type(result.get("status")) is not int or
                not isinstance(result.get("body"), str) or not isinstance(result.get("contentType"), str)):
            raise BrowserTransportFailure("Malformed browser-fetch result; no acknowledgement is assumed.")
        self.status = result["status"]
        self.headers = {"content-type": result["contentType"]}
        self._body = result["body"].encode("utf-8")

    def body(self):
        return self._body

    def dispose(self):
        self._body = b""


def exact_symbol(items, isin):
    if not isinstance(items, list):
        raise Blocked("Symbol API must return an array; its shape was not accepted.")
    matches = [item for item in items if isinstance(item, dict) and item.get("symbolIsin") == isin]
    if len(matches) != 1:
        raise Blocked("Exactly one fresh symbol record must match the draft ISIN.")
    return dict(matches[0])


def symbol_details(payload, isin):
    """Parse jl.fetchAllSymbols/ei.fetchAndUpdateSymbols, without using a cached hash."""
    if not isinstance(payload, dict) or not isinstance(payload.get("symbols"), list):
        raise Blocked("symbols/all must return an object containing a symbols array.")
    if not payload["symbols"]:
        raise Blocked("The full symbol response is empty; cached or missing metadata cannot validate an order.")
    return exact_symbol(payload["symbols"], isin)


def tehran_datetime(value, field):
    """Mirror the frontend's local interpretation of offset-free API date strings."""
    try:
        if type(value) is int:
            result = datetime.fromtimestamp(value / 1000, tehran_zone())
        elif isinstance(value, str):
            result = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if result.tzinfo is None:
                result = result.replace(tzinfo=tehran_zone())
        else:
            raise ValueError
        return result.astimezone(tehran_zone())
    except (ValueError, OverflowError, OSError):
        raise Blocked(f"Missing/invalid {field}; no calendar assumption was made.") from None


def validate_trading_time(symbol, calendar, start_session, at):
    """B9cqRonR.dt: Saturday=1; ordinary pre-trading/trading windows, end exclusive."""
    if not isinstance(calendar, dict) or not isinstance(calendar.get("items"), list):
        raise Blocked("TradingTime.items is missing.")
    trading_type = whole_number(symbol.get("tradingTimeType"), "tradingTimeType")
    rules = [r for r in calendar["items"] if isinstance(r, dict) and r.get("tradingTimeType") == trading_type]
    if len(rules) != 1:
        raise Blocked("Trading rules for this symbol are missing or ambiguous.")
    if not isinstance(start_session, dict):
        raise Blocked("A fresh startsession calendar response is required.")
    server = tehran_datetime(start_session.get("serverTime"), "serverTime")
    session = tehran_datetime(start_session.get("startSessionTimeStamp"), "startSessionTimeStamp")
    local = at.astimezone(tehran_zone())
    if server.date() != session.date() or local.date() != server.date():
        raise Blocked("Target is not the current broker market-session date.")
    rule = rules[0]
    days = rule.get("days")
    if (not isinstance(days, list) or not days or
            any(type(day) is not int or not 1 <= day <= 7 for day in days)):
        raise Blocked("Trading weekdays are missing/invalid.")
    if (local.weekday() + 2) % 7 + 1 not in days:
        raise Blocked("Target weekday is not permitted for this symbol.")
    seconds = local.hour * 3600 + local.minute * 60 + local.second
    windows = []
    for start_key, end_key in (("startPreTradingTime", "endPreTradingTime"), ("startTradingTime", "endTradingTime")):
        start, end = rule.get(start_key), rule.get(end_key)
        if start_key == "startPreTradingTime" and start in (None, "") and end in (None, ""):
            continue
        if any(not isinstance(v, str) or not re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", v) for v in (start, end)):
            raise Blocked("Missing/invalid ordinary trading window.")
        a, b = (int(v[:2]) * 3600 + int(v[3:]) * 60 for v in (start, end))
        if a > b:
            raise Blocked("Overnight trading rules are unsupported by this same-day POC.")
        windows.append((a, b))
    if not any(a <= seconds < b for a, b in windows):
        raise Blocked("Target is outside the symbol's ordinary order-entry windows.")


@dataclass(frozen=True)
class BuyOrder:
    symbol_isin: str
    symbol_name: str
    quantity: int
    price: Decimal
    commission: Decimal
    hide_price: Decimal
    contract_size: Decimal
    total_value: int
    order_from: int

    def payload(self, at):
        # Observed frontend toLocaleString(en-US), using the selected Tehran clock.
        local = at.astimezone(tehran_zone())
        hour = local.hour % 12 or 12
        stamp = (f"{local.month}/{local.day}/{local.year}, {hour}:{local.minute:02}:{local.second:02} "
                 f"{'AM' if local.hour < 12 else 'PM'}")
        return {"order": {"price": self.price, "quantity": self.quantity, "side": 0, "validityType": 0,
                          "createDateTime": stamp, "commission": self.commission,
                          "symbolIsin": self.symbol_isin, "symbolName": self.symbol_name,
                          "orderModelType": 1, "totalValue": self.total_value, "orderFrom": self.order_from}}


def build_buy_order(draft, symbol, market, buying_power, quantity, price, origin, at,
                    calendar, start_session, limit=None):
    """Build a fresh ordinary DAY BUY; never spread the draft's ID/state/timestamp."""
    limit = MAX_ORDER_VALUE_IRR if limit is None else limit
    isin = draft.get("symbolIsin")
    if not isinstance(isin, str) or not re.fullmatch(r"[A-Z0-9]{12}", isin):
        raise Blocked("A valid exact draft symbolIsin is required.")
    if type(draft.get("side")) is not int or draft["side"] != 0:
        raise Blocked("Only saved BUY drafts are supported.")
    if type(draft.get("validityType", 0)) is not int or draft.get("validityType", 0) != 0:
        raise Blocked("This ordinary BUY POC supports DAY validity only.")
    if not isinstance(symbol, dict) or symbol.get("symbolIsin") != isin:
        raise Blocked("Symbol metadata does not match the draft ISIN.")
    if symbol.get("isActive") is not True or symbol.get("canBuy") is not True:
        raise Blocked("Symbol is not explicitly active and buyable.")
    unit = whole_number(symbol.get("marketUnit"), "marketUnit")
    # Ordinary shares/rights and the frontend's ETF family; derivative contracts are excluded.
    ordinary_units = {1, 2, 3, 4, 5, 6, 7, 8, 18, 19, 20, 31, 32, 39, 40, 41, 42, 43, 52, 54}
    if unit not in ordinary_units:
        raise Blocked("This market unit has no supported ordinary BUY contract in the POC.")
    name = symbol.get("symbolName")
    if not isinstance(name, str) or not name.strip() or len(name) > 80 or not name.replace("\u200c", "").isprintable():
        raise Blocked("Invalid symbol name.")
    if not isinstance(market, dict) or market.get("symbolIsin") != isin:
        raise Blocked("Fresh market data must match the selected symbol exactly.")
    # M6BdUGtp.zce identifies A/65 as permitted. Other/unknown states are not assumed tradable.
    if str(market.get("stateCode", "")).strip() not in ("A", "65"):
        raise Blocked("Symbol market state is halted, restricted or unknown.")
    qty = whole_number(quantity, "quantity")
    amount = decimal_value(price, "price", positive=True)
    low = decimal_value(market.get("lowAllowedPrice"), "lowAllowedPrice")
    high = decimal_value(market.get("highAllowedPrice"), "highAllowedPrice", positive=True)
    tick = decimal_value(symbol.get("minDealablePrice"), "minDealablePrice", positive=True)
    step = whole_number(symbol.get("minDealableCount"), "minDealableCount")
    minimum = whole_number(symbol.get("minValidBuyVolume"), "minValidBuyVolume")
    maximum = whole_number(symbol.get("maxValidBuyVolume"), "maxValidBuyVolume")
    for key, chooser in (("minValidBuyVolume", max), ("maxValidBuyVolume", min)):
        if key in market:
            bound = whole_number(market[key], key)
            if key.startswith("min"):
                minimum = chooser(minimum, bound)
            else:
                maximum = chooser(maximum, bound)
    if low > high or not low <= amount <= high or not is_decimal_multiple(amount, tick):
        raise Blocked("Price is outside permitted bounds or is not a multiple of the price tick.")
    if minimum > maximum or not minimum <= qty <= maximum or qty % step:
        raise Blocked("Quantity is outside permitted bounds or is not a multiple of the quantity step.")
    rate = decimal_value(symbol.get("buyCommission"), "buyCommission")
    if rate >= 1:
        raise Blocked("Invalid buy commission rate.")
    hidden = decimal_value(symbol.get("hidePrice"), "hidePrice")
    size = decimal_value(1 if symbol.get("csize") is None else symbol["csize"], "csize", positive=True)
    # Enforce the verified frontend Ko minimum-buy helper as a conservative POC limit.
    etfs = {3, 4, 5, 6, 7, 8, 31, 32, 39, 43, 52, 54}
    base_market = {18, 19, 20, 40, 41, 42}
    minimum_notional = 1_000_000 if unit in etfs else 50_000_000 if unit in base_market else 5_000_000
    cap = decimal_value(limit, "MAX_ORDER_VALUE_IRR", positive=True)
    funds = decimal_value(buying_power, "buyPowerT2 (IRR)")
    with localcontext() as ctx:
        ctx.prec = 128
        if Decimal(qty) * (amount + hidden) < minimum_notional:
            raise Blocked("Quantity is below the frontend minimum-buy value for this market unit.")
        total = int((Decimal(qty) * (amount * (1 + rate) + hidden) * size).to_integral_value(rounding=ROUND_CEILING))
    if total <= 0 or total > cap:
        raise Blocked("Final order value including fees exceeds MAX_ORDER_VALUE_IRR.")
    if Decimal(total) > funds:
        raise Blocked("Insufficient buyPowerT2 for the final IRR order value including fees.")
    if origin not in (DESKTOP_ORIGIN, MOBILE_ORIGIN):
        raise Blocked("Unknown authenticated client context.")
    validate_trading_time(symbol, calendar, start_session, at)
    return BuyOrder(isin, name, qty, amount, rate, hidden, size, total, 34 if origin == DESKTOP_ORIGIN else 33)


def decimal_json(value):
    """Emit exact JSON numbers for Decimal; never convert monetary values to float."""
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise Blocked("Non-finite JSON number.")
        return format(value, "f")
    if isinstance(value, dict):
        return "{" + ",".join(json.dumps(k) + ":" + decimal_json(v) for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ",".join(decimal_json(v) for v in value) + "]"
    return json.dumps(value, ensure_ascii=True, allow_nan=False)


class BrowserOrderSession:
    """Explicit API reads plus one order POST; auth is captured in memory, never exported."""

    def __init__(self, context, page, report=None):
        self.context, self.page = context, page
        self._auth_headers = {}
        self.report = report
        self._draft_snapshot = None
        self._draft_consumed = False
        self._authenticated_by_draft = False
        self._authenticated_by_login = False
        self._failures = {}

    @property
    def authenticated(self):
        return self._authenticated_by_draft or self._authenticated_by_login or bool(self._auth_headers)

    def attach_listeners(self):
        # All listeners precede navigation/login and manual Orders > Drafts interaction.
        self.context.on("request", self.capture_request)
        self.context.on("response", self.observe_response)
        self.context.on("requestfailed", self.observe_failure)

    def _set_auth(self, headers):
        if not isinstance(headers, dict):
            return False
        allowed = {"authorization", "x-device-id", "x-app-name", "x-customheader", "x-api-key", "shard"}
        headers = {k.lower(): v for k, v in headers.items() if k.lower() in allowed}
        auth = headers.get("authorization", "")
        if not isinstance(auth, str) or not re.fullmatch(r"Bearer [A-Za-z0-9._~+/-]+=*", auth, re.I):
            return False
        if any(not isinstance(v, str) or len(v) > 20000 or "\r" in v or "\n" in v for v in headers.values()):
            return False
        self._auth_headers = headers
        return True

    def capture_request(self, request):
        parsed = urllib.parse.urlsplit(request.url)
        if f"{parsed.scheme}://{parsed.netloc}" != ACCOUNT_API_ORIGIN:
            return False
        # This property does not issue a nested protocol call from the event callback.
        return self._set_auth(request.headers)

    def capture_response_auth(self, response):
        parsed = urllib.parse.urlsplit(response.url)
        if f"{parsed.scheme}://{parsed.netloc}" != ACCOUNT_API_ORIGIN:
            return False
        headers = response.request.all_headers()
        if (response.request.method == "GET" and parsed.path == "/easy/api/draft" and
                response.status == 200 and isinstance(headers, dict) and
                not any(k.lower() == "authorization" for k in headers)):
            # A proven cookie-authenticated draft response does not require inventing a bearer token.
            self._auth_headers = {}
            return False
        return self._set_auth(headers)

    def observe_response(self, response):
        parsed = urllib.parse.urlsplit(response.url)
        if f"{parsed.scheme}://{parsed.netloc}" == ACCOUNT_API_ORIGIN:
            self._failures.pop((response.request.method, parsed.path), None)

    def observe_failure(self, request):
        parsed = urllib.parse.urlsplit(request.url)
        if f"{parsed.scheme}://{parsed.netloc}" == ACCOUNT_API_ORIGIN:
            self._failures[(request.method, parsed.path)] = safe_text(request.failure or "browser request failed")

    def last_failure(self, method, url):
        return self._failures.get((method, urllib.parse.urlsplit(url).path))

    def seed_drafts(self, payload):
        if self._draft_snapshot is not None or self._draft_consumed:
            raise Blocked("The saved draft snapshot has already been observed.")
        self._draft_snapshot = payload
        self._authenticated_by_draft = True

    @property
    def origin(self):
        url = urllib.parse.urlsplit(self.page.url)
        origin = f"{url.scheme}://{url.netloc}"
        if origin not in (DESKTOP_ORIGIN, MOBILE_ORIGIN):
            raise Blocked("The browser is not on an authenticated EasyTrader client page.")
        return origin

    def capture_auth(self, response):
        url = urllib.parse.urlsplit(response.url)
        if (response.request.method != "GET" or response.from_service_worker or response.status != 200 or
                url._replace(query="", fragment="").geturl() != MONEY_URL or
                response.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json"):
            return False
        return self.capture_response_auth(response)

    def _request(self, method, url, body=None, *, draft_bootstrap=False):
        reads = {MONEY_URL, TRADING_TIME_URL, START_SESSION_URL, ORDERS_URL}
        if not ((method == "GET" and url in reads) or
                (method == "POST" and url in (SYMBOLS_URL, MARKET_DATA_URL, ORDER_URL)) or
                (draft_bootstrap and self._authenticated_by_login and method == "GET" and url == DRAFT_URL)):
            raise Blocked("API operation is outside the POC allowlist.")
        if url == SYMBOLS_URL and body != SYMBOLS_REQUEST_BODY:
            raise Blocked("symbols/all requires the frontend's full-refresh POST body: hash is the string null.")
        if not self.authenticated:
            raise Blocked("An authenticated first-party draft response has not been observed.")
        self.page.wait_for_timeout(0)  # Deliver queued app token-refresh/navigation events before copying headers.
        self.origin  # Reject navigation away from the authenticated first-party client.
        headers = {**self._auth_headers, "Accept": "application/json", "Cache-Control": "no-cache"}
        if method == "POST":
            headers["Content-Type"] = "application/json"
        self._failures.pop((method, urllib.parse.urlsplit(url).path), None)
        # APIRequestContext uses a different HTTP/TLS stack from Chrome. Keep both reads
        # and the sole order POST in the proven signed-in browser network context.
        script = """async ({url, method, headers, body, timeoutMs, maxBytes}) => {
            const abort = new AbortController();
            const timer = setTimeout(() => abort.abort(), timeoutMs);
            try {
                const response = await fetch(url, {method, headers,
                    body: method === 'GET' ? undefined : body,
                    credentials: 'include', redirect: 'error', cache: 'no-store', signal: abort.signal});
                const reader = response.body?.getReader();
                const chunks = []; let total = 0;
                if (reader) { while (true) {
                    const {done, value} = await reader.read();
                    if (done) break;
                    total += value.byteLength;
                    if (total > maxBytes) { await reader.cancel(); throw new Error('Response exceeds size limit'); }
                    chunks.push(value);
                }}
                const bytes = new Uint8Array(total); let offset = 0;
                for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
                return {kind: 'response', status: response.status,
                    contentType: response.headers.get('content-type') || '',
                    body: new TextDecoder().decode(bytes)};
            } catch (error) {
                return {kind: 'browser-transport', name: error?.name || 'Error',
                    message: String(error?.message || 'Browser fetch failed').slice(0, 400)};
            } finally { clearTimeout(timer); }
        }"""
        try:
            result = self.page.evaluate(script, {"url": url, "method": method, "headers": headers, "body": body,
                                                "timeoutMs": NETWORK_TIMEOUT_SECONDS * 1000,
                                                "maxBytes": MAX_SYMBOL_RESPONSE_BYTES if url == SYMBOLS_URL else MAX_RESPONSE_BYTES})
        except Exception as exc:
            raise BrowserTransportFailure(sanitized_exception(exc)) from None
        if isinstance(result, dict) and result.get("kind") == "browser-transport":
            detail = safe_text(str(result.get("name", "Error")) + ": " + str(result.get("message", "fetch failed")))
            failure = self.last_failure(method, url)
            raise BrowserTransportFailure(detail + ("; " + failure if failure else ""))
        return BrowserFetchResponse(result)

    def read(self, url, body=None):
        method = "GET" if body is None else "POST"
        if url == DRAFT_URL:
            if body is not None or self._draft_snapshot is None or self._draft_consumed:
                raise Blocked("Drafts must come from the proven browser-response observation, once per run.")
            result, self._draft_snapshot = self._draft_snapshot, None
            self._draft_consumed = True
            return result
        if url == ORDER_URL:
            raise Blocked("An order cannot be submitted through the read API.")
        return self._read_remote(url, body)

    def load_drafts_after_login(self):
        if self._draft_snapshot is not None or self._draft_consumed:
            raise Blocked("Drafts have already been read for this run.")
        payload = self._read_remote(DRAFT_URL, draft_bootstrap=True)
        if not isinstance(payload, list):
            raise Blocked("Expected the proven root draft array.")
        self.seed_drafts(payload)

    def _read_remote(self, url, body=None, *, draft_bootstrap=False):
        method = "GET" if body is None else "POST"
        response = None
        path = urllib.parse.urlsplit(url).path
        entry = {"stage": "single-order-read", "method": method, "path": path, "http_status": None}
        started = time.perf_counter()
        if self.report is not None:
            self.report.append(entry)
        try:
            response = self._request(method, url, body, draft_bootstrap=draft_bootstrap)
            entry["http_status"] = response.status
            limit = MAX_SYMBOL_RESPONSE_BYTES if url == SYMBOLS_URL else MAX_RESPONSE_BYTES
            return browser_json(response, limit)
        except Blocked as exc:
            entry["failure_kind"] = ("browser_transport" if isinstance(exc, BrowserTransportFailure)
                                     else "http_response" if isinstance(exc, HttpResponseFailure) else "response_validation")
            entry["error"] = safe_text(str(exc), 320)
            raise type(exc)(f"{method} {path}: {exc}") from None
        except Exception as exc:
            entry["failure_kind"] = "browser_transport"
            entry["error"] = sanitized_exception(exc)
            raise BrowserTransportFailure(f"{method} {path}: {entry['error']}") from None
        finally:
            entry["latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
            if response is not None:
                try:
                    response.dispose()
                except Exception:
                    pass  # Disposal cannot invalidate the already-validated read.

    def submit(self, body):
        return self._request("POST", ORDER_URL, body)


def browser_json(response, limit=MAX_RESPONSE_BYTES, *, require_success=True):
    if ((require_success and not 200 <= response.status < 300) or
            response.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json"):
        raise HttpResponseFailure(f"Expected a successful JSON response (HTTP {response.status}).")
    body = response.body()
    if len(body) > limit:
        raise Blocked("API response exceeded the permitted size.")
    try:
        return json.loads(body, parse_float=Decimal,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError, RecursionError):
        raise Blocked("Malformed API JSON; response details suppressed.") from None


def read_buy_inputs(session, draft):
    symbol = symbol_details(session.read(SYMBOLS_URL, SYMBOLS_REQUEST_BODY), draft["symbolIsin"])
    market = exact_symbol(session.read(MARKET_DATA_URL, decimal_json([draft["symbolIsin"]])), draft["symbolIsin"])
    money = session.read(MONEY_URL)
    if not isinstance(money, dict):
        raise Blocked("Money API must return an object.")
    # main-RMHHQAO7.ai$3 maps buyPowerT2 directly to the form's IRR buying-power label.
    funds = decimal_value(money.get("buyPowerT2"), "buyPowerT2 (IRR)")
    calendar = session.read(TRADING_TIME_URL)
    start_session = session.read(START_SESSION_URL)
    return symbol, market, funds, calendar, start_session


@contextlib.contextmanager
def console_keys():
    """Read Enter/Esc without requiring an extra newline; restore POSIX terminal state."""
    if os.name == "nt":
        import msvcrt
        yield lambda wait=False: msvcrt.getwch() if wait or msvcrt.kbhit() else None
    elif sys.stdin.isatty():
        import select
        import termios
        import tty
        descriptor = sys.stdin.fileno()
        previous = termios.tcgetattr(descriptor)
        try:
            tty.setcbreak(descriptor)
            yield lambda wait=False: sys.stdin.read(1) if wait or select.select([sys.stdin], [], [], 0)[0] else None
        finally:
            termios.tcsetattr(descriptor, termios.TCSADRAIN, previous)
    else:
        raise Blocked("Use an interactive console for Enter/Esc confirmation.")


def check_console_cancel(read_key):
    while True:
        key = read_key()
        if key is None:
            return
        if key in ("\x1b", "\x03"):
            raise KeyboardInterrupt
        if key == "":
            raise EOFError


def confirm_order():
    print("ENTER to confirm these repeated orders; ESC to cancel.", flush=True)
    with console_keys() as read_key:
        while True:
            key = read_key(True)
            if key in ("\r", "\n"):
                return True
            if key == "\x1b":
                return False
            if key == "\x03":
                raise KeyboardInterrupt
            if key == "":
                raise EOFError


def local_now():
    return datetime.now().astimezone()


def prompt_order_time(default=None):
    """Use today's system-local clock; do not ask for or synchronize a time zone."""
    now = local_now()
    defaults = (default.hour, default.minute, default.second) if default is not None else (8, 44, 58)
    values = []
    for label, fallback, maximum in zip(("Hour", "Minute", "Second"), defaults, (23, 59, 59)):
        value = input(f"{label} [{fallback:02}]: ").strip() or str(fallback)
        if not re.fullmatch(r"[0-9]{1,2}", value) or not 0 <= int(value) <= maximum:
            raise Blocked(f"Invalid local {label.lower()}.")
        values.append(int(value))
    target = now.replace(hour=values[0], minute=values[1], second=values[2], microsecond=0)
    if target <= local_now():
        raise Blocked("Today's local target has passed; no next-day scheduling.")
    return target


@dataclass(frozen=True)
class SubmissionWindow:
    duration_ns: int
    interval_ns: int


def prompt_submission_window():
    duration = decimal_value(input("Submission window in seconds [5]: ").strip() or "5", "submission window", positive=True)
    interval = whole_number(input("Minimum dispatch gap, microseconds [350]: ").strip() or "350", "request gap")
    nanos = duration * 1_000_000_000
    if nanos != nanos.to_integral_value():
        raise Blocked("Submission-window precision cannot exceed nanoseconds.")
    return SubmissionWindow(int(nanos), interval * 1000)


def submission_validation_time(symbol, calendar, start_session, target, window):
    """Allow starting before opening only when this bounded window overlaps verified trading hours."""
    end = target + timedelta(microseconds=window.duration_ns // 1000)
    candidates = [target, end - timedelta(microseconds=1)]
    local = target.astimezone(tehran_zone())
    if isinstance(calendar, dict) and isinstance(calendar.get("items"), list):
        for rule in calendar["items"]:
            if not isinstance(rule, dict) or rule.get("tradingTimeType") != symbol.get("tradingTimeType"):
                continue
            for field in ("startPreTradingTime", "startTradingTime"):
                value = rule.get(field)
                if isinstance(value, str) and re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
                    candidate = local.replace(hour=int(value[:2]), minute=int(value[3:]), second=0, microsecond=0)
                    if target <= candidate < end:
                        candidates.append(candidate)
    error = None
    for candidate in sorted(candidates):
        try:
            validate_trading_time(symbol, calendar, start_session, candidate)
            return candidate
        except Blocked as exc:
            error = exc
    raise Blocked("The selected submission window does not overlap a verified trading session: " + str(error))


def wait_local_target(target, session, *, display_target=None):
    """Show six fractional digits on a monotonic countdown; this is not a timing guarantee."""
    delay = (target - datetime.now(tehran_zone())).total_seconds()
    if delay < -MAX_SUBMISSION_LATENESS_SECONDS:
        raise Blocked("Selected Tehran time has passed; no order was submitted.")
    deadline = time.monotonic_ns() + max(0, int(delay * 1_000_000_000))
    display_offset = max(0, int(((display_target or target) - target).total_seconds() * 1_000_000_000))
    next_display = 0
    with console_keys() as read_key:
        try:
            while True:
                check_console_cancel(read_key)
                now = time.monotonic_ns()
                remaining = max(0, deadline - now)
                if now >= next_display or remaining == 0:
                    micros = (remaining + display_offset) // 1000
                    seconds, fraction = divmod(micros, 1_000_000)
                    hours, seconds = divmod(seconds, 3600)
                    minutes, seconds = divmod(seconds, 60)
                    print(f"\rRemaining {hours:02}:{minutes:02}:{seconds:02}.{fraction:06} | ESC cancels", end="", flush=True)
                    next_display = now + 50_000_000
                if remaining == 0:
                    return
                if remaining > 2_000_000:
                    session.page.wait_for_timeout(min(20, (remaining - 2_000_000) / 1_000_000))
        finally:
            print()


class OneShotOrder:
    def __init__(self):
        self.attempted = False

    def submit(self, session, order, target, report, *, approved=False):
        if not approved or self.attempted:
            raise Blocked("Exactly one explicitly approved order attempt is permitted per run.")
        now = datetime.now(tehran_zone())
        lateness = (now - target).total_seconds() if target is not None else None
        if lateness is not None and (lateness < 0 or lateness > MAX_SUBMISSION_LATENESS_SECONDS):
            raise Blocked("Dispatch is outside the selected Tehran time tolerance.")
        if order.order_from != (34 if session.origin == DESKTOP_ORIGIN else 33):
            raise Blocked("The authenticated client context changed after approval.")
        body = decimal_json(order.payload(now))
        self.attempted = True
        entry = {"stage": "order-submit", "method": "POST", "path": "/core/api/v2/order",
                 "request_start": now.isoformat(timespec="milliseconds"), "response_arrival": None,
                 "http_status": None, "isSuccessful": None, "id": None, "message": None, "omsError": None,
                 "error": "Submission outcome uncertain; never retry.", "acceptance": "UNCERTAIN",
                 "latency_ms": None, "lateness_ms": round(lateness * 1000, 3) if lateness is not None else None,
                 "mode": "SCHEDULED" if target is not None else "IMMEDIATE"}
        report.append(entry)
        started = time.perf_counter()
        response = None
        try:
            response = session.submit(body)
            entry["response_arrival"] = datetime.now(tehran_zone()).isoformat(timespec="milliseconds")
            entry["http_status"] = response.status
            data = browser_json(response, require_success=False)
            if not isinstance(data, dict) or type(data.get("isSuccessful")) is not bool:
                raise Blocked("Order acknowledgement lacks a boolean isSuccessful.")
            entry["isSuccessful"] = data["isSuccessful"]
            entry["message"] = safe_text(data.get("message"))
            errors = data.get("omsError")
            if isinstance(errors, list):
                entry["omsError"] = [{"error": safe_text(e.get("error"))} for e in errors[:3] if isinstance(e, dict)]
            elif isinstance(errors, str):
                entry["omsError"] = safe_text(errors)
            identifier = data.get("id")
            if isinstance(identifier, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", identifier):
                entry["id"] = identifier
            if data["isSuccessful"]:
                if not 200 <= response.status < 300:
                    raise HttpResponseFailure(f"HTTP {response.status} conflicts with the successful acknowledgement; do not retry.")
                if entry["id"] is None:
                    raise Blocked("Successful acknowledgement has no valid order ID; do not retry.")
                entry.update(acceptance="ACCEPTED", error=None)
            else:
                messages = [safe_text(data.get("message"))]
                if isinstance(errors, list):
                    messages += [safe_text(e.get("error")) for e in errors[:3] if isinstance(e, dict)]
                entry.update(acceptance="REJECTED", error="; ".join(filter(None, messages)) or "Broker rejected the order.")
        except Blocked as exc:
            entry["error"] = safe_text(str(exc)) + " Submission outcome uncertain; never retry."
        except Exception:
            # Transport/parser exception strings can contain headers or private response data.
            if entry["error"] is None:
                entry["error"] = "Submission outcome uncertain; never retry."
        finally:
            entry["latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
            if response is not None:
                try:
                    response.dispose()
                except Exception:
                    pass  # Cleanup cannot change the acknowledgement or cause another submission.
        return entry


BURST_DISPATCH_SCRIPT = """({url, headers, body, startMs, durationMs, intervalMs}) => {
    const start = performance.now() + (startMs - Date.now());
    const end = start + durationMs;
    const pending = [];
    let next = start, count = 0;
    try {
        while (performance.now() < end) {
            const now = performance.now();
            if (now < next) continue;
            const controller = new AbortController();
            pending.push(controller);
            const payload = body.replace('"createDateTime":"__POC_TIMESTAMP__"',
                '"createDateTime":' + JSON.stringify(new Date().toLocaleString('en-US')));
            if (performance.now() >= end) break;
            // Each call is a distinct, pre-approved order; no response is awaited or retried.
            void fetch(url, {method: 'POST', headers, body: payload, credentials: 'include',
                redirect: 'error', cache: 'no-store', signal: controller.signal}).catch(() => {});
            count++;
            console.log('POC_DISPATCH ' + JSON.stringify({attempt: count, elapsed_us: Math.round((now - start) * 1000)}));
            next = performance.now() + intervalMs;
        }
    } finally {
        // Cancel queued HTTP work at the cutoff. This does NOT cancel an accepted brokerage order.
        for (const controller of pending) controller.abort();
    }
    return {attempts: count, responses_checked: 0};
}"""


def dispatch_order_window(session, order, target, window, report, *, approved=False):
    """Initiate independent orders only inside the authorized local-time window; never await responses."""
    if not approved or not session.authenticated:
        raise Blocked("A signed-in session and explicit confirmation are required.")
    if window.duration_ns <= 0 or window.interval_ns <= 0:
        raise Blocked("Submission duration and interval must be positive.")
    if order.order_from != (34 if session.origin == DESKTOP_ORIGIN else 33):
        raise Blocked("The authenticated client context changed after confirmation.")
    body = order.payload(target)
    body["order"]["createDateTime"] = "__POC_TIMESTAMP__"
    headers = {**session._auth_headers, "Accept": "application/json", "Content-Type": "application/json",
               "Cache-Control": "no-cache"}
    records = []

    def dispatched(message):
        if message.type != "log" or not message.text.startswith("POC_DISPATCH "):
            return
        try:
            data = json.loads(message.text[len("POC_DISPATCH "):])
            attempt, elapsed = data["attempt"], data["elapsed_us"]
            if (type(attempt) is not int or attempt != len(records) + 1 or
                    type(elapsed) is not int or not 0 <= elapsed <= window.duration_ns // 1000 + 1):
                return
        except (ValueError, KeyError, TypeError):
            return
        entry = {"stage": "order-submit", "method": "POST", "path": "/core/api/v2/order",
                 "attempt": attempt, "elapsed_us": elapsed, "acceptance": "UNOBSERVED",
                 "isSuccessful": None, "id": None, "error": None}
        records.append(entry)
        report.append(entry)
        print(f"{attempt:05} POST started | +{elapsed:09} us", flush=True)

    session.page.on("console", dispatched)
    try:
        result = session.page.evaluate(BURST_DISPATCH_SCRIPT, {
            "url": ORDER_URL, "headers": headers, "body": decimal_json(body),
            "startMs": target.timestamp() * 1000, "durationMs": window.duration_ns / 1_000_000,
            "intervalMs": window.interval_ns / 1_000_000})
        if not isinstance(result, dict) or type(result.get("attempts")) is not int or result["attempts"] != len(records):
            raise Blocked("Dispatch-log count could not be verified; outcomes remain unobserved. Do not replay the window.")
    except Blocked:
        raise
    except Exception as exc:
        raise BrowserTransportFailure("Dispatch interrupted; outcomes are unobserved. Do not replay. " + sanitized_exception(exc)) from None
    finally:
        session.page.remove_listener("console", dispatched)
    return {"acceptance": "UNOBSERVED", "attempts": len(records), "responses_checked": 0}


def reconcile_order(session, identifier, report):
    """Poll only GET /core/api/order for the exact acknowledged ID; never resend."""
    entry = {"stage": "order-reconcile", "method": "GET", "path": "/core/api/order",
             "id": identifier, "found": False, "reads": 0, "error": None}
    report.append(entry)
    for attempt in range(ORDER_RECONCILE_ATTEMPTS):
        entry["reads"] += 1
        try:
            payload = session.read(ORDERS_URL)
            if not isinstance(payload, dict) or not isinstance(payload.get("orders"), list):
                raise Blocked("Order list lacks the verified orders array.")
            matches = [order for order in payload["orders"] if isinstance(order, dict) and order.get("id") == identifier]
            if len(matches) > 1:
                raise Blocked("Order list contains duplicate acknowledged IDs.")
            if matches:
                entry["found"] = True
                print(f"Order-list reconciliation: FOUND exact order ID {identifier}. Execution/fills are not tracked.")
                return entry
        except Exception as exc:
            entry["error"] = sanitized_exception(exc)
            print("Order-list reconciliation unavailable: " + entry["error"] + " No order was resent.")
            return entry
        if attempt < ORDER_RECONCILE_ATTEMPTS - 1:
            session.page.wait_for_timeout(500)
    entry["error"] = "Acknowledged ID was not visible within the bounded read-only check. Do not resend."
    print("Order-list reconciliation: NOT YET FOUND. Acknowledgement remains recorded; do not resend.")
    return entry


def single_order_workflow(session, target, report, *, live=False):
    if target is not None and datetime.now(tehran_zone()) >= target:
        raise Blocked("Today's target passed before the draft read.")
    drafts = session.read(DRAFT_URL)  # One immutable selection snapshot; never re-read or delete drafts.
    if not isinstance(drafts, list):
        raise Blocked("Expected the observed saved-draft array.")
    # Preserve the proven preview's row numbering, including non-BUY drafts.
    details = draft_details(drafts)
    buys = [dict(d) for d in drafts]
    if not details:
        raise Blocked("No saved BUY draft is available.")
    for i, detail in enumerate(details, 1):
        print(f"  {i}. {safe_text(detail, 200)}")
    selection = input("One BUY draft number; Enter cancels: ").strip()
    if not selection:
        return
    index = whole_number(selection, "draft selection")
    if index > len(buys):
        raise Blocked("Select exactly one listed BUY draft.")
    draft = buys[index - 1]
    if type(draft.get("side")) is not int or draft["side"] != 0:
        raise Blocked("The selected saved draft must be a BUY; no order was submitted.")
    inputs = read_buy_inputs(session, draft)
    quantity = input(f"BUY quantity [{draft['quantity']}]: ").strip() or draft["quantity"]
    price = input(f"BUY unit price in IRR [{draft['price']}]: ").strip() or draft["price"]
    whole_number(quantity, "quantity")
    decimal_value(price, "price", positive=True)
    target = prompt_order_time(target)
    window = prompt_submission_window()

    def prepare(values):
        symbol, market, funds, calendar, start_session = values
        return build_buy_order(draft, symbol, market, funds, quantity, price, session.origin,
                               submission_validation_time(symbol, calendar, start_session, target, window),
                               calendar, start_session)

    order = prepare(inputs)
    print(f"BUY {order.symbol_name} | Quantity: {order.quantity} | Unit price: {order.price:,} IRR")
    print(f"Total per order including commission: {order.total_value:,} IRR | Local start: {target:%H:%M:%S}")
    print(f"Repeated independent orders for {window.duration_ns / 1_000_000_000:g}s; "
          f"minimum dispatch gap {window.interval_ns / 1000:g} us. Responses will not be checked.")
    print(f"Up to {(window.duration_ns + window.interval_ns - 1) // window.interval_ns:,} new order attempts; "
          "each successful order is an additional purchase.")
    if not live:
        report.append({"stage": "single-order-preview", "selected_count": 1, "order_requests": 0})
        return
    if not confirm_order():
        print("Cancelled before submission.")
        return
    if target is not None and datetime.now(tehran_zone()) >= target:
        raise Blocked("Target passed before approval completed.")
    if target is not None:
        refresh_at = target - timedelta(seconds=PREFLIGHT_LEAD_SECONDS)
        if datetime.now(tehran_zone()) < refresh_at:
            wait_local_target(refresh_at, session, display_target=target)
    checked_at = time.monotonic()
    with console_keys() as read_key:
        check_console_cancel(read_key)
    fresh = read_buy_inputs(session, draft)
    refreshed = prepare(fresh)
    if refreshed != order:
        raise Blocked("Order fields changed since approval; no POST was sent. Review a new preview.")
    if target is not None:
        wait_local_target(target, session)
    now = datetime.now(tehran_zone())
    if time.monotonic() - checked_at > MAX_PREFLIGHT_AGE_SECONDS:
        raise Blocked("Final validation became stale; no order was submitted.")
    if time.monotonic() - checked_at + window.duration_ns / 1_000_000_000 > MAX_PREFLIGHT_AGE_SECONDS:
        raise Blocked("The submission window would exceed the verified preflight freshness limit.")
    submission_validation_time(fresh[0], fresh[3], fresh[4], target, window)
    with console_keys() as read_key:
        check_console_cancel(read_key)
    return dispatch_order_window(session, order, target, window, report, approved=True)


def login_then_close_window(playwright, browser, report, browsers, origin):
    """Transfer the authenticated session in memory; close the visible private window."""
    context = browser.new_context(service_workers="block")
    page = context.new_page()
    session = BrowserOrderSession(context, page, report)
    session.attach_listeners()

    def signed_in(response):
        return (response.request.method == "GET" and not response.from_service_worker and
                response.url.split("?", 1)[0] == MONEY_URL and response.status == 200 and
                response.headers.get("content-type", "").split(";", 1)[0].strip().lower() == "application/json")

    print("Sign in manually in Chrome and complete MFA/CAPTCHA. The private window closes automatically after login.")
    with context.expect_event("response", predicate=signed_in, timeout=BROWSER_READ_TIMEOUT_MS) as observed:
        page.goto(origin + "/", wait_until="commit", timeout=30_000)
    response = observed.value
    parse_buying_power(response.status, {"Content-Type": response.headers.get("content-type", "")}, response.body())
    session.capture_response_auth(response)
    session._authenticated_by_login = True
    page.wait_for_load_state("domcontentloaded", timeout=30_000)
    if session.origin != origin:
        raise Blocked("Login did not return to the selected EasyTrader client.")
    # No path is passed: cookies, OIDC state and session storage never go to disk or logs.
    state = context.storage_state()
    transient = page.evaluate("() => Object.fromEntries(Object.entries(sessionStorage))")
    user_agent = page.evaluate("() => navigator.userAgent")
    background = playwright.chromium.launch(channel="chrome", headless=True)
    browsers.append(background)
    hidden_context = background.new_context(service_workers="block", storage_state=state, user_agent=user_agent)
    hidden_context.add_init_script("if (location.origin === " + json.dumps(origin) + ") {" +
                                   "for (const [key, value] of Object.entries(" + json.dumps(transient) +
                                   ")) sessionStorage.setItem(key, value);}")
    # Close before any draft selection, quantity, price, time or confirmation prompt.
    browser.close()
    browsers.remove(browser)
    session.context, session.page = hidden_context, hidden_context.new_page()
    session.attach_listeners()
    session.page.goto(origin + "/", wait_until="domcontentloaded", timeout=30_000)
    state, transient = None, None
    report.append({"stage": "browser-login", "http_status": response.status, "private_window_closed": True})
    print("Login complete. Private window closed; session retained in memory.")
    session.load_drafts_after_login()
    return session


def run_single_order_browser(target, report, *, live=False, mobile=False):
    try:
        from playwright.sync_api import Error, TimeoutError as BrowserTimeout, sync_playwright
    except ImportError:
        raise Blocked("This workflow requires the existing Playwright dependency.") from None
    browsers = []
    try:
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(channel="chrome", headless=False)
                browsers.append(browser)
                session = login_then_close_window(playwright, browser, report, browsers,
                                                 MOBILE_ORIGIN if mobile else DESKTOP_ORIGIN)
                return single_order_workflow(session, target, report, live=live)
            finally:
                for active in reversed(browsers):
                    if active.is_connected():
                        try:
                            active.close()
                        except Exception as exc:
                            # Cleanup cannot mask cancellation or an order acknowledgement.
                            detail = sanitized_exception(exc)
                            report.append({"stage": "browser-cleanup", "error": detail})
                            print("Browser cleanup stopped: " + detail + ". No request was retried.")
    except BrowserTimeout as exc:
        raise BrowserTransportFailure("Browser timeout: " + sanitized_exception(exc)) from None
    except Error as exc:
        raise BrowserTransportFailure("Browser operation: " + sanitized_exception(exc)) from None


def run_report(report):
    attempts = [entry for entry in report if entry.get("stage") == "order-submit"]
    last = attempts[-1] if attempts else None
    return {"requests": report, "order_requests": len(attempts),
            "order_id": last.get("id") if last else None,
            "broker_order_response": {k: last.get(k) for k in ("isSuccessful", "id", "message", "omsError", "error", "http_status", "latency_ms")} if last else None,
            "order_list_verified": last.get("order_list_verified") if last else None,
            "acceptance": last["acceptance"] if last else "NOT_ATTEMPTED",
            "execution": "NOT_TRACKED" if last else "NOT_ATTEMPTED"}


def main(args=None):
    args = sys.argv[1:] if args is None else args
    if args == ["--self-test"]:
        return self_test()
    browser_targets = {
        ("--browser-login",): CALLBACK,
        ("--browser-login", "--mobile"): MOBILE_CALLBACK,
    }
    compare_browser_token = args[-1:] == ["--compare-browser-token"]
    browser_args = args[:-1] if compare_browser_token else args
    open_chrome = browser_args[-1:] == ["--open-chrome"]
    if open_chrome:
        browser_args = browser_args[:-1]
    browser_redirect = browser_targets.get(tuple(browser_args))
    token_origins = {
        ("--browser-token",): DESKTOP_ORIGIN,
        ("--browser-token", "--mobile"): MOBILE_ORIGIN,
    }
    token_origin = token_origins.get(tuple(args))
    draft_preview = args == ["--browser-draft-preview"]
    draft_schedule = len(args) == 2 and args[0] == "--browser-draft-schedule"
    single_order = args[:1] == ["--browser-single-order"]
    live = args[:1] == ["--live"]
    order_contract = args == ["--browser-order-contract"]
    draft_send = args[:1] == ["--browser-draft-send"]
    browser_observation = args in (["--browser-read"], ["--browser-drafts"]) or draft_preview or draft_schedule
    if (args and args != ["--login"] and browser_redirect is None and token_origin is None
            and not browser_observation and not single_order and not draft_send and not order_contract and not live):
        print("Usage: python POC/easytrader_poc.py "
              "[--self-test | --login | --browser-login [--mobile] [--open-chrome] "
              "[--compare-browser-token] | --browser-token [--mobile] | --browser-read | --browser-drafts "
              "| --browser-draft-preview | --browser-draft-schedule HH:MM:SS | --browser-single-order [HH:MM:SS] "
              "| --browser-order-contract | --live [HH:MM:SS] [--mobile]]")
        return 2
    report = []
    try:
        require_read_only_mode()
        if args[:1] in (["--browser-single-order"], ["--live"]):
            flags = [part for part in args[1:] if part.startswith("--")]
            times = [part for part in args[1:] if not part.startswith("--")]
            if (len(times) > 1 or len(flags) != len(set(flags)) or
                    any(flag not in ("--mobile", "--live") for flag in flags) or
                    (args[0] == "--live" and "--live" in flags)):
                raise Blocked("Use --browser-single-order [HH:MM:SS] [--mobile] [--live], or --live [HH:MM:SS] [--mobile].")
            target = tehran_target(datetime.now(tehran_zone()), times[0]) if times else None
            result = run_single_order_browser(target, report, live=args[0] == "--live" or "--live" in flags,
                                              mobile="--mobile" in flags)
            return 0 if result is None or result.get("acceptance") in ("ACCEPTED", "UNOBSERVED") else 2
        if draft_send:
            raise Blocked("Direct group send is disabled until the EasyTrader API contract is verified.")
        print("Read-only POC mode.")
        if order_contract:
            observe_browser(report, order_contract=True)
        elif draft_schedule:
            scheduled_at = tehran_target(datetime.now(tehran_zone()), args[1])
            print(f"Scheduled draft rehearsal for {scheduled_at.isoformat()}.")
            payload = observe_browser(report, draft_discovery=True, scheduled_at=scheduled_at)
            preview_draft_selection(payload, report, scheduled_at=scheduled_at)
        elif browser_observation:
            payload = observe_browser(report, draft_discovery=args != ["--browser-read"])
            if draft_preview:
                preview_draft_selection(payload, report)
        elif token_origin is not None:
            access = read_browser_access_token(token_origin)
            read_money(report, access, token_origin)
        elif args:
            authenticate_and_check(report, browser_redirect=browser_redirect, open_chrome=open_chrome,
                                   compare_browser_token=compare_browser_token)
        else:
            print("No network requests. Use --browser-login for the PO's local authentication test.")
            value = validate_order(SYMBOL, QUANTITY, PRICE, MAX_ORDER_VALUE_IRR)
            print(f"Local intent: BUY {SYMBOL}, quantity={QUANTITY}, price={PRICE} IRR; notional={value} IRR.")
            delay = seconds_until_target(datetime.now(tehran_zone()), TARGET_TIME)
            print(f"Today's Tehran target is {delay:.3f}s away. No wait or arming occurs.")
        return 0
    except Blocked as exc:
        print("STOP:", exc)
        return 2
    except (KeyboardInterrupt, EOFError):
        print("Interrupted; submission may be uncertain. Do not retry." if run_report(report)["order_requests"]
              else "Cancelled. No order request was sent.")
        return 130
    except (ValueError, UnicodeError):
        print("STOP: malformed authentication response; sensitive details suppressed.")
        return 2
    finally:
        summary = run_report(report)
        if single_order or live:
            summary = {"order_requests": summary["order_requests"], "acceptance": summary["acceptance"]}
        print(json.dumps(summary, ensure_ascii=True))


def self_test():
    import contextlib
    import io
    import unittest
    from unittest.mock import MagicMock, Mock, patch

    class Tests(unittest.TestCase):
        def test_order_limits_and_types(self):
            self.assertEqual(validate_order("TEST", 2, 100, 200), 200)
            for values in [("xxxx", 1, 1, 10), ("", 1, 1, 10), ("TEST", 0, 1, 10),
                           ("TEST", True, 1, 10), ("TEST", 1, 1.5, 10), ("TEST", 1, -1, 10),
                           ("TEST", 2, 101, 200), ("TEST", 1, 1, 0)]:
                with self.subTest(values=values), self.assertRaises(Blocked):
                    validate_order(*values)

        def test_tehran_timing_and_no_rollover(self):
            now = datetime.fromisoformat("2026-11-03T05:14:59+00:00")
            self.assertEqual(seconds_until_target(now, "08:45:00"), 1)
            self.assertEqual(seconds_until_target(now, "08:44:59"), 0)
            for target in ("08:44:58", "24:00:00", "8:45:00", "08:45:00Z"):
                with self.subTest(target=target), self.assertRaises(Blocked):
                    seconds_until_target(now, target)
            with self.assertRaises(Blocked):
                seconds_until_target(now.replace(tzinfo=None), "08:45:00")

        def test_actual_forms_only(self):
            html = '<form id="primary_form" method="post" action="/Login?ReturnUrl=x"><input name="Username"><input type="password" name="Password"><input type="hidden" name="__RequestVerificationToken" value="fixture"></form>'
            action, fields, _ = parse_login_form(html, LOGIN_ORIGIN + "/Login")
            self.assertEqual(action, LOGIN_ORIGIN + "/Login?ReturnUrl=x")
            self.assertEqual(fields["__RequestVerificationToken"], "fixture")
            with self.assertRaisesRegex(Blocked, "returned the password form again"):
                parse_login_form(html, LOGIN_ORIGIN, otp=True)
            for bad in (html.replace('/Login?ReturnUrl=x', 'https://example.com/steal'),
                        html.replace('__RequestVerificationToken', 'missing'), html + 'captcha'):
                with self.assertRaises(Blocked):
                    parse_login_form(bad, LOGIN_ORIGIN)
            otp_html = '<form method="post" action="/server-supplied-action"><input name="server-supplied-field" autocomplete="one-time-code"><input type="hidden" name="__RequestVerificationToken" value="fixture"></form>'
            self.assertEqual(parse_login_form(otp_html, LOGIN_ORIGIN, otp=True)[2][0]["name"], "server-supplied-field")
            with self.assertRaises(Blocked):
                parse_login_form(otp_html.replace('autocomplete="one-time-code"', ''), LOGIN_ORIGIN, otp=True)

        def test_protection_signals_stop_without_logging_html(self):
            for html, expected in (
                ("<title>WAF</title>fixture-private", ["waf_title"]),
                ('<div class="g-recaptcha" data-sitekey="fixture-private"></div>', ["captcha_markup"]),
                ('<script>const captchaNote = "fixture-private";</script>', ["captcha_reference"]),
            ):
                with self.subTest(expected=expected):
                    report = [{"stage": "password"}]
                    with self.assertRaises(Blocked) as caught:
                        parse_login_form(html, LOGIN_ORIGIN, otp=True, report=report)
                    self.assertEqual(report[0]["protection_signals"], expected)
                    self.assertNotIn("fixture-private", json.dumps(report) + str(caught.exception))

        def test_no_orders_can_reach_transport(self):
            opener = Mock()
            for method in (None, {"order": "fixture"}):
                with self.assertRaises(Blocked):
                    request(opener, MONEY_URL.replace('/easy/api/money', '/core/api/v2/order'), [], "test", fields=method)
            with self.assertRaises(Blocked):
                request(opener, MONEY_URL, [], "test", fields={})
            with self.assertRaises(Blocked):
                request(opener, LOGIN_ORIGIN, [], "test", bearer="synthetic-token")
            opener.open.assert_not_called()

        def test_timeout_no_retry_and_safe_report(self):
            opener = Mock()
            opener.open.side_effect = urllib.error.URLError("synthetic-secret")
            report = []
            with self.assertRaises(Blocked) as caught:
                request(opener, MONEY_URL, report, "test", bearer="synthetic-token")
            self.assertNotIn("synthetic-secret", str(caught.exception))
            self.assertNotIn("synthetic-token", json.dumps(report))
            self.assertEqual(opener.open.call_count, 1)
            self.assertEqual(opener.open.call_args.kwargs["timeout"], NETWORK_TIMEOUT_SECONDS)
            self.assertIsNone(report[0]["http_status"])

        def test_response_report_omits_raw_headers_and_body(self):
            opener = Mock()
            response = opener.open.return_value = MagicMock()
            response.__enter__.return_value = response
            response.code = 200
            response.headers = {"Content-Type": "text/html; charset=utf-8", "Set-Cookie": "fixture-cookie"}
            response.read.return_value = b"fixture-account-data"
            report = []
            request(opener, MONEY_URL, report, "account-read", bearer="fixture-token",
                    account_origin="https://m.easytrader.ir")
            sent = opener.open.call_args.args[0]
            self.assertEqual(sent.get_header("Origin"), "https://m.easytrader.ir")
            self.assertEqual(sent.get_header("Referer"), "https://m.easytrader.ir/")
            self.assertEqual(report[0]["response_kind"], "html")
            self.assertNotIn("fixture-", json.dumps(report))

        def test_http_200_is_not_success(self):
            for status, content_type, body in [(200, "text/html", b"<title>WAF</title>"),
                                               (401, "application/json", b'{}'),
                                               (200, "application/json", b'{}'),
                                               (200, "application/json", b'{"isSuccessful":false}'),
                                               (200, "application/json", b'bad')]:
                with self.subTest(body=body), self.assertRaises(Blocked):
                    json_response(status, {"Content-Type": content_type}, body)

        def test_manual_browser_token_uses_only_the_read_only_endpoint(self):
            token = "fixture-browser-access"
            for pasted, expected_exit in (("Bearer " + token, 0),
                                          ("Bearer malformed token", 2),
                                          (getpass.GetPassWarning(), 2)):
                with self.subTest(expected_exit=expected_exit):
                    opener = Mock()
                    response = opener.open.return_value = MagicMock()
                    response.__enter__.return_value = response
                    response.code = 200
                    response.headers = {"Content-Type": "application/json"}
                    response.read.return_value = b'{"buyPowerT2":731953}'
                    output = io.StringIO()
                    with patch(__name__ + ".LIVE_ORDER_ENABLED", False), \
                         patch("builtins.input", side_effect=AssertionError("Unmasked input forbidden")), \
                         patch("getpass.getpass", side_effect=[pasted]), \
                         patch("urllib.request.build_opener", return_value=opener) as build_opener, \
                         contextlib.redirect_stdout(output):
                        self.assertEqual(main(["--browser-token", "--mobile"]), expected_exit)
                    report = json.loads(output.getvalue().splitlines()[-1])
                    self.assertEqual(report["order_requests"], 0)
                    for secret in (token, "malformed token", "731953"):
                        self.assertNotIn(secret, output.getvalue())
                    if expected_exit != 0:
                        build_opener.assert_not_called()
                        self.assertEqual(report["requests"], [])
                        continue
                    build_opener.assert_called_once()
                    self.assertIsInstance(build_opener.call_args.args[0], NoRedirect)
                    opener.open.assert_called_once()
                    sent = opener.open.call_args.args[0]
                    self.assertEqual(sent.get_method(), "GET")
                    self.assertEqual(sent.full_url, MONEY_URL)
                    self.assertEqual(sent.get_header("Authorization"), "Bearer " + token)
                    self.assertEqual(sent.get_header("Origin"), MOBILE_ORIGIN)
                    self.assertEqual([item["stage"] for item in report["requests"]], ["account-read"])

        def test_forbidden_account_token_comparison_stays_local(self):
            def fake_token(claims):
                payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
                return "fixture." + payload + ".signature"

            pkce = fake_token({"scope": "one two", "aud": "fixture-pkce-audience",
                               "client_id": "fixture-pkce-client", "sub": "fixture-user"})
            browser = fake_token({"scope": ["two", "one"], "aud": ["fixture-browser-audience"],
                                  "azp": "fixture-browser-client", "sub": "fixture-user"})
            opener = Mock()
            response = opener.open.return_value = MagicMock()
            response.__enter__.return_value = response
            response.code = 403
            response.headers = {}
            response.read.return_value = b"fixture-private-response"
            report = []
            output = io.StringIO()
            with patch(__name__ + ".LIVE_ORDER_ENABLED", False), \
                 patch("getpass.getpass", return_value="Bearer " + browser), \
                 patch("urllib.request.build_opener", return_value=opener), \
                 contextlib.redirect_stdout(output), self.assertRaisesRegex(Blocked, "HTTP 403"):
                read_money(report, pkce, MOBILE_ORIGIN, compare_browser_token=True)
            opener.open.assert_called_once()
            self.assertEqual(opener.open.call_args.args[0].get_header("Authorization"), "Bearer " + pkce)
            self.assertEqual(report[0]["token_claim_comparison"], {
                "status": "compared", "same": ["scope"], "different": ["aud"],
                "pkce_only": ["client_id"], "browser_only": ["azp"],
            })
            self.assertNotIn("fixture", output.getvalue() + json.dumps(report))
            self.assertEqual(compare_token_claims(pkce, "opaque"), {"status": "claims-unavailable"})

        def test_browser_read_validates_only_the_matching_network_response(self):
            def response(url=MONEY_URL, method="GET", status=200, service_worker=False, media_type="application/json"):
                result = Mock(url=url, status=status, from_service_worker=service_worker,
                              headers={"content-type": media_type})
                result.request.method = method
                return result

            ignored = [
                response(url="https://example.com/easy/api/money"),
                response(method="OPTIONS"),
                response(service_worker=True),
                response(status=403),
                response(media_type="text/html"),
            ]
            accepted = response()
            accepted.body.return_value = b'{"buyPowerT2":731953}'
            api = MagicMock(Error=RuntimeError, TimeoutError=TimeoutError)
            playwright = api.sync_playwright.return_value.__enter__.return_value
            browser = playwright.chromium.launch.return_value
            context = browser.new_context.return_value
            page = context.new_page.return_value
            observed = context.expect_event.return_value.__enter__.return_value
            observed.value = accepted

            def navigate(*args, **kwargs):
                predicate = context.expect_event.call_args.kwargs["predicate"]
                for item in ignored:
                    self.assertFalse(predicate(item))
                self.assertTrue(predicate(accepted))

            page.goto.side_effect = navigate
            output = io.StringIO()
            with patch.dict(sys.modules, {"playwright.sync_api": api}), \
                 patch(__name__ + ".LIVE_ORDER_ENABLED", False), \
                 contextlib.redirect_stdout(output):
                self.assertEqual(main(["--browser-read"]), 0)
            playwright.chromium.launch.assert_called_once_with(channel="chrome", headless=False)
            page.goto.assert_called_once_with(MOBILE_ORIGIN + "/market-watch", wait_until="commit", timeout=30_000)
            browser.close.assert_called_once()
            accepted.body.assert_called_once()
            for item in ignored:
                item.body.assert_not_called()
            report = json.loads(output.getvalue().splitlines()[-1])
            self.assertEqual(report["order_requests"], 0)
            self.assertEqual(len(report["requests"]), 1)
            self.assertEqual(report["requests"][0]["stage"], "browser-account-read")
            self.assertEqual(report["requests"][0]["http_status"], 200)
            self.assertNotIn("731953", output.getvalue())

        def test_draft_observation_reports_shape_without_order_values(self):
            context = MagicMock()
            page = Mock()
            unrelated = Mock(url=ACCOUNT_API_ORIGIN + "/core/api/order", from_service_worker=False)
            response = Mock(url=DRAFT_URL + "?fixture-query", status=200, from_service_worker=False,
                            headers={"content-type": "application/json"})
            response.request.method = "GET"
            response.body.return_value = b'{"drafts":[{"draftId":"fixture-id","price":12345,"fixture-private":true}]}'
            post = Mock(url=DRAFT_URL, status=200, from_service_worker=False, headers=response.headers)
            post.request.method = "POST"
            context.expect_event.return_value.__enter__.return_value.value = response

            def navigate(*args, **kwargs):
                predicate = context.expect_event.call_args.kwargs["predicate"]
                self.assertFalse(predicate(unrelated))
                self.assertFalse(predicate(post))
                self.assertTrue(predicate(response))

            page.goto.side_effect = navigate
            report = {}
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                observe_draft_reads(context, page, report)
            page.goto.assert_called_once_with(DESKTOP_ORIGIN + "/", wait_until="commit", timeout=30_000)
            unrelated.body.assert_not_called()
            post.body.assert_not_called()
            self.assertEqual(report["method"], "GET")
            self.assertEqual(report["path"], "/easy/api/draft")
            self.assertEqual(report["json_shape"], {"root_type": "object", "known_fields": ["drafts"],
                                                   "collections": {"drafts": {"count": 1,
                                                                              "known_item_fields": ["draftId", "price"]}}})
            self.assertNotIn("fixture", output.getvalue() + json.dumps(report))
            self.assertNotIn("12345", output.getvalue() + json.dumps(report))

        def test_draft_preview_selects_only_explicit_distinct_rows(self):
            first = {"id": "fixture-id-one", "symbolName": "FIXTURE ONE", "quantity": 10, "price": 12345, "side": 0}
            second = {"id": "fixture-id-two", "symbolName": "FIXTURE TWO", "quantity": 20, "price": 54321, "side": 1}
            for drafts, selection, exit_code, expected_preview in (
                ([first], "۱", 0, ["FIXTURE ONE"]),
                ([first, second], "۲، ۱", 0, ["FIXTURE TWO", "FIXTURE ONE"]),
                ([first, second], "2,2", 2, []),
                ([first, second], "3", 2, []),
                ([first, {**second, "id": first["id"]}], "1", 2, []),
                ([], "", 0, []),
            ):
                with self.subTest(selection=selection, exit_code=exit_code, count=len(drafts)):
                    output = io.StringIO()
                    with patch(__name__ + ".observe_browser", return_value=drafts) as observe, \
                         patch(__name__ + ".LIVE_ORDER_ENABLED", False), \
                         patch("builtins.input", return_value=selection), \
                         contextlib.redirect_stdout(output):
                        self.assertEqual(main(["--browser-draft-preview"]), exit_code)
                    observe.assert_called_once_with(
                        [{"stage": "draft-preview", "mode": "single" if len(expected_preview) == 1 else "group",
                          "selected_count": len(expected_preview)}] if expected_preview else [],
                        draft_discovery=True,
                    )
                    lines = output.getvalue().splitlines()
                    report = json.loads(lines[-1])
                    self.assertEqual(report["order_requests"], 0)
                    self.assertNotIn("fixture-id", output.getvalue())
                    self.assertNotIn("FIXTURE", lines[-1])
                    if expected_preview:
                        heading = next(index for index, line in enumerate(lines) if line.startswith("Dry-run"))
                        selected = [line.split(". ", 1)[1].split(" | ", 1)[0] for line in lines[heading + 1:-1]]
                        self.assertEqual(selected, expected_preview)
                    else:
                        self.assertFalse(any(line.startswith("Dry-run") for line in lines))

        def test_scheduled_draft_preview_waits_without_a_post_login_prompt(self):
            first = {"id": "fixture-id-one", "symbolName": "FIXTURE ONE", "quantity": 10, "price": 12345, "side": 0}
            second = {**first, "id": "fixture-id-two", "symbolName": "FIXTURE TWO"}
            startup = datetime.fromisoformat("2026-11-04T08:44:56+03:30")
            ready = datetime.fromisoformat("2026-11-04T08:44:59+03:30")
            target = datetime.fromisoformat("2026-11-04T08:45:00+03:30")
            late = datetime.fromisoformat("2026-11-04T08:45:00.012+03:30")
            for timestamps, expected_exit, expected_browser in (
                ([startup, ready, late], 0, True),
                ([startup, late], 2, True),
                ([late], 2, False),
            ):
                with self.subTest(timestamps=timestamps):
                    output = io.StringIO()
                    with patch(__name__ + ".datetime", wraps=datetime) as clock, \
                         patch(__name__ + ".observe_browser", return_value=[first, second]) as observe, \
                         patch(__name__ + ".LIVE_ORDER_ENABLED", False), \
                         patch("builtins.input", side_effect=AssertionError("Unexpected input prompt")), \
                         patch("time.sleep") as sleep, contextlib.redirect_stdout(output):
                        clock.now.side_effect = timestamps
                        self.assertEqual(main(["--browser-draft-schedule", "08:45:00"]), expected_exit)
                    self.assertEqual(observe.call_count, int(expected_browser))
                    report = json.loads(output.getvalue().splitlines()[-1])
                    self.assertEqual(report["order_requests"], 0)
                    if expected_exit == 0:
                        sleep.assert_called_once_with(1)
                        self.assertEqual(observe.call_args.kwargs["scheduled_at"], target)
                        self.assertEqual(report["requests"], [{
                            "stage": "draft-preview", "mode": "group", "selected_count": 2,
                            "target_time": target.isoformat(timespec="milliseconds"),
                            "preview_time": late.isoformat(timespec="milliseconds"),
                        }])
                    else:
                        sleep.assert_not_called()
                        self.assertEqual(report["requests"], [])

        def test_single_order_cli_defaults_to_preview_and_routes_explicit_live(self):
            ready = datetime.fromisoformat("2026-11-07T08:40:00+03:30")
            target = tehran_target(ready, "08:45:00")
            for args, live, mobile in ((["--browser-single-order"], False, False),
                                       (["--browser-single-order", "--live"], True, False),
                                       (["--live", "08:45:00"], True, False),
                                       (["--browser-single-order", "08:45:00", "--live", "--mobile"], True, True)):
                with self.subTest(args=args), patch(__name__ + ".datetime", wraps=datetime) as clock, \
                     patch(__name__ + ".run_single_order_browser", return_value=None) as run, \
                     contextlib.redirect_stdout(io.StringIO()):
                    clock.now.return_value = ready
                    self.assertEqual(main(args), 0)
                    run.assert_called_once_with(None if args in (["--browser-single-order"], ["--browser-single-order", "--live"]) else target, [], live=live, mobile=mobile)

        def test_single_order_rejects_invalid_selection_cap_and_zero_funds(self):
            draft = {"id": "fixture-id", "symbolName": "TEST", "quantity": 1, "price": 100, "side": 0}
            ready = datetime.fromisoformat("2026-11-04T08:44:59+03:30")
            target = tehran_target(ready, "08:45:00")
            for drafts, funds, answers, diagnostic in (
                ([], None, [], "No draft"),
                ([draft, draft], None, [], "identifiers"),
                ([draft], None, ["1,1"], "exactly one"),
                ([draft], None, ["1,2"], "exactly one"),
                ([draft], None, ["2"], "exactly one"),
                ([draft], None, ["1", "0"], "positive whole number"),
                ([draft], None, ["1", "50001"], "exceeds MAX_ORDER_VALUE_IRR"),
                ([{**draft, "price": Decimal("1.5")}], None, ["1", ""], "whole-number draft price"),
                ([draft], 0, ["1", ""], "buying-power field was zero"),
            ):
                with self.subTest(answers=answers, diagnostic=diagnostic), \
                     patch(__name__ + ".datetime", wraps=datetime) as clock, \
                     patch("builtins.input", side_effect=answers), patch("time.sleep") as sleep, \
                     contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(Blocked, diagnostic):
                    clock.now.return_value = ready
                    rehearse_single_order(drafts, funds, target, [])
                sleep.assert_not_called()

        def test_single_order_cli_rejects_expiry_flags_and_global_toggle(self):
            ready = datetime.fromisoformat("2026-11-07T09:00:00+03:30")
            for args, enabled in ((["--live", "08:45:00"], False),
                                  (["--live", "10:00:00", "--live"], False),
                                  (["--browser-single-order", "10:00:00", "--unknown"], False),
                                  (["--browser-single-order", "10:00:00"], True)):
                with self.subTest(args=args, enabled=enabled), \
                     patch(__name__ + ".datetime", wraps=datetime) as clock, \
                     patch(__name__ + ".LIVE_ORDER_ENABLED", enabled), \
                     patch(__name__ + ".run_single_order_browser") as run, \
                     patch("builtins.input") as prompt, contextlib.redirect_stdout(io.StringIO()):
                    clock.now.return_value = ready
                    self.assertEqual(main(args), 2)
                    run.assert_not_called()
                    prompt.assert_not_called()

        def test_single_order_browser_observes_each_read_once_and_ignores_order_responses(self):
            def response(url, body, method="GET", status=200):
                item = Mock(url=url, status=status, from_service_worker=False, headers={"content-type": "application/json"})
                item.request.method = method
                item.body.return_value = body
                return item

            drafts = response(DRAFT_URL, b'[{"id":"fixture-id","symbolName":"TEST","quantity":1,"price":100,"side":0}]')
            duplicate = response(DRAFT_URL, b'[]')
            order_url = ACCOUNT_API_ORIGIN + "/core/api/v2/order"
            orders = [response(order_url, b'{"message":"fixture-private","orderId":"fixture-order"}', "POST", status)
                      for status in (200, 400, 429, 503)]
            unrelated = response("https://example.com/easy/api/money", b'{"buyPowerT2":1}')
            for money_body, expected_power, expected_field in (
                (b'{"buyPowerT2":731953}', 731953, "NUMERIC"),
                (b'{"buyPowerT2":"fixture-private"}', None, "UNVERIFIED"),
                (None, None, None),
            ):
                with self.subTest(money_body=money_body):
                    drafts.reset_mock()
                    api = MagicMock(Error=RuntimeError, TimeoutError=TimeoutError)
                    playwright = api.sync_playwright.return_value.__enter__.return_value
                    browser = playwright.chromium.launch.return_value
                    context = browser.new_context.return_value
                    page = context.new_page.return_value
                    money = response(MONEY_URL, money_body)
                    later_money = response(MONEY_URL, b'{"buyPowerT2":20}')
                    context.expect_event.return_value.__enter__.return_value.value = drafts

                    def navigate(*args, **kwargs):
                        capture = context.on.call_args.args[1]
                        predicate = context.expect_event.call_args.kwargs["predicate"]
                        for item in [unrelated, *orders]:
                            capture(item)
                            self.assertFalse(predicate(item))
                        if money_body is not None:
                            capture(money)
                            capture(later_money)
                        self.assertTrue(predicate(drafts))
                        capture(duplicate)

                    page.goto.side_effect = navigate
                    output, report = io.StringIO(), []
                    with patch.dict(sys.modules, {"playwright.sync_api": api}), contextlib.redirect_stdout(output):
                        payload, power = observe_browser(report, single_order=True)
                    self.assertEqual(payload[0]["id"], "fixture-id")
                    self.assertEqual(power, expected_power)
                    drafts.body.assert_called_once_with()
                    self.assertEqual(money.body.call_count, int(money_body is not None))
                    for item in [unrelated, later_money, duplicate, *orders]:
                        item.body.assert_not_called()
                    context.expect_event.assert_called_once()
                    page.goto.assert_called_once()
                    page.locator.assert_not_called()
                    browser.close.assert_called_once()
                    if expected_field is not None:
                        self.assertEqual(report[-1]["money_field"], expected_field)
                    else:
                        self.assertEqual(len(report), 1)
                    for private in ("fixture-private", "fixture-order", "731953"):
                        self.assertNotIn(private, output.getvalue() + json.dumps(report))

        def test_single_order_browser_timeout_does_not_repeat_observation(self):
            api = MagicMock(Error=RuntimeError, TimeoutError=TimeoutError)
            browser = api.sync_playwright.return_value.__enter__.return_value.chromium.launch.return_value
            context = browser.new_context.return_value
            context.expect_event.return_value.__exit__.side_effect = TimeoutError("fixture-private")
            with patch.dict(sys.modules, {"playwright.sync_api": api}), \
                 contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(Blocked, "Timed out waiting for a draft GET"):
                observe_browser([], single_order=True)
            context.expect_event.assert_called_once()
            browser.close.assert_called_once()

        def test_order_contract_reports_only_allowlisted_fields_from_first_party_gets(self):
            def response(path, body, *, origin=ACCOUNT_API_ORIGIN, method="GET", status=200):
                item = Mock(url=origin + path, status=status, from_service_worker=False,
                            headers={"content-type": "application/json"})
                item.request.method = method
                item.body.return_value = body
                return item

            order_path = "/core/api/order"
            clock_path = "/easy/api/account/server-time/1793823448062"
            for clock_status, clock_body, expected_clock_fields in (
                (200, b'{"serverTimestamp":1793823448062,"diff":3,"token":"fixture-private"}',
                 {"serverTimestamp": "int", "diff": "int"}),
                (200, b'{"fixture-private":', None),
                (403, b'{"serverTimestamp":1793823448062}', None),
            ):
                with self.subTest(clock_status=clock_status, expected_clock_fields=expected_clock_fields):
                    api = MagicMock(Error=RuntimeError, TimeoutError=TimeoutError)
                    browser = api.sync_playwright.return_value.__enter__.return_value.chromium.launch.return_value
                    context = browser.new_context.return_value
                    page = context.new_page.return_value
                    orders = response(order_path, b'{"orders":[{"id":"fixture-private","orderState":7,"trades":[]}]}')
                    clock = response(clock_path, clock_body, status=clock_status)
                    ignored = [response(order_path, b'{}', method="POST"),
                               response(order_path, b'{}', origin="https://example.com"),
                               response("/core/api/v2/order", b'{}', method="POST")]

                    def navigate(*args, **kwargs):
                        predicate = context.expect_event.call_args.kwargs["predicate"]
                        for item in ignored:
                            self.assertFalse(predicate(item))
                        self.assertFalse(predicate(orders))
                        self.assertTrue(predicate(clock))

                    page.goto.side_effect = navigate
                    output = io.StringIO()
                    with patch.dict(sys.modules, {"playwright.sync_api": api}), contextlib.redirect_stdout(output):
                        self.assertEqual(main(["--browser-order-contract"]), 0)
                    for item in ignored:
                        item.body.assert_not_called()
                    orders.body.assert_called_once_with()
                    self.assertEqual(clock.body.call_count, int(clock_status == 200))
                    browser.close.assert_called_once()
                    self.assertNotIn("fixture-private", output.getvalue())
                    self.assertNotIn("1793823448062", output.getvalue())
                    report = json.loads(output.getvalue().splitlines()[-1])
                    self.assertEqual(report["order_requests"], 0)
                    order_read, clock_read = report["requests"]
                    self.assertEqual(order_read["field_types"], {"orders": "list"})
                    self.assertEqual(order_read["first_order_field_types"],
                                     {"id": "str", "orderState": "int", "trades": "list"})
                    self.assertEqual(clock_read["path"], "/easy/api/account/server-time/{client-ms}")
                    self.assertEqual(clock_read["http_status"], clock_status)
                    self.assertEqual(clock_read["field_types"] if "field_types" in clock_read else None,
                                     expected_clock_fields)

        def test_live_cli_reports_actual_dispatch_count_without_claiming_acceptance(self):
            def run(target, report, **kwargs):
                report.extend([{"stage": "order-submit", "acceptance": "UNOBSERVED"} for _ in range(3)])
                return {"acceptance": "UNOBSERVED", "attempts": 3}
            output = io.StringIO()
            with patch(__name__ + ".run_single_order_browser", side_effect=run), contextlib.redirect_stdout(output):
                self.assertEqual(main(["--browser-single-order", "--live"]), 0, output.getvalue())
            self.assertEqual(json.loads(output.getvalue().splitlines()[-1]), {"order_requests": 3, "acceptance": "UNOBSERVED"})

        def buy_fixture(self):
            at = datetime.fromisoformat("2026-11-07T09:00:00+03:30")
            draft = {"id": "fixture-draft", "symbolIsin": "IRT1TEST0001", "symbolName": "OLD NAME",
                     "price": 56593, "quantity": 22, "side": 0, "validityType": 0,
                     "orderModelType": 2, "createDateTime": "old-draft-time", "easyState": 8}
            symbol = {"symbolIsin": draft["symbolIsin"], "symbolName": "FIXTURE", "isActive": True,
                      "canBuy": True, "marketUnit": 4, "buyCommission": "0.00036875", "hidePrice": 0,
                      "csize": None, "minDealablePrice": 1, "minDealableCount": 1,
                      "minValidBuyVolume": 1, "maxValidBuyVolume": 1_000_000, "tradingTimeType": 13}
            market = {"symbolIsin": draft["symbolIsin"], "stateCode": "A", "lowAllowedPrice": 54825,
                      "highAllowedPrice": 58215, "minValidBuyVolume": 1, "maxValidBuyVolume": 1_000_000}
            calendar = {"items": [{"tradingTimeType": 13, "days": [1, 2, 3, 4, 5],
                                   "startPreTradingTime": "08:45", "endPreTradingTime": "09:00",
                                   "startTradingTime": "09:00", "endTradingTime": "15:00"}]}
            start = {"serverTime": "2026-11-07T08:59:00+03:30", "startSessionTimeStamp": "2026-11-07T08:30:00+03:30"}
            return at, draft, symbol, market, calendar, start

        def fixture_order(self, *, quantity=22, price=56593, origin=DESKTOP_ORIGIN, **kwargs):
            at, draft, symbol, market, calendar, start = self.buy_fixture()
            return build_buy_order(draft, symbol, market, Decimal(10_000_000), quantity, price,
                                   origin, at, calendar, start, **kwargs)

        def json_response(self, data, status=200):
            response = Mock(status=status, headers={"content-type": "application/json"})
            response.body.return_value = json.dumps(data).encode()
            return response

        def workflow_session(self):
            at, draft, symbol, market, calendar, start = self.buy_fixture()
            session = Mock(origin=DESKTOP_ORIGIN)
            def read(url, body=None):
                if url == DRAFT_URL:
                    return [dict(draft), {**draft, "id": "fixture-sell", "side": 1}]
                if url == SYMBOLS_URL:
                    self.assertEqual(body, '{"hash":"null"}')
                    return {"symbols": [dict(symbol)], "hash": "fixture-hash"}
                if url == MARKET_DATA_URL:
                    self.assertEqual(json.loads(body), [draft["symbolIsin"]])
                    return [dict(market)]
                if url == MONEY_URL:
                    return {"buyPowerT2": 10_000_000}
                if url == TRADING_TIME_URL:
                    return calendar
                if url == START_SESSION_URL:
                    return start
                if url == ORDERS_URL:
                    return {"orders": [{"id": "fixture-order", "symbolIsin": draft["symbolIsin"]}]}
                self.fail("Unexpected read/write endpoint")
            session.read.side_effect = read
            session.submit.return_value = self.json_response({"isSuccessful": True, "id": "fixture-order", "message": "", "omsError": None})
            return at, session

        @contextlib.contextmanager
        def scheduled_console(self, target, key="\r"):
            with patch(__name__ + ".prompt_order_time", return_value=target), \
                 patch(__name__ + ".prompt_submission_window", return_value=SubmissionWindow(5_000_000_000, 350_000)), \
                 patch(__name__ + ".console_keys", return_value=contextlib.nullcontext(lambda wait=False: key if wait else None)):
                yield

        def test_new_order_sources_decimal_formula_and_draft_immutability(self):
            import copy
            at, draft, symbol, market, calendar, start = self.buy_fixture()
            original = copy.deepcopy((draft, symbol, market))
            for quantity, price, expected in ((20, 56592, 1132258), (22, 56593, 1245506)):
                order = build_buy_order(draft, symbol, market, 10_000_000, quantity, price,
                                        DESKTOP_ORIGIN, at, calendar, start)
                payload = order.payload(at)["order"]
                self.assertEqual(order.total_value, expected)
                self.assertEqual(order.contract_size, Decimal(1))
                self.assertEqual(payload["commission"], Decimal("0.00036875"))
                self.assertEqual(payload["symbolName"], "FIXTURE")
                self.assertEqual((payload["orderModelType"], payload["orderFrom"], payload["side"], payload["validityType"]), (1, 34, 0, 0))
                self.assertEqual(payload["createDateTime"], "11/7/2026, 9:00:00 AM")
                self.assertTrue({"id", "easyState", "validityDate"}.isdisjoint(payload))
                serialized = decimal_json({"order": payload})
                self.assertIn('"commission":0.00036875', serialized)
                self.assertEqual(json.loads(serialized, parse_float=Decimal)["order"]["price"], price)
            self.assertEqual((draft, symbol, market), original)
            self.assertEqual(self.fixture_order(origin=MOBILE_ORIGIN).order_from, 33)

        def test_total_formula_uses_hidden_price_size_and_ceiling_without_float(self):
            at, draft, symbol, market, calendar, start = self.buy_fixture()
            symbol.update(hidePrice="0.0123456789", csize="1.0000000001")
            order = build_buy_order(draft, symbol, market, 10_000_000, 22, 56593,
                                    DESKTOP_ORIGIN, at, calendar, start)
            self.assertEqual(order.total_value, 1245506)
            symbol.update(hidePrice=100, csize=2)
            order = build_buy_order(draft, symbol, market, 10_000_000, 22, 56593,
                                    DESKTOP_ORIGIN, at, calendar, start)
            self.assertEqual(order.total_value, 2495411)
            for funds, cap in ((1245505, 5_000_000), (10_000_000, 1245046)):
                with self.assertRaises(Blocked):
                    build_buy_order(draft, {**symbol, "hidePrice": 0, "csize": None}, market, funds,
                                    22, 56593, DESKTOP_ORIGIN, at, calendar, start, limit=cap)

        def test_new_order_fails_closed_on_missing_rules_flags_bounds_and_unknown_context(self):
            cases = [({"isActive": False}, {}), ({"canBuy": "true"}, {}), ({"buyCommission": None}, {}),
                     ({"buyCommission": "NaN"}, {}), ({"buyCommission": "1"}, {}), ({"hidePrice": None}, {}),
                     ({"csize": 0}, {}), ({"marketUnit": 45}, {}), ({"marketUnit": 999}, {}),
                     ({"minDealablePrice": 10}, {}), ({"minDealableCount": 3}, {}),
                     ({"minValidBuyVolume": 23}, {}), ({"maxValidBuyVolume": 21}, {}),
                     ({}, {"highAllowedPrice": 56592}), ({}, {"lowAllowedPrice": None}),
                     ({}, {"stateCode": "I"}), ({}, {"stateCode": "unknown"}), ({}, {"maxValidBuyVolume": 21})]
            for symbol_changes, market_changes in cases:
                at, draft, symbol, market, calendar, start = self.buy_fixture()
                with self.subTest(symbol=symbol_changes, market=market_changes), self.assertRaises(Blocked):
                    build_buy_order(draft, {**symbol, **symbol_changes}, {**market, **market_changes},
                                    10_000_000, 22, 56593, DESKTOP_ORIGIN, at, calendar, start)
            at, draft, symbol, market, calendar, start = self.buy_fixture()
            for changes in ({"side": 1}, {"side": False}, {"validityType": 1}, {"symbolIsin": "wrong"}):
                with self.subTest(changes=changes), self.assertRaises(Blocked):
                    build_buy_order({**draft, **changes}, symbol, market, 10_000_000, 22, 56593,
                                    DESKTOP_ORIGIN, at, calendar, start)
            for value in (None, True, 1.1, "NaN", "Infinity", "1,2", "-1"):
                with self.subTest(value=value), self.assertRaises(Blocked):
                    decimal_value(value, "fixture", positive=True)
            for items in ([], [symbol, symbol], {"unknown": [symbol]}, [{**symbol, "symbolIsin": "wrong"}]):
                with self.assertRaises(Blocked):
                    exact_symbol(items, draft["symbolIsin"])
            self.assertEqual(decimal_value("0", "zero fee"), Decimal(0))

        def test_symbols_frontend_post_contract_uses_signed_in_page_and_wrapped_response(self):
            _, draft, symbol, *_ = self.buy_fixture()
            self.assertEqual(SYMBOLS_URL, "https://api-mts.orbis.easytrader.ir/symbols/api/symbols/all")
            self.assertEqual(json.loads(SYMBOLS_REQUEST_BODY), {"hash": "null"})
            context, page, report = Mock(), Mock(url=DESKTOP_ORIGIN + "/orders"), []
            session = BrowserOrderSession(context, page, report)
            session.seed_drafts([draft])
            session._set_auth({"authorization": "Bearer fixture-secret", "x-device-id": "fixture-device",
                               "x-app-name": "fixture-app", "cookie": "fixture-cookie"})
            page.evaluate.return_value = {
                "kind": "response", "status": 200, "contentType": "application/json; charset=utf-8",
                "body": json.dumps({"symbols": [{**symbol, "symbolIsin": "unrelated"}, symbol], "hash": "fixture-hash"})}
            result = symbol_details(session.read(SYMBOLS_URL, SYMBOLS_REQUEST_BODY), draft["symbolIsin"])
            self.assertEqual(result, symbol)
            script, options = page.evaluate.call_args.args
            self.assertEqual((options["method"], options["url"], options["body"]),
                             ("POST", SYMBOLS_URL, '{"hash":"null"}'))
            self.assertEqual(options["headers"]["Content-Type"], "application/json")
            self.assertEqual(options["headers"]["authorization"], "Bearer fixture-secret")
            self.assertEqual(options["headers"]["x-device-id"], "fixture-device")
            self.assertEqual(options["headers"]["x-app-name"], "fixture-app")
            self.assertNotIn("cookie", options["headers"])
            self.assertIn("credentials: 'include'", script)
            self.assertEqual(options["maxBytes"], MAX_SYMBOL_RESPONSE_BYTES)
            self.assertEqual(report[0]["http_status"], 200)
            self.assertEqual(run_report(report)["order_requests"], 0)
            self.assertNotIn("fixture-secret", json.dumps(report))
            context.request.get.assert_not_called()
            context.request.post.assert_not_called()

        def test_symbols_response_requires_full_wrapped_array_and_exact_isin(self):
            _, draft, symbol, *_ = self.buy_fixture()
            for payload in ([symbol], {}, {"symbols": None}, {"symbols": {}}, {"symbols": []},
                            {"symbols": [symbol, symbol]},
                            {"symbols": [{**symbol, "symbolIsin": symbol["symbolIsin"] + "-suffix"}]},
                            {"symbols": [{**symbol, "symbolIsin": "different", "companyIsin": symbol["symbolIsin"]}]}):
                with self.subTest(payload=payload), self.assertRaises(Blocked):
                    symbol_details(payload, draft["symbolIsin"])
            result = symbol_details({"symbols": [symbol], "hash": "fixture-hash"}, draft["symbolIsin"])
            self.assertIsNot(result, symbol)
            self.assertEqual(result["buyCommission"], symbol["buyCommission"])

        def test_symbols_405_failure_stops_before_approval_without_retry_or_order(self):
            _, draft, *_ = self.buy_fixture()
            # Reproduce the observed 405 as an HTTP failure, never as missing symbol data.
            with self.assertRaisesRegex(HttpResponseFailure, "HTTP 405"):
                browser_json(self.json_response({"message": "Method Not Allowed"}, 405))
            for content_type in ("application/json", "text/html"):
                context, page, report = Mock(), Mock(url=DESKTOP_ORIGIN + "/orders"), []
                session = BrowserOrderSession(context, page, report)
                session.seed_drafts([{**draft, "id": "fixture-" + str(i), "quantity": 23} for i in range(4)])
                page.evaluate.return_value = {"kind": "response", "status": 405, "contentType": content_type,
                                              "body": "fixture-private-response"}
                with self.subTest(content_type=content_type), patch("builtins.input", return_value="4") as prompt, \
                     contextlib.redirect_stdout(io.StringIO()), \
                     self.assertRaisesRegex(HttpResponseFailure, "POST /symbols/api/symbols/all:.*HTTP 405"):
                    single_order_workflow(session, None, report, live=True)
                page.evaluate.assert_called_once()
                self.assertEqual(page.evaluate.call_args.args[1]["method"], "POST")
                prompt.assert_called_once()  # Only draft selection, no approval after failed validation.
                self.assertEqual(report[0]["http_status"], 405)
                self.assertEqual(report[0]["failure_kind"], "http_response")
                self.assertEqual(run_report(report)["order_requests"], 0)
                self.assertNotIn("fixture-private-response", json.dumps(report))
                context.request.get.assert_not_called()
                context.request.post.assert_not_called()

        def test_symbols_get_and_conditional_cache_requests_are_blocked_locally(self):
            session = BrowserOrderSession(Mock(), Mock(url=DESKTOP_ORIGIN + "/orders"))
            session.seed_drafts([])
            with self.assertRaisesRegex(Blocked, "allowlist"):
                session.read(SYMBOLS_URL)  # The old GET that produced HTTP 405 must not be sent.
            for body in ('{}', '{"hash":null}', '{"hash":"fixture-cached-hash"}', '["IRT1TEST0001"]'):
                with self.subTest(body=body), self.assertRaisesRegex(Blocked, "full-refresh POST body"):
                    session.read(SYMBOLS_URL, body)
            session.page.evaluate.assert_not_called()

        def test_calendar_uses_broker_day_and_verified_windows_with_exclusive_end(self):
            import copy
            at, _, symbol, _, calendar, start = self.buy_fixture()
            validate_trading_time(symbol, calendar, start, at.replace(hour=8, minute=45))
            for moment in (at.replace(hour=8, minute=44), at.replace(hour=15), at + timedelta(days=1)):
                with self.assertRaises(Blocked):
                    validate_trading_time(symbol, calendar, start, moment)
            for changes in ({"days": []}, {"days": [True]}, {"days": [2]}, {"startTradingTime": "bad"}):
                altered = copy.deepcopy(calendar)
                altered["items"][0].update(changes)
                with self.assertRaises(Blocked):
                    validate_trading_time(symbol, altered, start, at)
            with self.assertRaises(Blocked):
                validate_trading_time(symbol, calendar, {**start, "startSessionTimeStamp": "2026-11-06T08:30:00"}, at)

        def test_preview_keeps_draft_snapshot_and_shows_per_order_total_without_dispatch(self):
            at, session = self.workflow_session()
            report, output = [], io.StringIO()
            with self.scheduled_console(at), patch(__name__ + ".datetime", wraps=datetime) as clock,           patch("builtins.input", side_effect=["1", "23", "56594"]),           patch(__name__ + ".dispatch_order_window") as dispatch, contextlib.redirect_stdout(output):
                clock.now.return_value = at - timedelta(minutes=1)
                single_order_workflow(session, None, report)
            dispatch.assert_not_called()
            session.submit.assert_not_called()
            self.assertEqual(sum(c.args[0] == DRAFT_URL for c in session.read.call_args_list), 1)
            self.assertEqual(session.read.call_count, 6)
            self.assertIn("Quantity: 23", output.getvalue())
            self.assertIn("Unit price: 56,594", output.getvalue())
            self.assertIn("Total per order including commission", output.getvalue())
            self.assertNotIn("fixture-draft", output.getvalue())
            self.assertEqual(run_report(report)["order_requests"], 0)

        def test_scheduled_workflow_revalidates_then_dispatches_one_authorized_window(self):
            at, session = self.workflow_session()
            current, report = [at - timedelta(minutes=1)], []
            def wait(target, active, **kwargs):
                self.assertIs(active, session)
                current[0] = target
            with self.scheduled_console(at), patch(__name__ + ".datetime", wraps=datetime) as clock,           patch(__name__ + ".wait_local_target", side_effect=wait) as timer,           patch(__name__ + ".dispatch_order_window", return_value={"acceptance": "UNOBSERVED"}) as dispatch,           patch("builtins.input", side_effect=["1", "", ""]), contextlib.redirect_stdout(io.StringIO()):
                clock.now.side_effect = lambda *_: current[0]
                result = single_order_workflow(session, None, report, live=True)
            self.assertEqual(result["acceptance"], "UNOBSERVED")
            dispatch.assert_called_once()
            self.assertTrue(dispatch.call_args.kwargs["approved"])
            self.assertEqual(dispatch.call_args.args[2], at)
            self.assertEqual(dispatch.call_args.args[3], SubmissionWindow(5_000_000_000, 350_000))
            self.assertEqual(sum(c.args[0] == DRAFT_URL for c in session.read.call_args_list), 1)
            self.assertEqual(sum(c.args[0] == SYMBOLS_URL for c in session.read.call_args_list), 2)
            self.assertEqual(session.read.call_count, 11)
            self.assertEqual(timer.call_count, 2)
            session.submit.assert_not_called()

        def test_escape_or_changed_preflight_cannot_start_dispatch(self):
            at, session = self.workflow_session()
            original_read, count = session.read.side_effect, [0]
            def changed_read(url, body=None):
                result = original_read(url, body)
                if url == SYMBOLS_URL:
                    count[0] += 1
                    if count[0] == 2:
                        result["symbols"][0]["buyCommission"] = "0.0004"
                return result
            session.read.side_effect = changed_read
            with self.scheduled_console(at), patch(__name__ + ".datetime", wraps=datetime) as clock,           patch(__name__ + ".wait_local_target"), patch(__name__ + ".dispatch_order_window") as dispatch,           patch("builtins.input", side_effect=["1", "", ""]), contextlib.redirect_stdout(io.StringIO()),           self.assertRaisesRegex(Blocked, "changed since approval"):
                clock.now.return_value = at - timedelta(seconds=20)
                single_order_workflow(session, at, [], live=True)
            dispatch.assert_not_called()
            at, session = self.workflow_session()
            with self.scheduled_console(at, key="\x1b"), patch(__name__ + ".datetime", wraps=datetime) as clock,           patch("builtins.input", side_effect=["1", "", ""]),           patch(__name__ + ".wait_local_target") as wait, patch(__name__ + ".dispatch_order_window") as dispatch,           contextlib.redirect_stdout(io.StringIO()):
                clock.now.return_value = at - timedelta(seconds=20)
                single_order_workflow(session, at, [], live=True)
            dispatch.assert_not_called()
            wait.assert_not_called()

        def test_sender_ack_errors_uncertainty_and_no_second_attempt(self):
            at, *_ = self.buy_fixture()
            cases = [({"isSuccessful": True, "id": "fixture-order"}, 200, "ACCEPTED"),
                     ({"isSuccessful": False, "message": "Rejected", "omsError": [{"error": "bad quantity"}]}, 400, "REJECTED"),
                     ({"isSuccessful": True, "id": "bad\nid"}, 200, "UNCERTAIN"),
                     ({"isSuccessful": True, "id": "fixture-order"}, 500, "UNCERTAIN"),
                     ({"message": "unknown"}, 200, "UNCERTAIN")]
            for data, status, expected in cases:
                session = Mock(origin=DESKTOP_ORIGIN)
                session.submit.return_value = self.json_response(data, status)
                sender, report = OneShotOrder(), []
                with self.subTest(status=status, data=data), patch(__name__ + ".datetime", wraps=datetime) as clock:
                    clock.now.return_value = at
                    result = sender.submit(session, self.fixture_order(), at, report, approved=True)
                    self.assertEqual(result["acceptance"], expected)
                    with self.assertRaises(Blocked):
                        sender.submit(session, self.fixture_order(), at, report, approved=True)
                session.submit.assert_called_once()
                self.assertEqual(run_report(report)["order_requests"], 1)
            session = Mock(origin=DESKTOP_ORIGIN)
            session.submit.side_effect = TimeoutError("Bearer fixture-private-token")
            sender, report = OneShotOrder(), []
            with patch(__name__ + ".datetime", wraps=datetime) as clock:
                clock.now.return_value = at
                self.assertEqual(sender.submit(session, self.fixture_order(), at, report, approved=True)["acceptance"], "UNCERTAIN")
                with self.assertRaises(Blocked):
                    sender.submit(session, self.fixture_order(), at, report, approved=True)
            session.submit.assert_called_once()
            self.assertNotIn("fixture-private-token", json.dumps(report))

        def test_sender_requires_approval_context_and_on_time_dispatch(self):
            at, *_ = self.buy_fixture()
            for approved, now, origin in ((False, at, DESKTOP_ORIGIN),
                                           (True, at - timedelta(seconds=1), DESKTOP_ORIGIN),
                                           (True, at + timedelta(seconds=3), DESKTOP_ORIGIN),
                                           (True, at, MOBILE_ORIGIN)):
                session, report = Mock(origin=origin), []
                with self.subTest(approved=approved, now=now, origin=origin), \
                     patch(__name__ + ".datetime", wraps=datetime) as clock, self.assertRaises(Blocked):
                    clock.now.return_value = now
                    OneShotOrder().submit(session, self.fixture_order(), at, report, approved=approved)
                session.submit.assert_not_called()
                self.assertEqual(run_report(report)["order_requests"], 0)

        def test_browser_transport_reuses_only_memory_auth_and_has_no_redirects_or_retries(self):
            context, page = Mock(), Mock(url=DESKTOP_ORIGIN + "/")
            session = BrowserOrderSession(context, page)
            response = Mock(url=MONEY_URL, status=200, from_service_worker=False,
                            headers={"content-type": "application/json"})
            response.request.method = "GET"
            response.request.all_headers.return_value = {"authorization": "Bearer fixture-secret", "cookie": "fixture-cookie"}
            self.assertTrue(session.capture_auth(response))
            context.request.get.side_effect = AssertionError("APIRequestContext is not the Chrome transport")
            page.evaluate.return_value = {"kind": "response", "status": 200, "contentType": "application/json",
                                          "body": '{"buyPowerT2":5000000}'}
            self.assertEqual(session.read(MONEY_URL)["buyPowerT2"], 5_000_000)
            script, options = page.evaluate.call_args.args
            self.assertIn("credentials: 'include'", script)
            self.assertIn("redirect: 'error'", script)
            self.assertEqual(script.count("await fetch("), 1)
            self.assertNotIn("cookie", options["headers"])
            self.assertNotIn("Origin", options["headers"])
            context.request.get.assert_not_called()
            for url in (ORDER_URL, "https://example.com/", DRAFT_URL + "/fixture-id"):
                with self.assertRaises(Blocked):
                    session.read(url)
            context.request.post.assert_not_called()
            with self.assertRaises(Blocked):
                session._request("DELETE", DRAFT_URL)
            with self.assertRaises(Blocked):
                session._request("POST", DRAFT_URL, "{}")

        def test_browser_cleanup_runs_after_workflow_or_failure_without_close_prompt(self):
            at, *_ = self.buy_fixture()
            for failure in (False, True):
                api = MagicMock(Error=RuntimeError, TimeoutError=TimeoutError)
                browser = api.sync_playwright.return_value.__enter__.return_value.chromium.launch.return_value
                with self.subTest(failure=failure), patch.dict(sys.modules, {"playwright.sync_api": api}),               patch(__name__ + ".login_then_close_window", return_value=Mock()),               patch(__name__ + ".single_order_workflow", side_effect=Blocked("fixture") if failure else None) as run,               patch("builtins.input", side_effect=AssertionError("No CLOSE prompt")), contextlib.redirect_stdout(io.StringIO()):
                    if failure:
                        with self.assertRaises(Blocked):
                            run_single_order_browser(at, [], live=True)
                    else:
                        run_single_order_browser(at, [], live=True)
                run.assert_called_once()
                browser.close.assert_called_once()

        def test_browser_close_driver_failure_preserves_result_and_sanitizes_error(self):
            api = MagicMock(Error=RuntimeError, TimeoutError=TimeoutError)
            browser = api.sync_playwright.return_value.__enter__.return_value.chromium.launch.return_value
            browser.close.side_effect = Exception("Connection closed; Authorization: Bearer fixture-secret")
            report, output = [], io.StringIO()
            with patch.dict(sys.modules, {"playwright.sync_api": api}),           patch(__name__ + ".login_then_close_window", return_value=Mock()),           patch(__name__ + ".single_order_workflow", return_value={"acceptance": "UNOBSERVED"}),           contextlib.redirect_stdout(output):
                self.assertEqual(run_single_order_browser(None, report, live=True), {"acceptance": "UNOBSERVED"})
            self.assertEqual(report[-1]["stage"], "browser-cleanup")
            self.assertNotIn("fixture-secret", json.dumps(report) + output.getvalue())

        def test_error_sanitization_never_exports_credentials_or_raw_acknowledgement(self):
            message = 'Rejected; authorization: Bearer fixture-secret; "access_token": "another-secret"'
            self.assertNotIn("fixture-secret", safe_text(message))
            self.assertNotIn("another-secret", safe_text(message))
            self.assertNotIn("fixture-cookie", safe_text("cookie=fixture-cookie"))
            at, *_ = self.buy_fixture()
            session = Mock(origin=DESKTOP_ORIGIN)
            session.submit.return_value = self.json_response({"isSuccessful": False, "message": message,
                                                             "private": "fixture-private"}, 429)
            with patch(__name__ + ".datetime", wraps=datetime) as clock:
                clock.now.return_value = at
                report = []
                OneShotOrder().submit(session, self.fixture_order(), at, report, approved=True)
            for secret in ("fixture-secret", "another-secret", "fixture-private"):
                self.assertNotIn(secret, json.dumps(run_report(report)))

        def test_explicit_zero_bound_persian_name_and_decimal_tick_are_not_missing_data(self):
            at, draft, symbol, market, calendar, start = self.buy_fixture()
            symbol.update(symbolName="FIXTURE\u200cNAME", minDealablePrice="0.000000000000000001")
            market["lowAllowedPrice"] = 0
            order = build_buy_order(draft, symbol, market, 10_000_000, 22, "56593.000000000000000001",
                                    DESKTOP_ORIGIN, at, calendar, start)
            self.assertEqual(order.symbol_name, symbol["symbolName"])
            self.assertEqual(order.price, Decimal("56593.000000000000000001"))
            self.assertEqual(order.total_value, 1245506)
            with self.assertRaises(Blocked):
                build_buy_order(draft, symbol, {**market, "lowAllowedPrice": None}, 10_000_000,
                                22, 56593, DESKTOP_ORIGIN, at, calendar, start)

        def test_read_failure_and_html_ack_are_sanitized_and_never_retried(self):
            context, page, report = Mock(), Mock(url=DESKTOP_ORIGIN + "/"), []
            session = BrowserOrderSession(context, page, report)
            session._auth_headers = {"authorization": "Bearer fixture-secret"}
            page.evaluate.side_effect = TimeoutError("Authorization: Bearer fixture-secret")
            with self.assertRaisesRegex(BrowserTransportFailure, "POST /symbols/api/symbols/all: TimeoutError"):
                session.read(SYMBOLS_URL, SYMBOLS_REQUEST_BODY)
            page.evaluate.assert_called_once()
            context.request.get.assert_not_called()
            self.assertEqual(report[0]["failure_kind"], "browser_transport")
            self.assertNotIn("fixture-secret", json.dumps(report))
            at, *_ = self.buy_fixture()
            active = Mock(origin=DESKTOP_ORIGIN)
            active.submit.return_value = Mock(status=200, headers={"content-type": "text/html"})
            attempts = []
            with patch(__name__ + ".datetime", wraps=datetime) as clock:
                clock.now.return_value = at
                result = OneShotOrder().submit(active, self.fixture_order(), at, attempts, approved=True)
            self.assertEqual(result["acceptance"], "UNCERTAIN")
            active.submit.assert_called_once()
            active.submit.return_value.body.assert_not_called()

        def test_keyboard_interrupt_after_attempt_is_reported_as_uncertain_not_zero(self):
            at, *_ = self.buy_fixture()
            def interrupted(target, report, **kwargs):
                active = Mock(origin=DESKTOP_ORIGIN)
                active.submit.side_effect = KeyboardInterrupt()
                OneShotOrder().submit(active, self.fixture_order(), at, report, approved=True)
            output = io.StringIO()
            with patch(__name__ + ".datetime", wraps=datetime) as clock, \
                 patch(__name__ + ".run_single_order_browser", side_effect=interrupted), contextlib.redirect_stdout(output):
                # Main sees a future target; the mocked transport reaches that target before dispatch.
                clock.now.side_effect = [at - timedelta(minutes=1), at]
                self.assertEqual(main(["--live", "09:00:00"]), 130)
            result = json.loads(output.getvalue().splitlines()[-1])
            self.assertEqual(result["order_requests"], 1)
            self.assertEqual(result["acceptance"], "UNCERTAIN")
            self.assertNotIn("No order request was sent", output.getvalue())

        def test_immediate_cli_does_not_default_to_past_0845(self):
            now = datetime.fromisoformat("2026-11-07T14:10:00+03:30")
            with patch(__name__ + ".datetime", wraps=datetime) as clock, \
                 patch(__name__ + ".run_single_order_browser", return_value=None) as run, \
                 contextlib.redirect_stdout(io.StringIO()):
                clock.now.return_value = now
                self.assertEqual(main(["--browser-single-order", "--live"]), 0)
            run.assert_called_once_with(None, [], live=True, mobile=False)

        def test_login_handoff_closes_private_window_before_prompts_and_dispatches_without_responses(self):
            at, draft, symbol, market, calendar, start = self.buy_fixture()
            draft.update(quantity=23, price=56592)
            drafts = [{**draft, "id": f"fixture-draft-{i}"} for i in range(1, 5)]
            api = MagicMock(Error=RuntimeError, TimeoutError=TimeoutError)
            chromium = api.sync_playwright.return_value.__enter__.return_value.chromium
            visible, background = MagicMock(), MagicMock()
            chromium.launch.side_effect = [visible, background]
            context, hidden_context = visible.new_context.return_value, background.new_context.return_value
            page, hidden = context.new_page.return_value, hidden_context.new_page.return_value
            page.url = hidden.url = DESKTOP_ORIGIN + "/"
            response = Mock(url=MONEY_URL, status=200, from_service_worker=False, headers={"content-type": "application/json"})
            response.request.method = "GET"
            response.request.all_headers.return_value = {}
            response.body.return_value = b'{"buyPowerT2":10000000}'
            context.expect_event.return_value.__enter__.return_value.value = response
            context.storage_state.return_value = {"cookies": [], "origins": []}
            page.evaluate.side_effect = [{"fixture-session": "fixture-value"}, "fixture-agent"]
            def navigate(*args, **kwargs):
                predicate = context.expect_event.call_args.kwargs["predicate"]
                unauthorized = Mock(url=MONEY_URL, status=401, from_service_worker=False, headers={"content-type": "application/json"})
                unauthorized.request.method = "GET"
                self.assertFalse(predicate(unauthorized))
                self.assertTrue(predicate(response))
            page.goto.side_effect = navigate
            handlers, evaluations = {}, []
            hidden.on.side_effect = lambda event, callback: handlers.update({event: callback})
            payloads = {DRAFT_URL: drafts, SYMBOLS_URL: {"symbols": [symbol], "hash": "fixture"},
                        MARKET_DATA_URL: [market], MONEY_URL: {"buyPowerT2": 10_000_000},
                        TRADING_TIME_URL: calendar, START_SESSION_URL: start}
            def evaluate(script, options):
                if script == BURST_DISPATCH_SCRIPT:
                    self.assertEqual(options["url"], ORDER_URL)
                    self.assertEqual(options["durationMs"], 5000)
                    self.assertEqual(options["intervalMs"], 0.35)
                    body = json.loads(options["body"])["order"]
                    self.assertEqual((body["quantity"], body["price"], body["totalValue"], body["orderModelType"]), (23, 56592, 1302096, 1))
                    for i in range(1, 4):
                        handlers["console"](Mock(type="log", text="POC_DISPATCH " + json.dumps({"attempt": i, "elapsed_us": i * 350})))
                    return {"attempts": 3, "responses_checked": 0}
                evaluations.append((options["method"], options["url"]))
                if options["url"] == SYMBOLS_URL:
                    self.assertEqual((options["method"], options["body"]), ("POST", '{"hash":"null"}'))
                return {"kind": "response", "status": 200, "contentType": "application/json", "body": json.dumps(payloads[options["url"]])}
            hidden.evaluate.side_effect = evaluate
            current, output = [at - timedelta(minutes=1)], io.StringIO()
            answers = iter(["4", "23", "56592", "9", "0", "0", "", ""])
            def answer(prompt):
                visible.close.assert_called_once()
                background.close.assert_not_called()
                return next(answers)
            def wait(target, session, **kwargs):
                current[0] = target
            with patch.dict(sys.modules, {"playwright.sync_api": api}), \
                 patch(__name__ + ".datetime", wraps=datetime) as clock, \
                 patch(__name__ + ".local_now", side_effect=lambda: current[0]), \
                 patch(__name__ + ".wait_local_target", side_effect=wait), \
                 patch(__name__ + ".console_keys", return_value=contextlib.nullcontext(lambda wait=False: "\r" if wait else None)), \
                 patch("builtins.input", side_effect=answer), contextlib.redirect_stdout(output):
                clock.now.side_effect = lambda *_: current[0]
                self.assertEqual(main(["--browser-single-order", "--live"]), 0, output.getvalue())
            self.assertEqual(json.loads(output.getvalue().splitlines()[-1]), {"order_requests": 3, "acceptance": "UNOBSERVED"})
            self.assertEqual(evaluations.count(("GET", DRAFT_URL)), 1)
            self.assertFalse(any(url == ORDERS_URL for _, url in evaluations))
            self.assertEqual(evaluations.count(("POST", SYMBOLS_URL)), 2)
            self.assertEqual(output.getvalue().count("POST started"), 3)
            self.assertNotIn("fixture-value", output.getvalue())
            self.assertNotIn("CLOSE", output.getvalue())
            context.storage_state.assert_called_once_with()
            hidden_context.add_init_script.assert_called_once()
            self.assertEqual(hidden_context.add_init_script.call_args.args[0].count("fixture-value"), 1)
            self.assertEqual(background.new_context.call_args.kwargs["user_agent"], "fixture-agent")
            visible.close.assert_called_once()
            background.close.assert_called_once()
            chromium.launch.assert_any_call(channel="chrome", headless=False)
            chromium.launch.assert_any_call(channel="chrome", headless=True)
            context.request.get.assert_not_called()
            hidden_context.request.post.assert_not_called()

        def test_observation_errors_distinguish_http_transport_and_timeout(self):
            for status, failure, expected in ((403, None, HttpResponseFailure),
                                               (None, "net::ERR_CONNECTION_RESET", BrowserTransportFailure),
                                               (None, None, DraftObservationTimeout)):
                context, page = MagicMock(), Mock(url=DESKTOP_ORIGIN + "/")
                session = BrowserOrderSession(context, page)
                session.last_failure = Mock(return_value=failure)
                context.expect_event.return_value.__exit__.side_effect = TimeoutError("fixture-private")
                details = {} if status is None else {"http_status": status}
                with self.subTest(status=status, failure=failure), contextlib.redirect_stdout(io.StringIO()), \
                     self.assertRaises(expected) as caught:
                    observe_draft_reads(context, page, details, manual_tab=True, session=session)
                self.assertNotIn("fixture-private", str(caught.exception))
                page.goto.assert_called_once()

        def test_observed_snapshot_is_consumed_once_and_no_http_draft_fallback_exists(self):
            context, page = Mock(), Mock(url=DESKTOP_ORIGIN + "/")
            session = BrowserOrderSession(context, page)
            with self.assertRaises(Blocked):
                session.read(DRAFT_URL)
            session.seed_drafts([])
            self.assertEqual(session.read(DRAFT_URL), [])
            with self.assertRaises(Blocked):
                session.read(DRAFT_URL)
            with self.assertRaises(Blocked):
                session._request("GET", DRAFT_URL)
            page.evaluate.assert_not_called()
            context.request.get.assert_not_called()

        def test_browser_fetch_failure_keeps_sanitized_underlying_details(self):
            context, page, report = Mock(), Mock(url=DESKTOP_ORIGIN + "/"), []
            session = BrowserOrderSession(context, page, report)
            session.seed_drafts([])
            page.evaluate.return_value = {"kind": "browser-transport", "name": "TypeError", "message": "Failed to fetch"}
            failed = Mock(url=SYMBOLS_URL, method="POST", failure="net::ERR_CONNECTION_RESET")
            session.observe_failure(failed)
            def evaluate(*args):
                session.observe_failure(failed)
                return {"kind": "browser-transport", "name": "TypeError", "message": "Failed to fetch"}
            page.evaluate.side_effect = evaluate
            with self.assertRaisesRegex(BrowserTransportFailure, "TypeError: Failed to fetch; net::ERR_CONNECTION_RESET"):
                session.read(SYMBOLS_URL, SYMBOLS_REQUEST_BODY)
            self.assertIsNone(report[0]["http_status"])
            self.assertEqual(report[0]["failure_kind"], "browser_transport")
            context.request.get.assert_not_called()

        def test_order_list_polling_matches_exact_id_without_another_post(self):
            session, report = Mock(), []
            session.read.side_effect = [{"orders": [{"id": "fixture-order-suffix"}]},
                                        {"orders": []}, {"orders": [{"id": "fixture-order"}]}]
            with contextlib.redirect_stdout(io.StringIO()):
                result = reconcile_order(session, "fixture-order", report)
            self.assertTrue(result["found"])
            self.assertEqual(result["reads"], 3)
            self.assertTrue(all(call.args == (ORDERS_URL,) for call in session.read.call_args_list))
            session.submit.assert_not_called()

        def test_local_time_prompts_separate_fields_with_084458_defaults(self):
            now = datetime.fromisoformat("2026-11-07T08:40:00+02:00")
            with patch(__name__ + ".local_now", return_value=now), patch("builtins.input", side_effect=["", "", ""]) as prompt:
                target = prompt_order_time()
            self.assertEqual((target.hour, target.minute, target.second), (8, 44, 58))
            self.assertEqual(target.utcoffset(), now.utcoffset())
            self.assertEqual(prompt.call_count, 3)
            self.assertNotIn("Tehran", " ".join(c.args[0] for c in prompt.call_args_list))
            for values in (["24"], ["8", "60"], ["8", "44", "60"], ["8", "39", "59"]):
                with self.subTest(values=values), patch(__name__ + ".local_now", return_value=now), \
                     patch("builtins.input", side_effect=values), self.assertRaises(Blocked):
                    prompt_order_time()

        def test_submission_window_defaults_and_invalid_values(self):
            with patch("builtins.input", side_effect=["", ""]):
                self.assertEqual(prompt_submission_window(), SubmissionWindow(5_000_000_000, 350_000))
            with patch("builtins.input", side_effect=["2.5", "700"]):
                self.assertEqual(prompt_submission_window(), SubmissionWindow(2_500_000_000, 700_000))
            for values in (["0"], ["-1"], ["NaN"], ["5", "0"], ["5", "0.5"]):
                with self.subTest(values=values), patch("builtins.input", side_effect=values), self.assertRaises(Blocked):
                    prompt_submission_window()

        def test_confirmation_accepts_enter_and_escape_without_a_typed_phrase(self):
            for keys, approved in ((["x", "\r"], True), (["\n"], True), (["\x1b"], False)):
                with self.subTest(keys=keys), patch(__name__ + ".console_keys",
                        return_value=contextlib.nullcontext(Mock(side_effect=keys))), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(confirm_order(), approved)

        def test_countdown_has_six_fractional_digits_and_stops_at_target(self):
            at, *_ = self.buy_fixture()
            output, session = io.StringIO(), Mock()
            with patch(__name__ + ".datetime", wraps=datetime) as clock, \
                 patch("time.monotonic_ns", side_effect=[0, 0, 50_000_000, 200_000_000]), \
                 patch(__name__ + ".console_keys", return_value=contextlib.nullcontext(lambda wait=False: None)), \
                 contextlib.redirect_stdout(output):
                clock.now.return_value = at
                wait_local_target(at + timedelta(microseconds=200000), session)
            self.assertIn("00:00:00.200000", output.getvalue())
            self.assertIn("00:00:00.000000", output.getvalue())
            self.assertLessEqual(max(c.args[0] for c in session.page.wait_for_timeout.call_args_list), 20)
            with patch(__name__ + ".datetime", wraps=datetime) as clock, \
                 patch(__name__ + ".console_keys", return_value=contextlib.nullcontext(lambda wait=False: "\x1b")), \
                 contextlib.redirect_stdout(io.StringIO()), self.assertRaises(KeyboardInterrupt):
                clock.now.return_value = at
                wait_local_target(at + timedelta(seconds=1), session)

        def test_dispatch_requires_explicit_approval_and_ignores_unrelated_console_messages(self):
            at, *_ = self.buy_fixture()
            session = BrowserOrderSession(Mock(), Mock(url=DESKTOP_ORIGIN + "/"))
            session.seed_drafts([])
            with self.assertRaises(Blocked):
                dispatch_order_window(session, self.fixture_order(), at, SubmissionWindow(1000000, 350000), [])
            session.page.evaluate.assert_not_called()
            report, output = [], io.StringIO()
            def evaluate(script, options):
                callback = session.page.on.call_args.args[1]
                callback(Mock(type="log", text="unrelated fixture-private-message"))
                callback(Mock(type="log", text='POC_DISPATCH {"attempt":999,"elapsed_us":0}'))
                callback(Mock(type="log", text='POC_DISPATCH {"attempt":1,"elapsed_us":10}'))
                self.assertEqual(options["url"], ORDER_URL)
                self.assertIn('"commission":0.00036875', options["body"])
                self.assertNotIn("await fetch", script)
                self.assertNotIn("response.json", script)
                self.assertIn("controller.abort()", script)
                return {"attempts": 1, "responses_checked": 0}
            session.page.evaluate.side_effect = evaluate
            with contextlib.redirect_stdout(output):
                result = dispatch_order_window(session, self.fixture_order(), at, SubmissionWindow(1000000, 350000), report, approved=True)
            self.assertEqual(result, {"acceptance": "UNOBSERVED", "attempts": 1, "responses_checked": 0})
            self.assertEqual(run_report(report)["order_requests"], 1)
            self.assertNotIn("fixture-private-message", output.getvalue())
            session.page.evaluate.assert_called_once()

        def test_draft_bootstrap_is_allowed_only_after_verified_login_and_only_once(self):
            session = BrowserOrderSession(Mock(), Mock(url=DESKTOP_ORIGIN + "/"))
            with self.assertRaises(Blocked):
                session.load_drafts_after_login()
            session.page.evaluate.assert_not_called()
            session._authenticated_by_login = True
            session.page.evaluate.return_value = {"kind": "response", "status": 200,
                                                 "contentType": "application/json", "body": "[]"}
            session.load_drafts_after_login()
            with self.assertRaises(Blocked):
                session.load_drafts_after_login()
            self.assertEqual(session.read(DRAFT_URL), [])
            session.page.evaluate.assert_called_once()

        def test_order_list_missing_or_unavailable_does_not_change_ack_or_resubmit(self):
            for data in ({"orders": []}, {"unexpected": []}):
                session, report = Mock(), [{"stage": "order-submit", "acceptance": "ACCEPTED", "id": "fixture-order"}]
                session.read.return_value = data
                with contextlib.redirect_stdout(io.StringIO()):
                    result = reconcile_order(session, "fixture-order", report)
                self.assertFalse(result["found"])
                self.assertEqual(run_report(report)["acceptance"], "ACCEPTED")
                self.assertLessEqual(session.read.call_count, ORDER_RECONCILE_ATTEMPTS)
                session.submit.assert_not_called()

        def test_dispatch_transport_failure_is_unobserved_and_never_replayed(self):
            at, *_ = self.buy_fixture()
            session = BrowserOrderSession(Mock(), Mock(url=DESKTOP_ORIGIN + "/"))
            session.seed_drafts([])
            session.page.evaluate.side_effect = TimeoutError("Authorization: Bearer fixture-secret")
            with self.assertRaisesRegex(BrowserTransportFailure, "Do not replay") as caught:
                dispatch_order_window(session, self.fixture_order(), at, SubmissionWindow(5_000_000_000, 350_000), [], approved=True)
            self.assertNotIn("fixture-secret", str(caught.exception))
            session.page.evaluate.assert_called_once()
            session.page.remove_listener.assert_called_once()

        def test_redirect_does_not_replay_password(self):
            responses = [(302, {"Location": "/next"}, b""), (200, {"Content-Type": "text/html"}, b"form")]
            with patch(__name__ + ".request", side_effect=responses) as call:
                follow_auth(Mock(), LOGIN_ORIGIN + "/Login", [], "test", fields={"Password": "fixture"})
                self.assertIsNone(call.call_args_list[1].kwargs["fields"])
            response = NoRedirect().redirect_request(None, None, 307, "", {}, LOGIN_ORIGIN)
            self.assertIsNone(response)

        def test_default_and_enabled_live_have_zero_network(self):
            with patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("Network forbidden")) as network:
                with contextlib.redirect_stdout(io.StringIO()):
                    with patch(__name__ + ".SYMBOL", "xxxx"), patch(__name__ + ".LIVE_ORDER_ENABLED", False):
                        self.assertEqual(main([]), 2)  # Placeholder intent is invalid.
                    with patch(__name__ + ".LIVE_ORDER_ENABLED", True):
                        self.assertEqual(main(["--login"]), 2)
                        self.assertEqual(main(["--browser-login"]), 2)
                network.assert_not_called()

        def test_mocked_password_otp_token_and_account_flow(self):
            password_form = '<form id="primary_form" method="post" action="/Login"><input name="Username"><input name="Password" type="password"><input type="hidden" name="__RequestVerificationToken" value="fixture"></form>'
            otp_form = '<form method="post" action="/fixture-mfa"><input name="fixture-otp" autocomplete="one-time-code"><input type="hidden" name="__RequestVerificationToken" value="fixture"></form>'
            calls = []

            def fake_request(opener, url, report, stage, **kwargs):
                calls.append((url, kwargs))
                if stage == "discovery":
                    data = {"issuer": LOGIN_ORIGIN, "authorization_endpoint": LOGIN_ORIGIN + "/connect/authorize",
                            "token_endpoint": LOGIN_ORIGIN + "/connect/token", "code_challenge_methods_supported": ["S256"]}
                elif stage == "authorize":
                    return 200, {"Content-Type": "text/html"}, password_form.encode()
                elif stage == "password":
                    self.assertEqual(kwargs["fields"]["Password"], "fixture-password")
                    return 200, {"Content-Type": "text/html"}, otp_form.encode()
                elif stage == "otp":
                    self.assertEqual(kwargs["fields"]["fixture-otp"], "123456")
                    return 302, {"Location": CALLBACK + "?code=fixture-code&state=fixture-state"}, b""
                elif stage == "token":
                    self.assertEqual(kwargs["fields"]["code"], "fixture-code")
                    data = {"token_type": "Bearer", "access_token": "fixture-access-token"}
                elif stage == "account-read":
                    self.assertEqual(kwargs["bearer"], "fixture-access-token")
                    data = {"buyPowerT2": 0}
                else:
                    self.fail("Unexpected request stage")
                return 200, {"Content-Type": "application/json"}, json.dumps(data).encode()

            output = io.StringIO()
            with patch(__name__ + ".request", side_effect=fake_request), \
                 patch(__name__ + ".LIVE_ORDER_ENABLED", False), \
                 patch(__name__ + ".USERNAME", "xxxx"), patch(__name__ + ".PASSWORD", "xxxx"), \
                 patch("builtins.input", side_effect=["fixture-user", "123456"]), \
                 patch("getpass.getpass", return_value="fixture-password"), \
                 patch("secrets.token_urlsafe", side_effect=["fixture-verifier", "fixture-state"]), \
                 contextlib.redirect_stdout(output):
                authenticate_and_check([])
            self.assertEqual(len(calls), 6)
            for secret in ("fixture-user", "fixture-password", "123456", "fixture-access-token", "fixture-code"):
                self.assertNotIn(secret, output.getvalue())

        def test_browser_handoff_validates_callback_before_token_exchange(self):
            discovery = {
                "issuer": LOGIN_ORIGIN, "authorization_endpoint": LOGIN_ORIGIN + "/connect/authorize",
                "token_endpoint": LOGIN_ORIGIN + "/connect/token", "code_challenge_methods_supported": ["S256"],
            }
            desktop_args = ["--browser-login"]
            mobile_args = ["--browser-login", "--mobile"]
            for args, redirect_uri, callback_uri, callback_state, expected_exit in (
                (desktop_args, CALLBACK, CALLBACK, "fixture-state", 0),
                (mobile_args + ["--open-chrome"], MOBILE_CALLBACK, MOBILE_CALLBACK, "fixture-state", 0),
                (mobile_args, MOBILE_CALLBACK, CALLBACK, "fixture-state", 130),
                (desktop_args, CALLBACK, MOBILE_CALLBACK, "fixture-state", 130),
                (mobile_args, MOBILE_CALLBACK, MOBILE_CALLBACK, "wrong-state", 130),
                (desktop_args, CALLBACK, "https://example.com/auth-callback", "fixture-state", 130),
            ):
                with self.subTest(args=args, callback_uri=callback_uri, expected_exit=expected_exit):
                    callback = callback_uri + "?code=fixture-browser-code&state=" + callback_state
                    expected_stages = ["discovery", "token", "account-read"] if expected_exit == 0 else ["discovery"]
                    stages = []
                    callback_inputs = [callback, KeyboardInterrupt()]
                    if "--open-chrome" in args:
                        callback_inputs.insert(0, callback.replace("state=fixture-state", "state=wrong-state"))
                    pastes = iter(callback_inputs)

                    def read_callback(prompt):
                        self.assertEqual(stages, ["discovery"])
                        result = next(pastes)
                        if isinstance(result, KeyboardInterrupt):
                            raise result
                        return result

                    def fake_request(opener, url, report, stage, **kwargs):
                        stages.append(stage)
                        if stage == "discovery":
                            data = discovery
                        elif stage == "token":
                            self.assertEqual(kwargs["fields"]["code"], "fixture-browser-code")
                            self.assertEqual(kwargs["fields"]["code_verifier"], "fixture-verifier")
                            self.assertEqual(kwargs["fields"]["redirect_uri"], redirect_uri)
                            data = {"token_type": "Bearer", "access_token": "fixture-browser-token"}
                        elif stage == "account-read":
                            self.assertEqual(url, MONEY_URL)
                            expected_origin = redirect_uri.removesuffix("/auth-callback")
                            self.assertEqual(kwargs, {"bearer": "fixture-browser-token",
                                                      "account_origin": expected_origin})
                            data = {"buyPowerT2": 0}
                        else:
                            self.fail("The browser handoff must not submit login or OTP forms.")
                        return 200, {"Content-Type": "application/json"}, json.dumps(data).encode()

                    output = io.StringIO()
                    with patch(__name__ + ".request", side_effect=fake_request), \
                         patch(__name__ + ".LIVE_ORDER_ENABLED", False), \
                         patch("builtins.input", side_effect=AssertionError("Unmasked input forbidden")), \
                         patch("getpass.getpass", side_effect=read_callback), \
                         patch("secrets.token_urlsafe", side_effect=["fixture-verifier", "fixture-state"]), \
                         patch.dict(os.environ, {"ProgramFiles": "fixture-program-files"}), \
                         patch.object(Path, "is_file", return_value=True), \
                         patch("subprocess.Popen") as launch, \
                         contextlib.redirect_stdout(output):
                        self.assertEqual(main(args), expected_exit)
                    self.assertEqual(stages, expected_stages)
                    if "--open-chrome" in args:
                        self.assertIn("Callback rejected: The callback state does not match this run.", output.getvalue())
                        launch.assert_called_once()
                        command = launch.call_args.args[0]
                        self.assertEqual(Path(command[0]).name, "chrome.exe")
                        self.assertEqual(command[1:3], ["--incognito", "--new-window"])
                        authorize_url = command[3]
                        self.assertNotIn(authorize_url, output.getvalue())
                    else:
                        launch.assert_not_called()
                        authorize_url = next(line for line in output.getvalue().splitlines()
                                             if line.startswith(discovery["authorization_endpoint"] + "?"))
                    query = urllib.parse.parse_qs(urllib.parse.urlsplit(authorize_url).query)
                    self.assertEqual(query["redirect_uri"], [redirect_uri])
                    self.assertEqual(query["state"], ["fixture-state"])
                    for secret in ("fixture-browser-code", "fixture-browser-token", "fixture-verifier"):
                        self.assertNotIn(secret, output.getvalue())

    # Even an accidental unmocked network call must fail during self-tests.
    with patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("Network forbidden in self-test")), \
         patch("socket.socket.connect", side_effect=AssertionError("Network forbidden in self-test")), \
         patch("subprocess.Popen", side_effect=AssertionError("Unmocked browser/process launch forbidden in self-test")):
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
