"""Disposable EasyTrader POC. Python 3.10+; no required packages for offline use.

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
With --browser-single-order [HH:MM:SS], select one draft as a BUY template,
confirm a local timing rehearsal, and use today's Tehran target (08:45:00 by
default). Live arming is blocked. Rehearsal timing uses only local clocks.

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

No direct order endpoint is callable. Missing: observed MFA form, OMS session setup,
instrument identity/rules, market/calendar/status semantics, order payload and
acceptance/status response semantics. A local order preview is NOT a broker
payload. The timing preview does NOT establish a permitted market session.

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
LIVE_ORDER_ENABLED = False
MAX_ORDER_VALUE_IRR = 5_000_000  # Notional only; no fee schedule is verified.
NETWORK_TIMEOUT_SECONDS = 15

import base64
from datetime import datetime
from decimal import Decimal
import getpass
import hashlib
from html.parser import HTMLParser
import http.cookiejar
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
SCOPE = "easy2_api mts_api openid profile login_delegation-api"
MAX_RESPONSE_BYTES = 1_000_000
BROWSER_READ_TIMEOUT_MS = 300_000


class Blocked(Exception):
    """A safe, non-secret diagnostic suitable for printing."""


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
        raise Blocked("Live submission is unavailable: instrument, session and order contracts remain unverified.")


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


def observe_draft_reads(context, page, last_read, *, scheduled_at=None, manual_tab=False):
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
        return method == "GET" and response.status == 200 and media_type == "application/json"

    timeout_ms = BROWSER_READ_TIMEOUT_MS
    if scheduled_at is None or manual_tab:
        print("After sign-in, open the Drafts tab in the desktop orders panel if needed.")
    if scheduled_at is not None:
        remaining_ms = int((scheduled_at - datetime.now(tehran_zone())).total_seconds() * 1000)
        if remaining_ms <= 0:
            raise Blocked("Target time passed before the browser could observe drafts.")
        timeout_ms = min(timeout_ms, remaining_ms)
    with context.expect_event("response", predicate=match_drafts, timeout=timeout_ms) as observed:
        page.goto(DESKTOP_ORIGIN + "/", wait_until="commit", timeout=min(30_000, timeout_ms))
        if scheduled_at is not None and not manual_tab:
            page.locator('[data-cy="order-grid-tab-draft-order"]').click(timeout=timeout_ms)
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


def observe_browser(report, *, draft_discovery=False, scheduled_at=None, single_order=False):
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
    single_order = len(args) in (1, 2) and args[0] == "--browser-single-order"
    draft_send = args[:1] == ["--browser-draft-send"]
    browser_observation = args in (["--browser-read"], ["--browser-drafts"]) or draft_preview or draft_schedule
    if (args and args != ["--login"] and browser_redirect is None and token_origin is None
            and not browser_observation and not single_order and not draft_send):
        print("Usage: python POC/easytrader_poc.py "
              "[--self-test | --login | --browser-login [--mobile] [--open-chrome] "
              "[--compare-browser-token] | --browser-token [--mobile] | --browser-read | --browser-drafts "
              "| --browser-draft-preview | --browser-draft-schedule HH:MM:SS | --browser-single-order [HH:MM:SS]]")
        return 2
    report = []
    try:
        require_read_only_mode()
        if draft_send:
            raise Blocked("Direct group send is disabled until the EasyTrader API contract is verified.")
        print("Read-only POC mode.")
        if single_order:
            target = args[1] if len(args) == 2 else TARGET_TIME
            scheduled_at = tehran_target(datetime.now(tehran_zone()), target)
            print(f"Single-order rehearsal target: {scheduled_at.isoformat()}.")
            payload, buying_power = observe_browser(report, scheduled_at=scheduled_at, single_order=True)
            rehearse_single_order(payload, buying_power, scheduled_at, report)
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
        print("Cancelled. No order request was sent.")
        return 130
    except (ValueError, UnicodeError):
        print("STOP: malformed authentication response; sensitive details suppressed.")
        return 2
    finally:
        print(json.dumps({"requests": report, "order_requests": 0,
                          "order_id": None, "broker_order_response": None,
                          "acceptance": "NOT_ATTEMPTED", "execution": "NOT_ATTEMPTED"}, ensure_ascii=True))


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

        def test_single_order_rehearses_only_one_corrected_buy_at_the_default_target(self):
            first = {"id": "fixture-id-one", "symbolName": "FIXTURE ONE", "quantity": 10, "price": 100, "side": 0}
            second = {**first, "id": "fixture-id-two", "symbolName": "FIXTURE TWO", "side": 1}
            ready = datetime.fromisoformat("2026-11-04T08:44:59+03:30")
            target = datetime.fromisoformat("2026-11-04T08:45:00+03:30")
            target_ns = int(target.timestamp()) * 1_000_000_000
            output = io.StringIO()
            with patch(__name__ + ".datetime", wraps=datetime) as clock, \
                 patch(__name__ + ".observe_browser", return_value=([first, second], 731953)) as observe, \
                 patch("builtins.input", side_effect=["۲", "۳", "REHEARSE"]) as prompt, \
                 patch("time.time_ns", side_effect=[target_ns - 10_000_000, target_ns + 500_000]), \
                 patch("time.perf_counter_ns", side_effect=[100_000_000, 100_000_000, 105_000_000, 110_500_000]), \
                 patch("time.sleep") as sleep, contextlib.redirect_stdout(output):
                clock.now.return_value = ready
                self.assertEqual(main(["--browser-single-order"]), 0)
            observe.assert_called_once()
            self.assertEqual(observe.call_args.kwargs, {"scheduled_at": target, "single_order": True})
            self.assertEqual(prompt.call_count, 3)
            self.assertEqual([call.args[0] for call in sleep.call_args_list], [0.01, 0.005])
            preview_lines = [line for line in output.getvalue().splitlines() if line.startswith("Dry-run BUY preview:")]
            self.assertEqual(preview_lines, ["Dry-run BUY preview: FIXTURE TWO | Quantity: 3 | Draft price: 100."])
            report = json.loads(output.getvalue().splitlines()[-1])
            self.assertEqual(report["order_requests"], 0)
            self.assertIsNone(report["order_id"])
            self.assertIsNone(report["broker_order_response"])
            self.assertEqual((report["acceptance"], report["execution"]), ("NOT_ATTEMPTED", "NOT_ATTEMPTED"))
            self.assertEqual(len(report["requests"]), 1)
            rehearsal = report["requests"][0]
            self.assertEqual(rehearsal["selected_count"], 1)
            self.assertFalse(rehearsal["live_armed"])
            self.assertEqual(rehearsal["funds_check"], "UNVERIFIED")
            self.assertEqual(rehearsal["broker_clock"],
                             {"status": "UNVERIFIED", "offset_ns": None, "uncertainty_ns": None})
            self.assertEqual(rehearsal["local_start_unix_ns"], target_ns - 10_000_000)
            self.assertEqual(rehearsal["local_preview_unix_ns"], target_ns + 500_000)
            self.assertEqual(rehearsal["local_target_delta_ns"], 500_000)
            self.assertEqual(rehearsal["elapsed_monotonic_ns"], 10_500_000)
            self.assertNotIn("731953", output.getvalue())
            self.assertNotIn("fixture-id", output.getvalue())
            self.assertNotIn("FIXTURE TWO", output.getvalue().splitlines()[-1])

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

        def test_single_order_cancellation_expiry_and_live_toggle_do_not_wait(self):
            draft = {"id": "fixture-id", "symbolName": "TEST", "quantity": 1, "price": 100, "side": 0}
            ready = datetime.fromisoformat("2026-11-04T12:19:59+03:30")
            target = tehran_target(ready, "12:20:00")
            late = datetime.fromisoformat("2026-11-04T12:20:01+03:30")
            args = ["--browser-single-order", "12:20:00"]
            for timestamps, answers, enable_live, exit_code, observe_count in (
                ([ready, ready, ready], ["1", "", "ARM"], False, 0, 1),
                ([ready, ready, ready], ["1", "", "REHEARSE"], False, 2, 1),
                ([ready, ready, late], ["1", ""], False, 2, 1),
                ([ready, late], [], False, 2, 1),
                ([late], [], False, 2, 0),
                ([], [], True, 2, 0),
            ):
                with self.subTest(timestamps=timestamps, answers=answers, enable_live=enable_live):
                    output = io.StringIO()
                    with patch(__name__ + ".datetime", wraps=datetime) as clock, \
                         patch(__name__ + ".LIVE_ORDER_ENABLED", enable_live), \
                         patch(__name__ + ".observe_browser", return_value=([draft], None)) as observe, \
                         patch("builtins.input", side_effect=answers) as prompt, \
                         patch("time.time_ns", return_value=int(target.timestamp()) * 1_000_000_000), \
                         patch("time.sleep") as sleep, contextlib.redirect_stdout(output):
                        clock.now.side_effect = timestamps
                        self.assertEqual(main(args), exit_code)
                    self.assertEqual(observe.call_count, observe_count)
                    self.assertEqual(prompt.call_count, len(answers))
                    sleep.assert_not_called()
                    self.assertNotIn("Dry-run BUY preview:", output.getvalue())
                    self.assertEqual(json.loads(output.getvalue().splitlines()[-1])["order_requests"], 0)

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
            playwright = api.sync_playwright.return_value.__enter__.return_value
            browser = playwright.chromium.launch.return_value
            context = browser.new_context.return_value
            context.expect_event.return_value.__exit__.side_effect = TimeoutError("fixture-private")
            ready = datetime.fromisoformat("2026-11-04T08:44:00+03:30")
            output = io.StringIO()
            with patch.dict(sys.modules, {"playwright.sync_api": api}), \
                 patch(__name__ + ".datetime", wraps=datetime) as clock, \
                 patch("builtins.input") as prompt, patch("time.sleep") as sleep, \
                 contextlib.redirect_stdout(output):
                clock.now.return_value = ready
                self.assertEqual(main(["--browser-single-order"]), 2)
            playwright.chromium.launch.assert_called_once()
            context.expect_event.assert_called_once()
            context.new_page.return_value.goto.assert_called_once()
            browser.close.assert_called_once()
            prompt.assert_not_called()
            sleep.assert_not_called()
            self.assertIn("Timed out waiting for a draft GET", output.getvalue())
            self.assertNotIn("fixture-private", output.getvalue())
            self.assertEqual(json.loads(output.getvalue().splitlines()[-1])["order_requests"], 0)

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
    with patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("Network forbidden in self-test")):
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
