"""Standalone native-HTTP opening-order POC. Run from the repository root.

REAL END-TO-END RUN (PO only; creates real independent BUY order requests):
    python POC/easytrader_direct_http_poc.py --authenticate --live

For the mobile EasyTrader login context, also add --mobile:
    python POC/easytrader_direct_http_poc.py --authenticate --mobile --live

Complete official login/MFA/CAPTCHA manually. The browser closes. Select one
saved BUY draft, enter quantity/price, today's FUTURE local start time, duration
in seconds and interval in milliseconds (default 350; live minimum 300). Review
the per-order value, request count and potential aggregate exposure. ENTER
approves actual sending; ESC cancels. After approval, countdown/status appears
while connections and final preflight are prepared. During sending, requests
run at the chosen minimum call interval without waiting for earlier send calls
or responses. ESC or Ctrl+C stops future requests, never recalls transmitted
ones. A readable final summary distinguishes accepted, rejected and unknown
acknowledgements; it does not claim execution/fills. No test server or simulated
response is used by this command. Timing and queue priority are not guaranteed.

Every --live invocation writes a sanitized per-run JSONL trace in POC/logs/.
Normal live execution prints no technical JSON.
OPTIONAL sanitized technical diagnostics, printed once after the run:
    python POC/easytrader_direct_http_poc.py --authenticate --live --diagnostics

Read-only checks, with NO order POSTs:
    python POC/easytrader_direct_http_poc.py --authenticate
    python POC/easytrader_direct_http_poc.py --authenticate --preflight
No arguments: offline only, with no network. Authentication material stays in
memory; no credentials, persistent browser profile, or reports are exported.
Never imports or runs the frozen reference. Only the PO tests real accounts.
"""

from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING, localcontext
import http.client
import http.cookiejar
import json
import math
from pathlib import Path
import queue
import re
import secrets
import socket
import ssl
import sys
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
MAX_ORDER_VALUE_IRR = 50_000_000
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


TRACE_DIRECTORY = Path(__file__).resolve().parent / "logs"
TRACE_TRANSPORTS = frozenset({
    "broker_response", "transport_timeout", "transport_failure", "tls_failure",
    "authentication_rejected", "broker_throttled", "http_error", "response_too_large",
    "malformed_acknowledgement", "malformed_response", "non_json_response",
    "connection_capacity_timeout", "transport_closed", "initiation_cancelled_or_cutoff",
    "native_verification_required", "explicit_live_authorization_required",
})
TRACE_STOPS = TRACE_TRANSPORTS | frozenset("""cutoff cancelled cancelled_or_broker_stop
    cancelled_during_cleanup worker_start_failure confirmation_cancelled
    trace_writer_failed trace_queue_exhausted trace_event_invalid
    live_requires_interactive_authentication interactive_authentication_failed
    authentication_teardown_failed existing_playwright_unavailable
    invalid_auth_material invalid_native_handoff unavailable_session_state unexpected_login_origin
    no_drafts invalid_draft_selection invalid_number invalid_integer invalid_local_target
    local_target_passed invalid_dispatch_window duration_precision live_interval_below_300_ms
    invalid_dispatch_limits explicit_confirmation_required live_authorization_or_preflight_failed
    stale_preflight_or_late_start client_identity_changed connection_warmup_timeout connection_warmup_failed
    invalid_draft_identity invalid_draft_side only_day_buy_verified instrument_identity_mismatch
    invalid_instrument_identity invalid_instrument_name instrument_not_buyable instrument_not_tradable
    malformed_drafts malformed_instrument_metadata malformed_money invalid_commission
    unsupported_market_unit price_constraint quantity_constraint minimum_buy_value insufficient_buying_power
    per_order_safety_cap invalid_client_origin invalid_transport_limits operation_not_allowed
    unexpected_failure_no_retry other_failure""".split())


class RunTrace:
    """Bounded, ordered producer buffer; only the writer touches disk after setup.

    Exhaustion stops dispatch and reserves space for the bounded workers and
    cleanup events. A failed write retains the head and buffer for a final flush
    on close. No request is retried. Pending workers are observed until close;
    their eventual broker outcome may remain unknown after this local run ends.
    """

    EVENTS = frozenset("""run_started authentication_started authentication_completed
        native_verification_completed preflight_completed user_confirmation
        connection_warmup_started connection_warmup_completed final_preflight_completed
        window_configured final_preflight_started connection_refresh_started connection_refresh_completed
        dispatch_started dispatch_window_ended drain_started drain_completed
        drain_deadline_reached dispatch_report_snapshot run_completed run_aborted
        attempt_initiated attempt_result_completed attempt_pending_at_snapshot
        capacity_skipped non_initiated_outcome attempt_assigned connection_ready
        http_request_returned http_headers_received http_exchange_failed
        attempt_pending_before_initiation""".split())
    NUMBERS = frozenset("""attempt_number scheduled_attempt scheduled_monotonic_ns
        initiation_monotonic_ns gap_ns completion_monotonic_ns elapsed_ns
        planned_attempts scheduled_attempts initiated_attempts capacity_skips
        worker_capacity http_responses_observed completed_broker_acknowledgements
        completed_unknown_outcomes pending_attempts workers_still_running
        start_monotonic_ns cutoff_monotonic_ns drain_seconds snapshot_monotonic_ns
        target_epoch_seconds local_utc_offset_seconds duration_ns interval_ns
        pending_before_initiation non_initiated_attempts""".split())
    FLAGS = frozenset({"confirmed", "pending_at_snapshot", "worker_alive", "completed_result_available",
                       "reused_connection"})
    ENUMS = {
        "transport": TRACE_TRANSPORTS | {"other_transport_outcome"},
        "broker_acceptance": {"accepted", "rejected", "unknown"},
        "rejection_category": {"market_entry_time", "unspecified"},
        "outcome": {"completed", "aborted", "confirmation_cancelled"},
        "completion_observation": {"until_trace_close"},
        "stop_category": TRACE_STOPS,
        "trace_failure": {"trace_writer_failed", "trace_queue_exhausted", "trace_event_invalid"},
        "exchange_phase": {"pool", "prepare", "connect", "admission", "send", "headers", "body"},
    }

    def __init__(self, run_id, *, directory=None, capacity=4096):
        self._condition = threading.Condition()
        self._pending = deque()
        self._capacity = capacity
        self._closing = False
        self._closed = False
        self._sequence = 0
        self._failure = None
        self._cancel = None
        self.unwritten_events = 0
        self._file = None
        try:
            if not re.fullmatch(r"[0-9a-f]{16}", run_id) or capacity < 1:
                raise ValueError
            self.run_id = run_id
            directory = TRACE_DIRECTORY if directory is None else Path(directory)
            directory.mkdir(parents=True, exist_ok=True)
            stem = datetime.now().astimezone().strftime("opening_order_%Y%m%d_%H%M%S_") + run_id
            for index in range(8):
                self.path = directory / (stem + ("_" + secrets.token_hex(4) if index else "") + ".jsonl")
                try:
                    self._file = self.path.open("x", encoding="utf-8", newline="\n")
                    break
                except FileExistsError:
                    continue
            if self._file is None:
                raise OSError
            self._write(self._record("run_started", {}))
            self._writer = threading.Thread(target=self._write_loop, daemon=True, name="run-trace-writer")
            self._writer.start()
        except Exception:
            if self._file is not None:
                try:
                    self._file.close()
                except Exception:
                    pass
            raise Blocked("trace_initialization_failed") from None

    @property
    def failure(self):
        with self._condition:
            return self._failure

    def bind_cancel(self, cancel):
        with self._condition:
            self._cancel = cancel
            if self._failure:
                cancel.set()

    def _fail(self, category):
        # Caller owns the condition. Never export an exception message.
        self._failure = self._failure or category
        if self._cancel is not None:
            self._cancel.set()
        self._condition.notify_all()

    def _record(self, event, fields):
        self._sequence += 1
        return {"event": event, "run_id": self.run_id, "sequence": self._sequence,
                "local_timestamp": datetime.now().astimezone().isoformat(timespec="microseconds"),
                "monotonic_ns": time.perf_counter_ns(), **fields}

    def emit(self, event, **fields):
        with self._condition:
            # The snapshot explicitly records workers whose completion can outlive
            # the trace. Do not reopen a closed file for those daemon workers.
            if self._closed or self._closing:
                return False
            valid = event in self.EVENTS
            for key, value in fields.items():
                if value is None:
                    valid = valid and key in self.NUMBERS | self.FLAGS | self.ENUMS.keys() | {"http_status"}
                elif key in self.NUMBERS:
                    valid = valid and type(value) in (int, float) and math.isfinite(value)
                elif key in self.FLAGS:
                    valid = valid and type(value) is bool
                elif key == "http_status":
                    valid = valid and type(value) is int and 100 <= value <= 599
                else:
                    valid = valid and key in self.ENUMS and type(value) is str and value in self.ENUMS.get(key, ())
            if not valid:
                self._fail("trace_event_invalid")
                return False
            if len(self._pending) >= self._capacity:
                self._fail("trace_queue_exhausted")
            # Reserve exceeds the maximum cleanup events from 16 workers. The
            # explicit counter surfaces any loss even for a misbehaving producer.
            if len(self._pending) >= self._capacity + 256:
                self.unwritten_events += 1
                return False
            if event == "run_completed" and self._failure:
                event = "run_aborted"
                fields.update(outcome="aborted", trace_failure=self._failure, stop_category=self._failure)
            self._pending.append(self._record(event, fields))
            self._condition.notify()
            return self._failure is None

    def admit_initiation(self, **fields):
        """Atomically admit an initiation while healthy, ordered against _fail.

        The condition uses an RLock, so emit validates and appends under the
        same lock. Rejected initiations never consume the cleanup reserve.
        Once admitted, the request is in-flight even if a later failure is
        published before the HTTP call. No disk I/O occurs under this lock.
        """
        with self._condition:
            if self._failure:
                return False
            if len(self._pending) >= self._capacity:
                self._fail("trace_queue_exhausted")
                return False
            if not self.emit("attempt_initiated", **fields):
                self._fail("trace_event_invalid")
                return False
            return True

    def result(self, event, result, **fields):
        self.emit(event, transport=(result.category if result.category in TRACE_TRANSPORTS
                                   else "other_transport_outcome"),
                  http_status=result.status if type(result.status) is int and 100 <= result.status <= 599 else None,
                  broker_acceptance=(result.acceptance if result.acceptance in {"accepted", "rejected"} else "unknown"),
                  rejection_category=(result.rejection_reason if result.rejection_reason in
                                      {"market_entry_time", "unspecified"} else None), **fields)

    def check(self):
        if self.failure:
            raise Blocked(self.failure)

    def _write(self, record):
        offset = self._file.tell()
        try:
            self._file.write(json.dumps(record, ensure_ascii=True, allow_nan=False) + "\n")
            self._file.flush()
        except Exception:
            # A recoverable partial write must not leave a broken/duplicate line
            # when close makes its final attempt to persist the retained head.
            try:
                self._file.seek(offset)
                self._file.truncate()
            except Exception:
                pass
            raise

    def _write_loop(self):
        failed_write = False
        try:
            while True:
                with self._condition:
                    self._condition.wait_for(lambda: self._closing or (self._pending and not failed_write))
                    if not self._pending:
                        if self._closing:
                            break
                        continue
                    record = self._pending[0]
                    if record["event"] == "run_completed" and self._failure:
                        record = {**record, "event": "run_aborted", "outcome": "aborted",
                                  "trace_failure": self._failure, "stop_category": self._failure}
                try:
                    self._write(record)
                except Exception:
                    with self._condition:
                        self._fail("trace_writer_failed")
                        if self._closing:
                            break
                    failed_write = True
                    continue
                with self._condition:
                    self._pending.popleft()
        finally:
            with self._condition:
                self.unwritten_events += len(self._pending)
            try:
                self._file.close()
            except Exception:
                with self._condition:
                    self._fail("trace_writer_failed")

    def close(self, *, outcome=None, stop_category="other_failure"):
        with self._condition:
            if outcome is not None and not self._closing:
                # Seal the terminal event and admission together, so a late
                # worker cannot append a result after the run's final event.
                self.emit("run_completed" if outcome == "completed" else "run_aborted",
                          outcome=outcome, trace_failure=self._failure, stop_category=stop_category)
            self._closing = True
            self._condition.notify_all()
        self._writer.join()
        with self._condition:
            self._closed = True
        return self.failure


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
    rejection_reason: str | None = None


def rejection_reason(data):
    """Recognize only the public timing error evidenced by the PO's screenshot.

    Do not export arbitrary broker messages: they can contain private data.
    An unrecognized or missing reason remains unspecified, never guessed.
    """
    messages = [data.get("message")]
    errors = data.get("omsError")
    if isinstance(errors, str):
        messages.append(errors)
    elif isinstance(errors, list):
        messages.extend(e.get("error") for e in errors[:3] if isinstance(e, dict))
    for message in messages:
        if not isinstance(message, str):
            continue
        normalized = "".join(message[:4000].replace("\u200c", " ").replace("ي", "ی").split())
        if "محدودهزمانیسفارشمعتبرنمیباشد" in normalized:
            return "market_entry_time"
    return "unspecified"


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

        handed_off = 0
        try:
            for conn in borrowed:
                if conn is not None and conn.sock is not None:
                    self._release(conn, True)
                else:
                    worker = threading.Thread(target=warm_slot, args=(conn,), daemon=True, name="native-connect")
                    worker.start()
                    workers.append(worker)
                handed_off += 1
        except RuntimeError:
            self.verified = False
            raise Blocked("connection_warmup_failed") from None
        finally:
            for conn in borrowed[handed_off:]:
                self._release(conn, True)
        for worker in workers:
            worker.join(max(0, (deadline_ns - time.perf_counter_ns()) / 1e9))
        if any(worker.is_alive() for worker in workers) or time.perf_counter_ns() >= deadline_ns:
            self.verified = False
            raise Blocked("connection_warmup_timeout")
        if errors:
            self.verified = False
            raise Blocked(errors[0])

    def _exchange(self, method, path, body=None, before_request=None, observe=None):
        with self._lock:
            if self._closed:
                raise Blocked("transport_closed")
        try:
            conn = self._pool.get(timeout=self._timeout)
        except queue.Empty:
            if observe is not None:
                observe("http_exchange_failed", exchange_phase="pool", transport="connection_capacity_timeout")
            raise Blocked("connection_capacity_timeout") from None
        reusable = False
        status = None
        phase = "prepare"
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
            reused = conn.sock is not None
            phase = "connect"
            if not reused:
                conn.connect()
            if observe is not None:
                observe("connection_ready", reused_connection=reused)
            phase = "admission"
            if before_request is not None and not before_request():
                raise Blocked("initiation_cancelled_or_cutoff")
            phase = "send"
            conn.request(method, path, body=body, headers=headers)
            if observe is not None:
                observe("http_request_returned")
            phase = "headers"
            response = conn.getresponse()
            status = response.status
            if observe is not None:
                observe("http_headers_received", http_status=status)
            phase = "body"
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
        except (Blocked, OSError, http.client.HTTPException) as exc:
            if isinstance(exc, Blocked):
                category = exc.category
            elif isinstance(exc, ssl.SSLError):
                category = "tls_failure"
            elif isinstance(exc, TimeoutError):
                category = "transport_timeout"
            else:
                category = "transport_failure"
            if observe is not None:
                observe("http_exchange_failed", exchange_phase=phase, transport=category, http_status=status)
            raise Blocked(category, status) from None
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

    def submit(self, body, *, approved=False, on_initiated=None, observe=None):
        if not self.live_enabled or not approved:
            return HttpResult("explicit_live_authorization_required")
        if not self.verified:
            return HttpResult("native_verification_required")
        status = None
        try:
            status, kind, raw = self._exchange("POST", ORDER, body, before_request=on_initiated, observe=observe)
            self._status(status)
            data = parse_json(raw, kind)
            if not isinstance(data, dict) or type(data.get("isSuccessful")) is not bool:
                raise Blocked("malformed_acknowledgement")
            if not data["isSuccessful"]:
                return HttpResult("broker_response", status, "rejected", time.perf_counter_ns(),
                                  rejection_reason(data))
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
    scheduled_attempt: int | None = None


@dataclass
class DispatchReport:
    planned: int
    attempts: list[Attempt] = field(default_factory=list)
    stop: str = "cutoff"
    capacity_skips: int = 0
    scheduled_attempts: int = 0
    non_initiated: list[str] = field(default_factory=list)
    worker_capacity: int = 0
    skipped: set[int] = field(default_factory=set)
    non_initiated_by_slot: dict[int, str] = field(default_factory=dict)
    _snapshot: dict | None = field(default=None, init=False, repr=False)

    def _collect(self):
        snapshot = [(a.number, a.initiated_ns, a.result, a.scheduled_attempt) for a in self.attempts]
        slots = {slot: (n, r) for n, _, r, slot in snapshot if slot is not None}
        rows = []
        for slot in range(1, self.scheduled_attempts + 1):
            number, result = slots.get(slot, (None, None))
            if number is not None:
                state = result.acceptance if result else "pending"
                detail = result.category if result else None
            elif slot in self.skipped:
                state, detail = "capacity_skipped", None
            elif slot in self.non_initiated_by_slot:
                state, detail = "not_initiated", self.non_initiated_by_slot[slot]
            else:
                state, detail = "pending_before_initiation", None
            rows.append({"scheduled_attempt": slot, "attempt_number": number, "state": state,
                         "transport": detail, "http_status": result.status if result else None,
                         "rejection_reason": result.rejection_reason if result else None})
        return {"theoretical_attempts": self.planned, "local_initiations": len(snapshot),
                "stop": self.stop, "capacity_skips": self.capacity_skips,
                "scheduled_attempts": self.scheduled_attempts,
                "worker_capacity": self.worker_capacity,
                "non_initiated_outcomes": list(self.non_initiated),
                "http_responses_observed": sum(r is not None and r.status is not None for _, _, r, _ in snapshot),
                "broker_results_observed": sum(r is not None and r.acceptance != "unknown" for _, _, r, _ in snapshot),
                "broker_results_unknown": sum(r is None or r.acceptance == "unknown" for _, _, r, _ in snapshot),
                "pending_attempts": sum(r is None for _, _, r, _ in snapshot),
                "pending_before_initiation": sum(row["state"] == "pending_before_initiation" for row in rows),
                "completed_unknown_outcomes": sum(r is not None and r.acceptance == "unknown" for _, _, r, _ in snapshot),
                "rows": rows,
                "attempts": [{"number": n, "monotonic_ns": stamp, "scheduled_attempt": slot,
                              "transport": r.category if r else "outstanding_unknown",
                              "http_status": r.status if r else None,
                              "completion_monotonic_ns": r.completed_ns if r else None,
                              "broker_acceptance": r.acceptance if r else "unknown",
                              "rejection_reason": r.rejection_reason if r else None,
                              "execution": "unknown"} for n, stamp, r, slot in snapshot]}

    def diagnostics(self):
        # A late worker can add a trace event, but cannot rewrite the drain snapshot.
        return {**(self._snapshot if self._snapshot is not None else self._collect()), "stop": self.stop}


def format_duration(nanoseconds):
    micros = max(0, nanoseconds) // 1000
    seconds, fraction = divmod(micros, 1_000_000)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}.{fraction:06}"


class LiveConsole:
    """One presentation/input thread; dispatch never writes or waits for output."""

    def __init__(self, start_ns, window, cancel, *, stream=None, clock=time.perf_counter_ns,
                 poll_cancel=None):
        self.start_ns, self.window, self.cancel = start_ns, window, cancel
        self.stream = sys.stdout if stream is None else stream
        self.clock = clock
        self.poll_cancel = poll_cancel or self._escape_pressed
        self.stage = "Preparing"
        self.report = None
        self._stop = threading.Event()
        self._worker = None

    @staticmethod
    def _escape_pressed():
        if not sys.stdin.isatty():
            return False
        try:
            import msvcrt
        except ImportError:
            return False
        return msvcrt.kbhit() and msvcrt.getwch() in ("\x1b", "\x03")

    def frame(self):
        now = self.clock()
        count = len(self.report.attempts) if self.report is not None else 0
        stage = "Cancelling" if self.cancel.is_set() else self.stage
        if now < self.start_ns:
            return f"{stage} | Starts in {format_duration(self.start_ns - now)} | Requests {count}"
        elapsed = min(max(0, now - self.start_ns), self.window.duration_ns)
        remaining = max(0, self.start_ns + self.window.duration_ns - now)
        if stage == "Ready":
            stage = "Sending" if remaining else "Finishing"
        return (f"{stage} | Elapsed {format_duration(elapsed)} | "
                f"Left {format_duration(remaining)} | Requests {count}")

    def _render(self):
        width = 0
        try:
            while not self._stop.is_set():
                if self.poll_cancel():
                    self.cancel.set()
                line = self.frame()
                self.stream.write("\r" + line.ljust(width))
                width = max(width, len(line))
                self.stream.flush()
                self._stop.wait(.05)
        except Exception:
            # Console failure must not kill or serialize a handed-off POST.
            return

    def __enter__(self):
        print("Approved. Preparing live dispatch; ESC or Ctrl+C stops future requests.",
              file=self.stream, flush=True)
        self._worker = threading.Thread(target=self._render, daemon=True, name="live-console")
        self._worker.start()
        return self

    def __exit__(self, *_):
        self._stop.set()
        self._worker.join(.25)
        if not self._worker.is_alive():
            print(file=self.stream, flush=True)


def print_live_summary(report):
    data = report.diagnostics()
    outcomes = data["attempts"]
    accepted = sum(a["broker_acceptance"] == "accepted" for a in outcomes)
    rejected = sum(a["broker_acceptance"] == "rejected" for a in outcomes)
    unknown = data["completed_unknown_outcomes"]
    stop = "configured duration ended" if report.stop == "cutoff" else report.stop.replace('_', ' ')
    print(f"Window finished ({stop}). "
          f"Requests initiated: {len(outcomes)} / planned {report.planned}.")
    print(f"Broker responses: accepted {accepted} | rejected {rejected} | unknown {unknown}.")
    print(f"Pending after drain: {data['pending_attempts']}.")
    if data["rows"]:
        print("Scheduled | Attempt | Outcome | HTTP | Detail")
        for row in data["rows"]:
            detail = row["rejection_reason"] or row["transport"] or "-"
            print(f"{row['scheduled_attempt']:>9} | {str(row['attempt_number'] or '-'):>7} | "
                  f"{row['state']} | {row['http_status'] or '-'} | {detail}")
    if any(a["rejection_reason"] == "market_entry_time" for a in outcomes):
        print("Broker rejection reason: order time window is invalid.")
    if any(a["rejection_reason"] == "unspecified" for a in outcomes):
        print("The broker rejected requests without a recognized public reason; no cause was assumed.")
    if report.capacity_skips:
        print(f"Skipped scheduled calls while all workers were occupied: {report.capacity_skips}.")
    if unknown or data["pending_attempts"]:
        print("Unknown outcomes must not be replayed automatically.")
    print("Execution/fills were not verified. Check broker orders independently.")


def dispatch(submit, body, window, start_ns, *, approved=False, cancel=None,
             concurrency=4, drain_seconds=4.0, clock=time.perf_counter_ns, pause=time.sleep, progress=None,
             trace=None, observe_transport=False):
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
    if trace is not None:
        trace.bind_cancel(cancel)
        trace.check()
        trace.emit("dispatch_started", planned_attempts=report.planned, worker_capacity=concurrency,
                   start_monotonic_ns=start_ns, cutoff_monotonic_ns=start_ns + window.duration_ns)
    if progress is not None:
        progress.report = report
        progress.stage = "Preparing dispatch"
    cutoff, due = start_ns + window.duration_ns, start_ns
    idle = queue.Queue(concurrency)
    shutdown = threading.Event()
    lock = threading.Lock()
    workers = []
    attempt_workers = {}
    last = None

    def initiate(ready, scheduled_ns, scheduled_number):
        nonlocal last
        attempt = None

        def before_request():
            nonlocal last, attempt
            with lock:
                stamp = clock()
                if (cancel.is_set() or stamp >= cutoff
                        or (last is not None and stamp - last < window.interval_ns)):
                    return False
                attempt_number = len(report.attempts) + 1
                if trace is not None and not trace.admit_initiation(
                        attempt_number=attempt_number, scheduled_attempt=scheduled_number,
                        scheduled_monotonic_ns=scheduled_ns, initiation_monotonic_ns=stamp,
                        gap_ns=None if last is None else stamp - last):
                    cancel.set()
                    return False
                attempt = Attempt(attempt_number, stamp, scheduled_attempt=scheduled_number)
                report.attempts.append(attempt)
                if trace is not None:
                    attempt_workers[attempt.number] = threading.current_thread()
                last = stamp
                ready.set()
                return True

        def observe(event, **fields):
            trace.emit(event, scheduled_attempt=scheduled_number,
                       attempt_number=attempt.number if attempt else None, **fields)

        try:
            try:
                if trace is not None and observe_transport:
                    result = submit(body, before_request, observe)
                else:
                    result = submit(body, before_request)
            except Exception:
                result = HttpResult("transport_failure")
            with lock:
                if attempt is not None:
                    attempt.result = result
                    if trace is not None:
                        completed = result.completed_ns if result.completed_ns is not None else clock()
                        trace.result("attempt_result_completed", result, attempt_number=attempt.number,
                                     scheduled_attempt=scheduled_number,
                                     completion_monotonic_ns=completed,
                                     elapsed_ns=max(0, completed - attempt.initiated_ns))
                else:
                    report.non_initiated.append(result.category)
                    report.non_initiated_by_slot[scheduled_number] = result.category
                    if trace is not None:
                        trace.result("non_initiated_outcome", result, scheduled_attempt=scheduled_number,
                                     scheduled_monotonic_ns=scheduled_ns)
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
                ready, scheduled_ns, scheduled_number = inbox.get(timeout=.05)
            except queue.Empty:
                if shutdown.is_set():
                    return
                continue
            initiate(ready, scheduled_ns, scheduled_number)
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
        if progress is not None:
            progress.stage = "Ready"
        while not cancel.is_set() and clock() < cutoff:
            if not wait_until(due, cancel, clock=clock, pause=pause) or clock() >= cutoff:
                break
            report.scheduled_attempts += 1
            try:
                inbox = idle.get_nowait()
            except queue.Empty:
                report.capacity_skips += 1
                report.skipped.add(report.scheduled_attempts)
                if trace is not None:
                    trace.emit("capacity_skipped", scheduled_attempt=report.scheduled_attempts,
                               scheduled_monotonic_ns=due)
                due = clock() + window.interval_ns
                continue
            ready = threading.Event()
            initiated_before = len(report.attempts)
            if trace is not None:
                trace.emit("attempt_assigned", scheduled_attempt=report.scheduled_attempts,
                           scheduled_monotonic_ns=due)
            inbox.put_nowait((ready, due, report.scheduled_attempts))
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
        if trace is not None:
            trace.emit("dispatch_window_ended")
            trace.emit("drain_started", drain_seconds=drain_seconds)
        if progress is not None:
            progress.stage = "Finishing"
        shutdown.set()
        end = time.perf_counter() + drain_seconds
        for worker in workers:
            try:
                worker.join(max(0, end - time.perf_counter()))
            except KeyboardInterrupt:
                cancel.set()
                report.stop = "cancelled_during_cleanup"
                break
        with lock:
            if trace is not None:
                if trace.failure:
                    report.stop = trace.failure
                snapshot_ns = clock()
                running = sum(worker.is_alive() for worker in workers)
                trace.emit("drain_deadline_reached" if running else "drain_completed",
                           workers_still_running=running)
            snapshot = report._snapshot = report._collect()
            if trace is not None:
                snapshot["snapshot_monotonic_ns"] = snapshot_ns
                for attempt in report.attempts:
                    if attempt.result is None:
                        trace.emit("attempt_pending_at_snapshot", attempt_number=attempt.number,
                                   scheduled_attempt=attempt.scheduled_attempt,
                                   pending_at_snapshot=True, completed_result_available=False,
                                   completion_observation="until_trace_close",
                                   worker_alive=attempt_workers[attempt.number].is_alive(),
                                   snapshot_monotonic_ns=snapshot_ns)
                for row in snapshot["rows"]:
                    if row["state"] == "pending_before_initiation":
                        trace.emit("attempt_pending_before_initiation", scheduled_attempt=row["scheduled_attempt"],
                                   snapshot_monotonic_ns=snapshot_ns)
                trace.emit("dispatch_report_snapshot", planned_attempts=report.planned,
                           scheduled_attempts=report.scheduled_attempts, initiated_attempts=snapshot["local_initiations"],
                           capacity_skips=report.capacity_skips, worker_capacity=report.worker_capacity,
                           http_responses_observed=snapshot["http_responses_observed"],
                           completed_broker_acknowledgements=snapshot["broker_results_observed"],
                           completed_unknown_outcomes=snapshot["completed_unknown_outcomes"],
                           pending_attempts=snapshot["pending_attempts"], workers_still_running=running,
                           pending_before_initiation=snapshot["pending_before_initiation"],
                           non_initiated_attempts=len(snapshot["non_initiated_outcomes"]),
                           snapshot_monotonic_ns=snapshot_ns, trace_failure=trace.failure,
                           stop_category=report.stop if report.stop in TRACE_STOPS else "other_failure")
                if trace.failure:
                    report.stop = trace.failure
    return report


def live_dispatch(client, approved_order, fresh, window, start_ns, *, confirmed=False, cancel=None, progress=None,
                  trace=None):
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
    def submit(data, begin, observe=None):
        return client.submit(data, approved=True, on_initiated=begin, observe=observe)

    return dispatch(submit, body, window, start_ns,
                    approved=True, cancel=cancel, concurrency=client.dispatch_capacity(window), progress=progress,
                    trace=trace, observe_transport=True)


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
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--authenticate", action="store_true", help="PO-only interactive login and native read-only verification")
    parser.add_argument("--mobile", action="store_true")
    parser.add_argument("--preflight", action="store_true", help="PO-only full read-only draft/financial preview; requires --authenticate")
    parser.add_argument("--live", action="store_true", help="PO-only, requires authentication, fresh preflight and per-window confirmation")
    parser.add_argument("--diagnostics", action="store_true", help="print sanitized technical JSON once after the run; live tracing is always enabled")
    args = parser.parse_args(argv)
    diagnostics = {"run_id": secrets.token_hex(8), "authentication_handoff": "not_requested",
                   "native_read_only": "not_checked", "live_requested": args.live}
    client = None
    trace = None
    outcome = "aborted"
    exit_code = 0

    def stage(event, **fields):
        if trace is not None:
            trace.emit(event, **fields)
            trace.check()

    try:
        if args.live:
            trace = RunTrace(diagnostics["run_id"])
        if (args.live or args.preflight) and not args.authenticate:
            raise Blocked("live_requires_interactive_authentication")
        if not args.authenticate:
            diagnostics.update(mode="offline", order_requests=0, interval_ms=350,
                               theoretical_attempts=Window.from_inputs().attempts)
            print("Offline mode. No network or orders. Use --authenticate for read-only verification.")
            return 0
        print("Sign in manually in Chrome, including MFA/CAPTCHA. Browser closes before native HTTP verification.")
        diagnostics["authentication_handoff"] = "started"
        stage("authentication_started")
        auth = authenticate_browser(origin=MOBILE if args.mobile else DESKTOP)
        diagnostics["authentication_handoff"] = "browser_context_and_playwright_closed"
        stage("authentication_completed")
        client = NativeHttp(auth, live_enabled=args.live)
        drafts = client.verify()
        diagnostics["native_read_only"] = client.read_outcome
        stage("native_verification_completed")
        if not args.live and not args.preflight:
            print("Native HTTP session verified. Read-only money/draft checks completed; no order POSTs.")
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
        stage("window_configured", target_epoch_seconds=int(target.timestamp()),
              local_utc_offset_seconds=int(target.utcoffset().total_seconds()),
              duration_ns=window.duration_ns, interval_ns=window.interval_ns, planned_attempts=window.attempts)
        if args.live and window.interval_ns < MIN_LIVE_INTERVAL_NS:
            raise Blocked("live_interval_below_300_ms")
        initial = preflight(client, draft, quantity, price)
        stage("preflight_completed")
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
            print("Read-only preview complete. No order POSTs were sent.")
            return 0
        confirmed = confirm_order()
        stage("user_confirmation", confirmed=confirmed)
        if not confirmed:
            diagnostics["stop"] = "confirmation_cancelled"
            outcome = "confirmation_cancelled"
            print("Cancelled before dispatch. No order POSTs were sent.")
        else:
            cancel = threading.Event()
            start_ns = monotonic_target(target)
            with LiveConsole(start_ns, window, cancel) as progress:
                progress.stage = "Countdown"
                if not wait_until(start_ns - 5_000_000_000, cancel):
                    raise Blocked("cancelled")
                progress.stage = "Preparing connections"
                stage("connection_warmup_started")
                client.warm_connections(client.dispatch_capacity(window), start_ns)
                stage("connection_warmup_completed")
                if cancel.is_set():
                    raise Blocked("cancelled")
                progress.stage = "Final preflight"
                stage("final_preflight_started")
                fresh = preflight(client, draft, quantity, price)
                stage("final_preflight_completed")
                if cancel.is_set():
                    raise Blocked("cancelled")
                progress.stage = "Refreshing connections"
                stage("connection_refresh_started")
                # Replace any pool entries closed by the final reads before the window.
                client.warm_connections(client.dispatch_capacity(window), start_ns)
                stage("connection_refresh_completed")
                if cancel.is_set():
                    raise Blocked("cancelled")
                report = live_dispatch(client, order, fresh, window, start_ns, confirmed=True, cancel=cancel,
                                       progress=progress, trace=trace)
            diagnostics.update(report.diagnostics())
            if trace.failure:
                report.stop = trace.failure
                diagnostics["stop"] = trace.failure
            print_live_summary(report)
            outcome = "completed" if report.stop == "cutoff" else "aborted"
    except Blocked as exc:
        diagnostics["stop"] = exc.category
        if diagnostics["authentication_handoff"] == "started":
            diagnostics["authentication_handoff"] = "failed"
        if client is not None:
            diagnostics["native_read_only"] = client.read_outcome
        print("Stopped: " + exc.category.replace("_", " ") + ". No automatic replay.")
        exit_code = 2
    except KeyboardInterrupt:
        diagnostics["stop"] = "cancelled"
        print("Cancelled. Transmitted requests cannot be recalled; no automatic replay.")
        exit_code = 130
    except Exception:
        diagnostics["stop"] = "unexpected_failure_no_retry"
        print("Stopped after an unexpected failure. Check broker orders before any new run; no automatic replay.")
        exit_code = 2
    finally:
        try:
            if client is not None:
                client.close()
        finally:
            if trace is not None:
                failure = trace.close(outcome=outcome,
                                      stop_category=(diagnostics.get("stop") if diagnostics.get("stop") in TRACE_STOPS
                                                     else "other_failure"))
                if failure:
                    diagnostics["stop"] = failure
                    diagnostics["trace_unwritten_events"] = trace.unwritten_events
                    print("Stopped: " + failure.replace("_", " ") +
                          f". Trace events not persisted: {trace.unwritten_events}. No automatic replay.")
        if args.diagnostics:
            print(json.dumps(diagnostics, sort_keys=True))
    return 2 if trace is not None and trace.failure else exit_code


if __name__ == "__main__":
    raise SystemExit(main())
