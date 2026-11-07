"""Experimental native-HTTP POC; never imports or runs the frozen reference.

Default: offline configuration preview. PO-only read-only acceptance:
    python POC/easytrader_direct_http_poc.py --authenticate
    python POC/easytrader_direct_http_poc.py --authenticate --preflight
Only after reviewing read-only acceptance, --authenticate --live offers a
separate confirmation. No credentials, browser profiles, or reports are saved.
Private broker contracts and native-stack compatibility remain PO-unverified.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING, localcontext
import http.client
import http.cookiejar
import json
import math
import queue
import re
import secrets
import socket
import ssl
import threading
import time
from urllib.parse import urlsplit
from urllib.request import Request


DESKTOP = "https://d.easytrader.ir"
MOBILE = "https://m.easytrader.ir"
API = "https://api-mts.orbis.easytrader.ir"
MONEY = "/easy/api/money"
DRAFTS = "/easy/api/draft"
SYMBOLS = "/symbols/api/symbols/all"
MARKET = "/symbols/api/marketdata/v2"
ORDER = "/core/api/v2/order"
AUTH_HEADERS = {"authorization", "x-device-id", "x-app-name", "x-customheader", "x-api-key", "shard"}
MAX_ORDER_VALUE_IRR = 5_000_000
MAX_PREFLIGHT_NS = 15_000_000_000
MIN_LIVE_INTERVAL_NS = 300_000_000  # PO-reported broker minimum; 350 ms remains the default.
MAX_CONCURRENCY = 16
TEHRAN = timezone(timedelta(hours=3, minutes=30))
MARKET_TIME_WARNING = "Broker enforces market-entry timing; requests may be rejected before entry is allowed."


class Blocked(Exception):
    """Only constant, sanitized categories may cross this boundary."""

    def __init__(self, category, status=None):
        self.category = category
        self.status = status
        super().__init__(category)


def number(value, *, positive=False):
    if type(value) not in (str, int, Decimal):
        raise Blocked("invalid_number")
    text = str(value).strip()
    if len(text) > 50 or not re.fullmatch(r"[+]?[0-9]+(?:\.[0-9]+)?", text):
        raise Blocked("invalid_number")
    try:
        result = Decimal(text)
        if (not result.is_finite() or result < 0 or (positive and result == 0)
                or result > Decimal("1e18") or result.as_tuple().exponent < -18):
            raise Blocked("invalid_number")
        return result
    except InvalidOperation:
        raise Blocked("invalid_number") from None


def integer(value, *, positive=True):
    result = number(value, positive=positive)
    if result != result.to_integral_value():
        raise Blocked("invalid_integer")
    return int(result)


def decimal_json(value):
    """Encode exact decimal numeric literals, never binary floats or quoted money."""
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise Blocked("invalid_number")
        return format(value, "f")
    if isinstance(value, dict):
        return "{" + ",".join(json.dumps(k) + ":" + decimal_json(v) for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ",".join(decimal_json(v) for v in value) + "]"
    return json.dumps(value, ensure_ascii=True, allow_nan=False)


def parse_json(raw, content_type):
    if content_type.split(";", 1)[0].strip().lower() != "application/json":
        raise Blocked("non_json_response")
    try:
        def unique_object(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError
                result[key] = value
            return result

        def reject_constant(_):
            raise ValueError

        return json.loads(raw, parse_float=Decimal,
                          object_pairs_hook=unique_object,
                          parse_constant=reject_constant)
    except (ValueError, UnicodeError, RecursionError):
        raise Blocked("malformed_response") from None


@dataclass(repr=False)
class AuthMaterial:
    origin: str
    headers: dict = field(repr=False)
    cookies: http.cookiejar.CookieJar = field(repr=False)
    teardown_complete: bool = False

    def __repr__(self):
        return "AuthMaterial(<redacted>)"


def capture_material(headers, cookies, origin):
    selected = {k.lower(): v for k, v in headers.items() if k.lower() in AUTH_HEADERS}
    if any(not isinstance(v, str) or len(v) > 20000 or any(c in v for c in "\r\n")
           for v in selected.values()):
        raise Blocked("invalid_auth_material")
    if "authorization" in selected and not re.fullmatch(
            r"Bearer [A-Za-z0-9._~+/-]+=*", selected["authorization"], re.I):
        raise Blocked("invalid_auth_material")
    jar = http.cookiejar.CookieJar()
    for item in cookies:
        expiry = item.get("expires", -1)
        domain = item["domain"]
        jar.set_cookie(http.cookiejar.Cookie(
            0, item["name"], item["value"], None, False, domain,
            domain.startswith("."), domain.startswith("."), item["path"], True,
            item["secure"], int(expiry) if expiry > 0 else None, expiry <= 0,
            None, None, {}, False))
    if not selected.get("authorization") and not list(jar):
        raise Blocked("unavailable_session_state")
    return AuthMaterial(origin, selected, jar)


def authenticate_browser(*, origin=DESKTOP, api_origin=API, factory=None, headless=False):
    """Observe a legitimate login response; tear down ALL owned resources first.

    factory/origins are injected only by offline loopback tests. Production CLI
    always uses the official origins and visible manual login. No JS evaluation,
    storage export, token exchange, challenge automation, or fingerprint copying.
    """
    if factory is None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise Blocked("existing_playwright_unavailable") from None
        factory = sync_playwright
    manager = browser = context = material = None
    cleanup_ok = True
    try:
        manager = factory().start()
        browser = manager.chromium.launch(channel="chrome", headless=headless)
        context = browser.new_context(service_workers="block")
        page = context.new_page()

        def login_response(response):
            return (response.url == api_origin + MONEY and response.request.method == "GET"
                    and response.status == 200 and not response.from_service_worker
                    and response.headers.get("content-type", "").startswith("application/json"))

        with context.expect_event("response", predicate=login_response, timeout=300_000) as observed:
            page.goto(origin + "/", wait_until="commit", timeout=30_000)
        response = observed.value
        money = parse_json(response.body(), response.headers.get("content-type", ""))
        validate_money(money)
        current = urlsplit(page.url)
        if f"{current.scheme}://{current.netloc}" != origin:
            raise Blocked("unexpected_login_origin")
        material = capture_material(response.request.all_headers(), context.cookies(
            [api_origin + path for path in (MONEY, DRAFTS, SYMBOLS, MARKET, ORDER)]), origin)
    except Blocked:
        raise
    except Exception:
        raise Blocked("interactive_authentication_failed") from None
    finally:
        # Continue cleanup if one close fails; never return usable auth on failure.
        for resource in (context, browser):
            if resource is not None:
                try:
                    resource.close()
                except Exception:
                    cleanup_ok = False
        if browser is not None:
            try:
                cleanup_ok = not browser.is_connected() and cleanup_ok
            except Exception:
                cleanup_ok = False
        if manager is not None:
            try:
                manager.stop()
            except Exception:
                cleanup_ok = False
        if not cleanup_ok:
            raise Blocked("authentication_teardown_failed") from None
    material.teardown_complete = True
    return material


@dataclass(frozen=True)
class HttpResult:
    category: str
    status: int | None = None
    acceptance: str = "unknown"
    completed_ns: int | None = None


class NativeHttp:
    """Fixed-origin native HTTP pool; no redirects, proxies, automatic retries, or browser reference."""

    def __init__(self, material, *, api_origin=API, concurrency=None, timeout=3.0, loopback=False, live_enabled=False):
        parsed = urlsplit(api_origin)
        is_local = parsed.hostname in ("127.0.0.1", "localhost", "::1")
        if (not material.teardown_complete or (api_origin != API and not (loopback and is_local))
                or parsed.path or parsed.query or parsed.fragment or parsed.username
                or parsed.scheme not in (("https", "http") if loopback and is_local else ("https",))):
            raise Blocked("invalid_native_handoff")
        if not math.isfinite(timeout) or not 0 < timeout <= 30:
            raise Blocked("invalid_transport_limits")
        if concurrency is None:
            concurrency = min(MAX_CONCURRENCY, math.ceil(timeout * 1e9 / MIN_LIVE_INTERVAL_NS) + 1)
        if type(concurrency) is not int or not 1 <= concurrency <= MAX_CONCURRENCY:
            raise Blocked("invalid_transport_limits")
        if material.origin not in (DESKTOP, MOBILE) and not (loopback and is_local and material.origin == api_origin):
            raise Blocked("invalid_client_origin")
        self.origin = material.origin
        self.api_origin, self._parsed = api_origin, parsed
        self._auth, self._timeout = material, timeout
        self.capacity = concurrency
        self._tls_context = ssl.create_default_context() if parsed.scheme == "https" else None
        self._pool = queue.LifoQueue(concurrency)
        for _ in range(concurrency):
            self._pool.put(None)
        self._lock = threading.Lock()
        self._closed = False
        self.live_enabled = live_enabled
        self.verified = False
        self.read_outcome = "not_checked"

    def _connection(self):
        if self._parsed.scheme == "https":
            return http.client.HTTPSConnection(self._parsed.hostname, self._parsed.port,
                                               timeout=self._timeout, context=self._tls_context)
        return http.client.HTTPConnection(self._parsed.hostname, self._parsed.port, timeout=self._timeout)

    def dispatch_capacity(self, window):
        """Enough bounded slots to cover the timeout at the selected call interval."""
        return min(self.capacity, window.attempts, math.ceil(self._timeout * 1e9 / window.interval_ns) + 1)

    def _release(self, conn, reusable):
        with self._lock:
            reusable = reusable and not self._closed
            if conn is not None and not reusable:
                conn.close()
            self._pool.put_nowait(conn if reusable else None)

    def warm_connections(self, count, deadline_ns):
        """Prepare TCP/TLS only, with no HTTP request, before the timed window.

        DNS/TLS setup is bounded by the pre-start deadline at the caller. A late
        setup worker owns its connection until cleanup; failure prevents orders.
        """
        if not self.verified or not 1 <= count <= self.capacity:
            raise Blocked("native_verification_required")
        if time.perf_counter_ns() >= deadline_ns:
            raise Blocked("connection_warmup_timeout")
        errors = []
        workers = []

        # Reserve distinct pool entries while warming; a fast worker must not
        # repeatedly borrow one already-warm LIFO connection for all slots.
        borrowed = []
        try:
            for _ in range(count):
                borrowed.append(self._pool.get_nowait())
        except queue.Empty:
            for conn in borrowed:
                self._release(conn, True)
            raise Blocked("connection_capacity_timeout") from None

        def warm_slot(conn):
            reusable = False
            try:
                conn = conn or self._connection()
                if conn.sock is None:
                    conn.connect()
                reusable = True
            except ssl.SSLError:
                errors.append("tls_failure")
            except TimeoutError:
                errors.append("connection_warmup_timeout")
            except (OSError, http.client.HTTPException):
                errors.append("transport_failure")
            except Exception:
                errors.append("connection_warmup_failed")
            finally:
                self._release(conn, reusable)

        try:
            for conn in borrowed:
                worker = threading.Thread(target=warm_slot, args=(conn,), daemon=True, name="native-connect")
                worker.start()
                workers.append(worker)
        except RuntimeError:
            self.verified = False
            raise Blocked("connection_warmup_failed") from None
        finally:
            for conn in borrowed[len(workers):]:
                self._release(conn, True)
        for worker in workers:
            worker.join(max(0, (deadline_ns - time.perf_counter_ns()) / 1e9))
        if any(worker.is_alive() for worker in workers) or time.perf_counter_ns() >= deadline_ns:
            self.verified = False
            raise Blocked("connection_warmup_timeout")
        if errors:
            self.verified = False
            raise Blocked(errors[0])

    def _exchange(self, method, path, body=None, before_request=None):
        with self._lock:
            if self._closed:
                raise Blocked("transport_closed")
        try:
            conn = self._pool.get(timeout=self._timeout)
        except queue.Empty:
            raise Blocked("connection_capacity_timeout") from None
        reusable = False
        status = None
        try:
            conn = conn or self._connection()
            request = Request(self.api_origin + path)
            with self._lock:
                if self._closed:
                    raise Blocked("transport_closed")
                self._auth.cookies.add_cookie_header(request)
                headers = {**self._auth.headers, "Accept": "application/json", "Cache-Control": "no-cache",
                           "Origin": self.origin, "Referer": self.origin + "/"}
                if request.has_header("Cookie"):
                    headers["Cookie"] = request.get_header("Cookie")
            if body is not None:
                headers["Content-Type"] = "application/json"
            if conn.sock is not None:
                conn.sock.settimeout(self._timeout)
            deadline = time.perf_counter() + self._timeout
            if conn.sock is None:
                conn.connect()
            if before_request is not None and not before_request():
                raise Blocked("initiation_cancelled_or_cutoff")
            conn.request(method, path, body=body, headers=headers)
            response = conn.getresponse()
            status = response.status
            with self._lock:
                self._auth.cookies.extract_cookies(response, request)
            if not 200 <= status < 300:
                # Do not wait for an error body before respecting auth/rate limits.
                return status, response.getheader("Content-Type", ""), b""
            limit = 12_000_000 if path == SYMBOLS else 1_000_000
            raw = bytearray()
            while True:
                remaining = deadline - time.perf_counter()
                if remaining <= 0:
                    raise TimeoutError
                if conn.sock is not None:
                    conn.sock.settimeout(remaining)
                chunk = response.read1(min(65536, limit + 1 - len(raw)))
                raw.extend(chunk)
                if len(raw) > limit:
                    raise Blocked("response_too_large")
                if not chunk:
                    if response.length not in (None, 0):
                        raise http.client.IncompleteRead(bytes(raw))
                    break
            reusable = not response.will_close
            return response.status, response.getheader("Content-Type", ""), bytes(raw)
        except Blocked as exc:
            exc.status = status
            raise
        except ssl.SSLError:
            raise Blocked("tls_failure", status) from None
        except (TimeoutError, socket.timeout):
            raise Blocked("transport_timeout", status) from None
        except (OSError, http.client.HTTPException):
            raise Blocked("transport_failure", status) from None
        finally:
            self._release(conn, reusable)

    @staticmethod
    def _status(status):
        if status in (401, 403):
            raise Blocked("authentication_rejected", status)
        if status == 429:
            raise Blocked("broker_throttled", status)
        if not 200 <= status < 300:
            raise Blocked("http_error", status)

    def read(self, path, payload=None):
        allowed = {MONEY, DRAFTS}
        if not ((path in allowed and payload is None) or (path == SYMBOLS and payload == {"hash": "null"})
                or (path == MARKET and isinstance(payload, list) and len(payload) == 1
                    and isinstance(payload[0], str) and re.fullmatch(r"[A-Z0-9]{12}", payload[0]))):
            raise Blocked("operation_not_allowed")
        try:
            status, kind, raw = self._exchange("GET" if payload is None else "POST", path,
                                             None if payload is None else decimal_json(payload).encode())
            self._status(status)
            return parse_json(raw, kind)
        except Blocked:
            self.verified = False
            raise

    def verify(self):
        self.verified = False
        try:
            validate_money(self.read(MONEY))
            drafts = self.read(DRAFTS)
            validate_drafts(drafts)
        except Blocked as exc:
            self.read_outcome = exc.category
            raise
        self.verified, self.read_outcome = True, "verified_money_and_drafts"
        return drafts

    def submit(self, body, *, approved=False, on_initiated=None):
        if not self.live_enabled or not approved:
            return HttpResult("explicit_live_authorization_required")
        if not self.verified:
            return HttpResult("native_verification_required")
        status = None
        try:
            status, kind, raw = self._exchange("POST", ORDER, body, before_request=on_initiated)
            self._status(status)
            data = parse_json(raw, kind)
            if not isinstance(data, dict) or type(data.get("isSuccessful")) is not bool:
                raise Blocked("malformed_acknowledgement")
            if not data["isSuccessful"]:
                return HttpResult("broker_response", status, "rejected", time.perf_counter_ns())
            if not isinstance(data.get("id"), str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", data["id"]):
                raise Blocked("malformed_acknowledgement")
            return HttpResult("broker_response", status, "accepted", time.perf_counter_ns())
        except Blocked as exc:
            if exc.category in ("authentication_rejected", "broker_throttled"):
                self.verified = False
            return HttpResult(exc.category, status if status is not None else exc.status,
                              completed_ns=time.perf_counter_ns())

    def close(self):
        # In-use connections remain owned by workers and close on return.
        with self._lock:
            self._closed = True
            self.verified = False
            while True:
                try:
                    conn = self._pool.get_nowait()
                except queue.Empty:
                    break
                if conn is not None:
                    conn.close()


def validate_money(data):
    if not isinstance(data, dict):
        raise Blocked("malformed_money")
    return number(data.get("buyPowerT2"))


def validate_drafts(drafts):
    if not isinstance(drafts, list):
        raise Blocked("malformed_drafts")
    seen = set()
    for draft in drafts:
        if not isinstance(draft, dict):
            raise Blocked("malformed_drafts")
        identity = draft.get("id")
        if type(identity) not in (int, str) or not str(identity).strip() or str(identity) in seen:
            raise Blocked("invalid_draft_identity")
        seen.add(str(identity))
        if not isinstance(draft.get("symbolIsin"), str) or not re.fullmatch(r"[A-Z0-9]{12}", draft["symbolIsin"]):
            raise Blocked("invalid_instrument_identity")
        if type(draft.get("side")) is not int or draft["side"] not in (0, 1):
            raise Blocked("invalid_draft_side")
        name = draft.get("symbolName")
        if not isinstance(name, str) or not name.strip() or len(name) > 80 or not name.replace("\u200c", "").isprintable():
            raise Blocked("invalid_instrument_name")
        integer(draft.get("quantity"))
        number(draft.get("price"), positive=True)


def exact_symbol(items, isin):
    if not isinstance(items, list):
        raise Blocked("malformed_instrument_metadata")
    matches = [x for x in items if isinstance(x, dict) and x.get("symbolIsin") == isin]
    if len(matches) != 1:
        raise Blocked("instrument_identity_mismatch")
    return matches[0]


@dataclass(frozen=True, repr=False)
class BuyOrder:
    isin: str
    name: str
    quantity: int
    price: Decimal
    commission: Decimal
    hidden: Decimal
    size: Decimal
    total: int
    order_from: int

    def payload(self, at):
        local = at.astimezone(TEHRAN)
        stamp = (f"{local.month}/{local.day}/{local.year}, {local.hour % 12 or 12}:"
                 f"{local.minute:02}:{local.second:02} {'AM' if local.hour < 12 else 'PM'}")
        return {"order": {"price": self.price, "quantity": self.quantity, "side": 0, "validityType": 0,
                          "createDateTime": stamp, "commission": self.commission, "symbolIsin": self.isin,
                          "symbolName": self.name, "orderModelType": 1, "totalValue": self.total,
                          "orderFrom": self.order_from}}


def build_buy(draft, symbol, market, funds, quantity, price, origin):
    """Independent implementation of the evidenced financial/payload invariants."""
    validate_drafts([draft])
    if draft["side"] != 0 or type(draft.get("validityType", 0)) is not int or draft.get("validityType", 0) != 0:
        raise Blocked("only_day_buy_verified")
    isin = draft["symbolIsin"]
    if not isinstance(symbol, dict) or not isinstance(market, dict) or any(x.get("symbolIsin") != isin for x in (symbol, market)):
        raise Blocked("instrument_identity_mismatch")
    if symbol.get("isActive") is not True or symbol.get("canBuy") is not True:
        raise Blocked("instrument_not_buyable")
    if str(market.get("stateCode", "")).strip() not in ("A", "65"):
        raise Blocked("instrument_not_tradable")
    unit = integer(symbol.get("marketUnit"))
    if unit not in {1, 2, 3, 4, 5, 6, 7, 8, 18, 19, 20, 31, 32, 39, 40, 41, 42, 43, 52, 54}:
        raise Blocked("unsupported_market_unit")
    name = symbol.get("symbolName")
    if not isinstance(name, str) or not name.strip() or len(name) > 80 or not name.replace("\u200c", "").isprintable():
        raise Blocked("invalid_instrument_name")
    qty, amount = integer(quantity), number(price, positive=True)
    low, high = number(market.get("lowAllowedPrice")), number(market.get("highAllowedPrice"), positive=True)
    tick, step = number(symbol.get("minDealablePrice"), positive=True), integer(symbol.get("minDealableCount"))
    minimum, maximum = integer(symbol.get("minValidBuyVolume")), integer(symbol.get("maxValidBuyVolume"))
    if "minValidBuyVolume" in market:
        minimum = max(minimum, integer(market["minValidBuyVolume"]))
    if "maxValidBuyVolume" in market:
        maximum = min(maximum, integer(market["maxValidBuyVolume"]))
    rate, hidden = number(symbol.get("buyCommission")), number(symbol.get("hidePrice"))
    size = number(1 if symbol.get("csize") is None else symbol["csize"], positive=True)
    if rate >= 1:
        raise Blocked("invalid_commission")
    notional = 1_000_000 if unit in {3, 4, 5, 6, 7, 8, 31, 32, 39, 43, 52, 54} else 50_000_000 if unit in {18, 19, 20, 40, 41, 42} else 5_000_000
    with localcontext() as ctx:
        ctx.prec = 128
        if not low <= amount <= high or amount % tick:
            raise Blocked("price_constraint")
        if not minimum <= qty <= maximum or qty % step:
            raise Blocked("quantity_constraint")
        if qty * (amount + hidden) < notional:
            raise Blocked("minimum_buy_value")
        total = int((qty * (amount * (1 + rate) + hidden) * size).to_integral_value(rounding=ROUND_CEILING))
    if not 0 < total <= MAX_ORDER_VALUE_IRR:
        raise Blocked("per_order_safety_cap")
    if total > number(funds):
        raise Blocked("insufficient_buying_power")
    if origin not in (DESKTOP, MOBILE):
        raise Blocked("invalid_client_origin")
    return BuyOrder(isin, name, qty, amount, rate, hidden, size, total, 34 if origin == DESKTOP else 33)


@dataclass(frozen=True)
class Preflight:
    order: BuyOrder
    checked_ns: int


def preflight(client, draft, quantity, price):
    checked = time.perf_counter_ns()
    all_symbols = client.read(SYMBOLS, {"hash": "null"})
    if not isinstance(all_symbols, dict):
        raise Blocked("malformed_instrument_metadata")
    symbol = exact_symbol(all_symbols.get("symbols"), draft["symbolIsin"])
    market = exact_symbol(client.read(MARKET, [draft["symbolIsin"]]), draft["symbolIsin"])
    funds = validate_money(client.read(MONEY))
    order = build_buy(draft, symbol, market, funds, quantity, price, client.origin)
    return Preflight(order, checked)


@dataclass(frozen=True)
class Window:
    duration_ns: int
    interval_ns: int

    def __post_init__(self):
        if (type(self.duration_ns) is not int or type(self.interval_ns) is not int
                or self.duration_ns <= 0 or self.interval_ns <= 0):
            raise Blocked("invalid_dispatch_window")

    @classmethod
    def from_inputs(cls, duration_seconds="5", interval_milliseconds="350"):
        with localcontext() as ctx:
            ctx.prec = 128
            duration = number(duration_seconds, positive=True) * 1_000_000_000
        if duration != duration.to_integral_value():
            raise Blocked("duration_precision")
        interval = integer(interval_milliseconds) * 1_000_000
        return cls(int(duration), interval)

    @property
    def attempts(self):
        return (self.duration_ns + self.interval_ns - 1) // self.interval_ns


def monotonic_target(target, *, now=None, clock=time.perf_counter_ns):
    now = now or datetime.now().astimezone()
    if target.tzinfo is None or target.date() != now.date():
        raise Blocked("invalid_local_target")
    delta = target - now
    nanos = (delta.days * 86400 + delta.seconds) * 1_000_000_000 + delta.microseconds * 1000
    if nanos <= 0:
        raise Blocked("local_target_passed")
    return clock() + nanos


def wait_until(deadline_ns, cancel, *, clock=time.perf_counter_ns, pause=time.sleep):
    while not cancel.is_set():
        left = deadline_ns - clock()
        if left <= 0:
            return True
        if left > 20_000_000:
            cancel.wait(min((left - 20_000_000) / 1_000_000_000, .05))
        else:
            # CPython uses a high-resolution waitable timer for sleep on modern
            # Windows. Avoid the coarser Event.wait timeout at the final deadline.
            # This sleeps, never spins; cancellation latency here is at most the
            # requested 20 ms sleep plus unbounded OS scheduling delay.
            pause(left / 1_000_000_000)
    return False


@dataclass
class Attempt:
    number: int
    initiated_ns: int
    result: HttpResult | None = None


@dataclass
class DispatchReport:
    planned: int
    attempts: list[Attempt] = field(default_factory=list)
    stop: str = "cutoff"
    capacity_skips: int = 0
    scheduled_attempts: int = 0
    non_initiated: list[str] = field(default_factory=list)
    worker_capacity: int = 0

    def diagnostics(self):
        # Called only after scheduling and bounded draining. No payloads or IDs.
        snapshot = [(a.number, a.initiated_ns, a.result) for a in tuple(self.attempts)]
        return {"theoretical_attempts": self.planned, "local_initiations": len(snapshot),
                "stop": self.stop, "capacity_skips": self.capacity_skips,
                "scheduled_attempts": self.scheduled_attempts,
                "worker_capacity": self.worker_capacity,
                "non_initiated_outcomes": list(self.non_initiated),
                "http_responses_observed": sum(r is not None and r.status is not None for _, _, r in snapshot),
                "broker_results_observed": sum(r is not None and r.acceptance != "unknown" for _, _, r in snapshot),
                "broker_results_unknown": sum(r is None or r.acceptance == "unknown" for _, _, r in snapshot),
                "attempts": [{"number": n, "monotonic_ns": stamp,
                              "transport": r.category if r else "outstanding_unknown",
                              "http_status": r.status if r else None,
                              "completion_monotonic_ns": r.completed_ns if r else None,
                              "broker_acceptance": r.acceptance if r else "unknown",
                              "execution": "unknown"} for n, stamp, r in snapshot]}


def dispatch(submit, body, window, start_ns, *, approved=False, cancel=None,
             concurrency=4, drain_seconds=4.0, clock=time.perf_counter_ns, pause=time.sleep):
    """No response-driven scheduling, queue, catch-up, retry, or console work.

    submit(body, before_request) must call before_request immediately before
    handing the request to native HTTP, and refrain from sending if it is False.
    Workers signal that handoff before doing HTTP I/O. At most `concurrency`
    reusable workers start before waiting for the target. Each idle worker has
    one inbox, so there is no backlog behind busy workers. Native calls are
    rechecked against the exclusive cutoff, and paced from the actual previous
    call timestamp rather than the scheduler's later notification time.
    Daemon workers retain ownership of unresolved requests after bounded drain.
    """
    if not approved:
        raise Blocked("explicit_confirmation_required")
    if not 1 <= concurrency <= MAX_CONCURRENCY or not math.isfinite(drain_seconds) or drain_seconds < 0:
        raise Blocked("invalid_dispatch_limits")
    cancel = cancel or threading.Event()
    concurrency = min(concurrency, window.attempts)
    report = DispatchReport(window.attempts, worker_capacity=concurrency)
    cutoff, due = start_ns + window.duration_ns, start_ns
    idle = queue.Queue(concurrency)
    shutdown = threading.Event()
    lock = threading.Lock()
    workers = []
    last = None

    def initiate(ready):
        nonlocal last
        attempt = None

        def before_request():
            nonlocal last, attempt
            with lock:
                stamp = clock()
                if cancel.is_set() or stamp >= cutoff or (last is not None and stamp - last < window.interval_ns):
                    return False
                attempt = Attempt(len(report.attempts) + 1, stamp)
                report.attempts.append(attempt)
                last = stamp
                ready.set()
                return True

        try:
            try:
                result = submit(body, before_request)
            except Exception:
                result = HttpResult("transport_failure")
            with lock:
                if attempt is not None:
                    attempt.result = result
                else:
                    report.non_initiated.append(result.category)
                if result.category in ("authentication_rejected", "broker_throttled", "native_verification_required",
                                       "explicit_live_authorization_required"):
                    cancel.set()
        finally:
            ready.set()

    def worker_loop(inbox, initialized):
        idle.put_nowait(inbox)
        initialized.set()
        while True:
            try:
                ready = inbox.get(timeout=.05)
            except queue.Empty:
                if shutdown.is_set():
                    return
                continue
            initiate(ready)
            if shutdown.is_set():
                return
            idle.put_nowait(inbox)

    try:
        for index in range(concurrency):
            inbox, initialized = queue.Queue(1), threading.Event()
            worker = threading.Thread(target=worker_loop, args=(inbox, initialized), daemon=True,
                                      name=f"native-order-{index + 1}")
            try:
                worker.start()
            except RuntimeError:
                report.stop = "worker_start_failure"
                cancel.set()
                break
            workers.append(worker)
            if not initialized.wait(1):
                report.stop = "worker_start_failure"
                cancel.set()
                break
        while not cancel.is_set() and clock() < cutoff:
            if not wait_until(due, cancel, clock=clock, pause=pause) or clock() >= cutoff:
                break
            report.scheduled_attempts += 1
            try:
                inbox = idle.get_nowait()
            except queue.Empty:
                report.capacity_skips += 1
                due = clock() + window.interval_ns
                continue
            ready = threading.Event()
            initiated_before = len(report.attempts)
            inbox.put_nowait(ready)
            while not ready.wait(.01):
                if cancel.is_set() or clock() >= cutoff:
                    break
            with lock:
                due = (last + window.interval_ns if len(report.attempts) > initiated_before
                       else clock() + window.interval_ns)
        if cancel.is_set() and report.stop == "cutoff":
            report.stop = "cancelled_or_broker_stop"
    except KeyboardInterrupt:
        cancel.set()
        report.stop = "cancelled"
    finally:
        shutdown.set()
        end = time.perf_counter() + drain_seconds
        for worker in workers:
            try:
                worker.join(max(0, end - time.perf_counter()))
            except KeyboardInterrupt:
                cancel.set()
                report.stop = "cancelled_during_cleanup"
                break
    return report


def live_dispatch(client, approved_order, fresh, window, start_ns, *, confirmed=False, cancel=None):
    if window.interval_ns < MIN_LIVE_INTERVAL_NS:
        raise Blocked("live_interval_below_300_ms")
    if not confirmed or not client.live_enabled or not client.verified or fresh.order != approved_order:
        raise Blocked("live_authorization_or_preflight_failed")
    now = time.perf_counter_ns()
    if start_ns < now or start_ns + window.duration_ns - fresh.checked_ns > MAX_PREFLIGHT_NS:
        raise Blocked("stale_preflight_or_late_start")
    if approved_order.order_from != (34 if client.origin == DESKTOP else 33):
        raise Blocked("client_identity_changed")
    body = decimal_json(approved_order.payload(datetime.now().astimezone())).encode()
    return dispatch(lambda data, begin: client.submit(data, approved=True, on_initiated=begin), body, window, start_ns,
                    approved=True, cancel=cancel, concurrency=client.dispatch_capacity(window))


def confirm_order():
    print("Each request creates an independent order; multiple orders may be accepted or executed.")
    print("Press Enter to approve this window, or Escape to cancel.")
    try:
        import msvcrt
    except ImportError:
        return input("Type CONFIRM to approve: ") == "CONFIRM"
    while True:
        key = msvcrt.getwch()
        if key in ("\r", "\n", "\x1b"):
            return key != "\x1b"


def local_target():
    now = datetime.now().astimezone()
    values = [integer(input(f"Local {name} [{default}]: ").strip() or str(default), positive=False)
              for name, default in (("hour", 8), ("minute", 44), ("second", 58))]
    try:
        target = now.replace(hour=values[0], minute=values[1], second=values[2], microsecond=0)
    except ValueError:
        raise Blocked("invalid_local_target") from None
    monotonic_target(target)
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authenticate", action="store_true", help="PO-only interactive login and native read-only verification")
    parser.add_argument("--mobile", action="store_true")
    parser.add_argument("--preflight", action="store_true", help="PO-only full read-only draft/financial preview; requires --authenticate")
    parser.add_argument("--live", action="store_true", help="PO-only, requires authentication, fresh preflight and per-window confirmation")
    args = parser.parse_args(argv)
    diagnostics = {"run_id": secrets.token_hex(8), "authentication_handoff": "not_requested",
                   "native_read_only": "not_checked", "live_requested": args.live}
    client = None
    try:
        if (args.live or args.preflight) and not args.authenticate:
            raise Blocked("live_requires_interactive_authentication")
        if not args.authenticate:
            diagnostics.update(mode="offline", order_requests=0, interval_ms=350,
                               theoretical_attempts=Window.from_inputs().attempts)
            return 0
        print("Sign in manually in Chrome, including MFA/CAPTCHA. Browser closes before native HTTP verification.")
        diagnostics["authentication_handoff"] = "started"
        auth = authenticate_browser(origin=MOBILE if args.mobile else DESKTOP)
        diagnostics["authentication_handoff"] = "browser_context_and_playwright_closed"
        client = NativeHttp(auth, live_enabled=args.live)
        drafts = client.verify()
        diagnostics["native_read_only"] = client.read_outcome
        if not args.live and not args.preflight:
            return 0
        if not drafts:
            raise Blocked("no_drafts")
        # Interactive review only; structured diagnostics never include these fields.
        for i, draft in enumerate(drafts, 1):
            print(f"{i}: {draft['symbolName']} | BUY={draft['side'] == 0} | quantity={draft['quantity']} | price={draft['price']}")
        index = integer(input("Select exactly one BUY draft row: ")) - 1
        if index >= len(drafts):
            raise Blocked("invalid_draft_selection")
        draft = dict(drafts[index])
        quantity = input(f"Quantity [{draft['quantity']}]: ").strip() or draft["quantity"]
        price = input(f"Unit price IRR [{draft['price']}]: ").strip() or draft["price"]
        target = local_target()
        window = Window.from_inputs(input("Duration seconds [5]: ").strip() or "5",
                                    input("Minimum interval milliseconds [350]: ").strip() or "350")
        if args.live and window.interval_ns < MIN_LIVE_INTERVAL_NS:
            raise Blocked("live_interval_below_300_ms")
        initial = preflight(client, draft, quantity, price)
        print("WARNING: " + MARKET_TIME_WARNING)
        order = initial.order
        print(f"BUY {order.name} | quantity={order.quantity} | price={order.price} IRR | commission={order.commission}")
        print(f"Per-order total={order.total} IRR; planned independent requests={window.attempts}; "
              f"potential aggregate exposure={order.total * window.attempts} IRR.")
        print(f"Local start={target.isoformat()}; duration={window.duration_ns / 1e9:g}s; interval={window.interval_ns / 1e6:g} ms.")
        diagnostics.update(scheduled_start=target.isoformat(), duration_seconds=window.duration_ns / 1e9,
                           interval_ms=window.interval_ns / 1e6, theoretical_attempts=window.attempts)
        if not args.live:
            diagnostics["order_requests"] = 0
            return 0
        if not confirm_order():
            diagnostics["stop"] = "confirmation_cancelled"
            return 0
        cancel = threading.Event()
        start_ns = monotonic_target(target)
        if not wait_until(start_ns - 5_000_000_000, cancel):
            raise Blocked("cancelled")
        client.warm_connections(client.dispatch_capacity(window), start_ns)
        fresh = preflight(client, draft, quantity, price)
        report = live_dispatch(client, order, fresh, window, start_ns, confirmed=True, cancel=cancel)
        diagnostics.update(report.diagnostics())
        return 0
    except Blocked as exc:
        diagnostics["stop"] = exc.category
        if diagnostics["authentication_handoff"] == "started":
            diagnostics["authentication_handoff"] = "failed"
        if client is not None:
            diagnostics["native_read_only"] = client.read_outcome
        return 2
    except KeyboardInterrupt:
        diagnostics["stop"] = "cancelled"
        return 130
    except Exception:
        diagnostics["stop"] = "unexpected_failure_no_retry"
        return 2
    finally:
        if client is not None:
            client.close()
        print(json.dumps(diagnostics, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
