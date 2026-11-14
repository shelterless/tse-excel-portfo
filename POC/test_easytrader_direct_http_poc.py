"""Offline tests: python -m unittest discover -s POC -p test_easytrader_direct_http_poc.py -v

Include real Chrome teardown on a fake loopback login (no broker credentials):
    $env:POC_REAL_BROWSER='1'; python -m unittest discover -s POC -p test_easytrader_direct_http_poc.py -v
"""

import contextlib
import copy
from dataclasses import replace
from datetime import datetime, timedelta
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import socket
import ssl
import threading
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import easytrader_direct_http_poc as poc


AT = datetime.fromisoformat("2026-11-08T08:45:00+03:30")
ISIN = "IRTEST000001"
FAKE_TOKEN = "Bearer fake-offline-token"
FAKE_COOKIE = "fake-offline-cookie"


def fixtures():
    draft = dict(id="fake-draft", symbolIsin=ISIN, symbolName="TEST", side=0,
                 quantity=1000, price=1000, validityType=0)
    symbol = dict(symbolIsin=ISIN, symbolName="TEST", isActive=True, canBuy=True,
                  marketUnit=3, tradingTimeType=1, minDealablePrice="0.5", minDealableCount=10,
                  minValidBuyVolume=10, maxValidBuyVolume=10000, buyCommission="0.00036875",
                  hidePrice="0.1", csize=None)
    market = dict(symbolIsin=ISIN, stateCode="A", lowAllowedPrice=900, highAllowedPrice=1100)
    return draft, symbol, market


def auth(origin=poc.DESKTOP):
    material = poc.capture_material({"Authorization": FAKE_TOKEN, "x-device-id": "fake-device",
                                     "User-Agent": "must-not-copy", "unrelated": "must-not-copy"},
                                    [dict(name="session", value=FAKE_COOKIE, domain="127.0.0.1",
                                          path="/", secure=False, expires=-1)], origin)
    material.teardown_complete = True
    return material


def simulated_submit(action):
    def submit(body, before_request):
        if not before_request():
            return poc.HttpResult("initiation_cancelled_or_cutoff")
        return action(body)
    return submit


class FakeClock:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()
        self.jump = 0

    def __call__(self):
        with self.lock:
            return self.value

    def advance(self, seconds):
        with self.lock:
            self.value += int(seconds * 1e9) + self.jump
            self.jump = 0


class FakeCancel(threading.Event):
    def __init__(self, clock):
        super().__init__()
        self.clock = clock

    def wait(self, timeout=None):
        self.clock.advance(timeout or 0)
        return self.is_set()


class Server:
    def __init__(self):
        self.received = []
        self.lock = threading.Lock()
        self.delay = 0
        self.order_status = 200
        self.order_responses = []
        self.money_status = 200
        self.money_body = None
        self.money_kind = "application/json"
        self.ack = {"isSuccessful": True, "id": "fake-order"}
        self.require_token = True
        self.require_cookie = True
        self.cancel_on_receive = None
        self.drop_order_response = False
        self.active = self.max_active = 0
        owner = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):
                pass

            def handle(self):
                try:
                    super().handle()
                except (ConnectionAbortedError, ConnectionResetError):
                    pass  # Expected when a timeout closes a local fixture connection.

            def send(self, status, body, kind="application/json", extra=None):
                data = body if isinstance(body, bytes) else poc.decimal_json(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", kind)
                self.send_header("Content-Length", str(len(data)))
                for key, value in (extra or {}).items():
                    self.send_header(key, value)
                self.end_headers()
                try:
                    self.wfile.write(data)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass

            def do_GET(self):
                self.handle_api()

            def do_POST(self):
                self.handle_api()

            def handle_api(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                if self.path == "/":
                    # Pure HTTP login simulation: redirect and an HttpOnly cookie.
                    self.send(302, b"", extra={"Location": poc.MONEY,
                              "Set-Cookie": "session=" + FAKE_COOKIE + "; Path=/; HttpOnly; SameSite=Lax"})
                    return
                valid = (not owner.require_token or self.headers.get("Authorization") == FAKE_TOKEN)
                valid = valid and (not owner.require_cookie or self.headers.get("Cookie") == "session=" + FAKE_COOKIE)
                if not valid:
                    self.send(401, {"private": "fake-private-rejection"})
                    return
                draft, symbol, market = fixtures()
                if self.path == poc.ORDER:
                    with owner.lock:
                        index = len(owner.received)
                        owner.received.append((time.perf_counter_ns(), body))
                        status, ack, delay, drop = (owner.order_responses[index]
                            if index < len(owner.order_responses)
                            else (owner.order_status, owner.ack, owner.delay, owner.drop_order_response))
                        owner.active += 1
                        owner.max_active = max(owner.active, owner.max_active)
                    if owner.cancel_on_receive is not None:
                        owner.cancel_on_receive.set()
                    try:
                        time.sleep(delay)
                        if drop:
                            self.close_connection = True
                            self.connection.shutdown(socket.SHUT_RDWR)
                        else:
                            self.send(status, ack)
                    finally:
                        with owner.lock:
                            owner.active -= 1
                    return
                values = {poc.MONEY: {"buyPowerT2": 100000000}, poc.DRAFTS: [draft],
                          poc.SYMBOLS: {"symbols": [symbol]}, poc.MARKET: [market]}
                if self.path == poc.MONEY:
                    self.send(owner.money_status, owner.money_body if owner.money_body is not None else values[poc.MONEY], owner.money_kind)
                elif self.path in values:
                    if self.path == poc.SYMBOLS and body != b'{"hash":"null"}':
                        self.send(400, {})
                    elif self.path == poc.MARKET and json.loads(body) != [ISIN]:
                        self.send(400, {})
                    else:
                        self.send(200, values[self.path])
                else:
                    self.send(404, {})

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.httpd.daemon_threads = True
        self.origin = "http://127.0.0.1:" + str(self.httpd.server_port)

    def __enter__(self):
        self.thread = threading.Thread(target=self.httpd.serve_forever, kwargs={"poll_interval": .01}, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(1)

    def client(self, *, material=None, timeout=3, live_enabled=True):
        return poc.NativeHttp(material or auth(), api_origin=self.origin, loopback=True,
                              timeout=timeout, live_enabled=live_enabled)


class OfflineCase(unittest.TestCase):
    def setUp(self):
        self.trace_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.trace_directory.cleanup)
        trace_path = patch.object(poc, "TRACE_DIRECTORY", Path(self.trace_directory.name))
        trace_path.start()
        self.addCleanup(trace_path.stop)
        # An accidental brokerage or internet request must fail even in integration tests.
        original = socket.socket.connect

        def local_only(sock, address):
            if not isinstance(address, tuple) or address[0] not in ("127.0.0.1", "::1"):
                raise AssertionError("Only loopback is permitted by this test suite")
            return original(sock, address)

        self.guard = patch("socket.socket.connect", local_only)
        self.guard.start()
        self.addCleanup(self.guard.stop)


class AuthenticationTests(OfflineCase):
    def browser_fixture(self):
        factory, manager, browser, context, page, response = (Mock() for _ in range(6))
        factory.return_value.start.return_value = manager
        manager.chromium.launch.return_value = browser
        browser.new_context.return_value = context
        context.new_page.return_value = page
        browser.is_connected.return_value = False
        page.url = poc.DESKTOP + "/"
        response.body.return_value = b'{"buyPowerT2":100000000}'
        response.headers = {"content-type": "application/json"}
        response.request.all_headers.return_value = {"Authorization": FAKE_TOKEN}
        context.cookies.return_value = []
        event = contextlib.nullcontext(Mock(value=response))
        context.expect_event.return_value = event
        return factory, manager, browser, context, page

    def test_handoff_finishes_all_teardown_before_native_reads(self):
        factory, manager, browser, context, page = self.browser_fixture()
        material = poc.authenticate_browser(factory=factory)
        context.close.assert_called_once()
        browser.close.assert_called_once()
        manager.stop.assert_called_once()
        page.evaluate.assert_not_called()
        material.cookies = auth().cookies
        with Server() as server, patch.object(page, "evaluate", side_effect=AssertionError("browser forbidden")), \
                patch.object(manager.chromium, "launch", side_effect=AssertionError("browser restart forbidden")):
            client = server.client(material=material)
            self.addCleanup(client.close)
            self.assertEqual(len(client.verify()), 1)
            client.read(poc.SYMBOLS, {"hash": "null"})

    def test_cleanup_on_login_failure_and_teardown_failure_prevent_handoff(self):
        for resource in ("login", "context", "browser", "manager", "still_connected"):
            with self.subTest(resource=resource):
                factory, manager, browser, context, page = self.browser_fixture()
                if resource == "login":
                    page.goto.side_effect = RuntimeError("fake-private-secret")
                elif resource == "still_connected":
                    browser.is_connected.return_value = True
                else:
                    {"context": context.close, "browser": browser.close, "manager": manager.stop}[resource].side_effect = RuntimeError("fake-private-secret")
                with self.assertRaises(poc.Blocked) as caught:
                    poc.authenticate_browser(factory=factory)
                self.assertNotIn("fake-private", str(caught.exception))
                context.close.assert_called_once()
                browser.close.assert_called_once()
                manager.stop.assert_called_once()

    def test_headers_cookie_scope_and_missing_state(self):
        material = auth()
        self.assertEqual(set(material.headers), {"authorization", "x-device-id"})
        self.assertNotIn(FAKE_TOKEN, repr(material))
        with self.assertRaisesRegex(poc.Blocked, "unavailable_session_state"):
            poc.capture_material({}, [], poc.DESKTOP)
        with self.assertRaises(poc.Blocked):
            poc.capture_material({"Authorization": "Bearer fake\r\nInjected: secret"}, [], poc.DESKTOP)
        material.teardown_complete = False
        with self.assertRaisesRegex(poc.Blocked, "invalid_native_handoff"):
            poc.NativeHttp(material)
        with Server() as server:
            material = auth()
            cookies = list(material.cookies)
            material.cookies.clear()
            for cookie in cookies:
                cookie.path = "/unrelated"
                material.cookies.set_cookie(cookie)
            client = server.client(material=material)
            self.addCleanup(client.close)
            with self.assertRaisesRegex(poc.Blocked, "authentication_rejected"):
                client.verify()

    @unittest.skipUnless(os.environ.get("POC_REAL_BROWSER") == "1", "Opt in to installed Chrome loopback test")
    def test_real_chrome_and_playwright_teardown_then_native_cookie_only_reads(self):
        from playwright.sync_api import sync_playwright
        captured = {}

        class TrackingFactory:
            def start(self):
                captured["manager"] = sync_playwright().start()
                launch = captured["manager"].chromium.launch

                def tracked_launch(**kwargs):
                    captured["browser"] = launch(**kwargs)
                    captured["browser"].on("disconnected", lambda _: captured.update(disconnected=True))
                    return captured["browser"]

                captured["manager"].chromium.launch = tracked_launch
                return captured["manager"]

        with Server() as server:
            server.require_token = False
            material = poc.authenticate_browser(origin=server.origin, api_origin=server.origin,
                                                factory=TrackingFactory, headless=True)
            self.assertTrue(material.teardown_complete)
            self.assertTrue(captured["disconnected"])
            self.assertFalse(captured["browser"].is_connected())
            with self.assertRaises(Exception):
                captured["manager"].chromium.launch(channel="chrome", headless=True)
            with patch.object(captured["manager"].chromium, "launch", side_effect=AssertionError("restart forbidden")):
                client = server.client(material=material)
                self.addCleanup(client.close)
                self.assertEqual(len(client.verify()), 1)
                self.assertEqual(client.read(poc.SYMBOLS, {"hash": "null"})["symbols"][0]["symbolIsin"], ISIN)
                report = poc.dispatch(lambda body, begin: client.submit(body, approved=True, on_initiated=begin), b"{}",
                                      poc.Window.from_inputs("0.1", 50), time.perf_counter_ns(), approved=True)
                self.assertEqual(len(server.received), 2)
                self.assertEqual(len(report.attempts), 2)
            print("BROWSER_EVIDENCE " + json.dumps(dict(browser_disconnected=True, playwright_stopped=True,
                                                       native_money_drafts_symbols_verified=True,
                                                       native_loopback_posts=2, real_orders=0)))


class HttpTests(OfflineCase):
    def test_only_evidenced_public_timing_reason_is_exposed(self):
        with Server() as server:
            client = server.client()
            self.addCleanup(client.close)
            client.verify()
            for data, expected in (({"isSuccessful": False, "message": "محدوده زمانی سفارش معتبر نمی‌باشد!"}, "market_entry_time"),
                                   ({"isSuccessful": False, "omsError": [{"error": "محدوده زمانی سفارش معتبر نمی باشد!"}]}, "market_entry_time"),
                                   ({"isSuccessful": False, "message": "fake-private-account-123456"}, "unspecified"),
                                   ({"isSuccessful": False}, "unspecified")):
                server.ack = data
                result = client.submit(b"{}", approved=True)
                self.assertEqual(result.acceptance, "rejected")
                self.assertEqual(result.rejection_reason, expected)
                self.assertNotIn("fake-private", repr(result))
            self.assertEqual(len(server.received), 4)

    def test_warmup_prepares_distinct_connections_without_any_http_request(self):
        client = poc.NativeHttp(auth(), api_origin="http://127.0.0.1:12345", loopback=True)
        self.addCleanup(client.close)
        client.verified = True
        connections = []

        def connection():
            conn = Mock(sock=None)
            conn.connect.side_effect = lambda: setattr(conn, "sock", Mock())
            connections.append(conn)
            return conn

        with patch.object(client, "_connection", side_effect=connection):
            client.warm_connections(3, time.perf_counter_ns() + 1_000_000_000)
        self.assertEqual(len(connections), 3)
        for conn in connections:
            conn.connect.assert_called_once()
            conn.request.assert_not_called()
        self.assertGreaterEqual(client.dispatch_capacity(poc.Window.from_inputs(3, 340)), 9)
        self.assertLessEqual(client.capacity, poc.MAX_CONCURRENCY)

    def test_warmup_failure_or_deadline_prevents_live_dispatch(self):
        for error, expected in ((ssl.SSLError("fake-private"), "tls_failure"),
                                (TimeoutError("fake-private"), "connection_warmup_timeout"),
                                (ConnectionRefusedError("fake-private"), "transport_failure")):
            with self.subTest(expected=expected):
                client = poc.NativeHttp(auth(), api_origin="http://127.0.0.1:12345", loopback=True)
                client.verified = True
                conn = Mock(sock=None)
                conn.connect.side_effect = error
                with patch.object(client, "_connection", return_value=conn):
                    with self.assertRaisesRegex(poc.Blocked, expected):
                        client.warm_connections(1, time.perf_counter_ns() + 1_000_000_000)
                self.assertFalse(client.verified)
                conn.request.assert_not_called()
                client.close()
        release = threading.Event()
        client = poc.NativeHttp(auth(), api_origin="http://127.0.0.1:12345", loopback=True)
        client.verified = True
        conn = Mock(sock=None)
        conn.connect.side_effect = lambda: release.wait(1)
        with patch.object(client, "_connection", return_value=conn):
            with self.assertRaisesRegex(poc.Blocked, "connection_warmup_timeout"):
                client.warm_connections(1, time.perf_counter_ns() + 20_000_000)
        self.assertFalse(client.verified)
        client.close()
        release.set()
        conn.request.assert_not_called()

    def test_required_headers_and_cookies_native_reads_and_full_preflight(self):
        with Server() as server:
            client = server.client()
            self.addCleanup(client.close)
            draft = client.verify()[0]
            fresh = poc.preflight(client, draft, 1000, 1000)
            self.assertEqual(fresh.order.total, 1000469)
            self.assertTrue(client.verified)
            self.assertEqual(server.received, [])
            client._auth.headers.clear()
            with self.assertRaisesRegex(poc.Blocked, "authentication_rejected"):
                client.read(poc.MONEY)
            self.assertFalse(client.verified)

    def test_auth_rejection_waf_malformed_and_http_categories_no_fallback(self):
        cases = [(401, None, "application/json", "authentication_rejected"),
                 (403, None, "application/json", "authentication_rejected"),
                 (429, None, "application/json", "broker_throttled"),
                 (503, None, "application/json", "http_error"),
                 (200, b"<title>WAF</title>fake-secret", "text/html", "non_json_response"),
                 (200, b"not-json-fake-secret", "application/json", "malformed_response"),
                 (200, {"unknown": 1}, "application/json", "invalid_number")]
        with Server() as server, patch.object(poc, "authenticate_browser", side_effect=AssertionError("no fallback")):
            for status, body, kind, expected in cases:
                with self.subTest(expected=expected):
                    server.money_status, server.money_body, server.money_kind = status, body, kind
                    client = server.client()
                    try:
                        with self.assertRaisesRegex(poc.Blocked, expected):
                            client.verify()
                        self.assertFalse(client.verified)
                        self.assertEqual(client.read_outcome, expected)
                        self.assertEqual(client.submit(b"{}", approved=True).category, "native_verification_required")
                    finally:
                        client.close()
            self.assertEqual(server.received, [])

    def test_tls_connection_timeout_distinguished_and_no_retry(self):
        with Server() as server:
            client = server.client()
            self.addCleanup(client.close)
            for exc, category in ((ssl.SSLError("fake-secret"), "tls_failure"),
                                  (ConnectionRefusedError("fake-secret"), "transport_failure"),
                                  (TimeoutError("fake-secret"), "transport_timeout")):
                conn = Mock()
                conn.request.side_effect = exc
                with patch.object(client, "_connection", return_value=conn):
                    with self.assertRaisesRegex(poc.Blocked, category):
                        client.verify()
                conn.request.assert_called_once()
                conn.close.assert_called_once()

    def test_expired_secure_and_other_domain_cookies_are_not_sent(self):
        for attr, value in (("expires", 1), ("secure", True), ("domain", "example.com")):
            with self.subTest(attr=attr), Server() as server:
                material = auth()
                cookie = next(iter(material.cookies))
                material.cookies.clear()
                setattr(cookie, attr, value)
                material.cookies.set_cookie(cookie)
                client = server.client(material=material)
                try:
                    with self.assertRaisesRegex(poc.Blocked, "authentication_rejected"):
                        client.verify()
                finally:
                    client.close()

    def test_redirects_and_ambiguous_json_are_never_accepted(self):
        with Server() as server:
            client = server.client()
            self.addCleanup(client.close)
            for raw in (b'{"buyPowerT2":1,"buyPowerT2":100000000}', b'{"buyPowerT2":NaN}'):
                server.money_body = raw
                with self.assertRaisesRegex(poc.Blocked, "malformed_response"):
                    client.verify()
            server.money_status = 302
            with self.assertRaisesRegex(poc.Blocked, "http_error"):
                client.verify()

    def test_default_submit_needs_separate_live_and_confirmation(self):
        with Server() as server:
            client = server.client(live_enabled=False)
            self.addCleanup(client.close)
            client.verify()
            self.assertEqual(client.submit(b"{}", approved=True).category, "explicit_live_authorization_required")
            client.live_enabled = True
            self.assertEqual(client.submit(b"{}").category, "explicit_live_authorization_required")
            self.assertEqual(server.received, [])
            with self.assertRaises(poc.Blocked):
                client.read(poc.ORDER)

    def test_observed_acknowledgement_does_not_claim_execution(self):
        with Server() as server:
            client = server.client()
            self.addCleanup(client.close)
            for ack, acceptance in (({"isSuccessful": True, "id": "fake-order"}, "accepted"),
                                    ({"isSuccessful": False, "message": "fake-private"}, "rejected"),
                                    ({"isSuccessful": True}, "unknown"), ({"unknown": True}, "unknown")):
                server.ack = ack
                client.verify()
                result = client.submit(b"{}", approved=True)
                self.assertEqual(result.acceptance, acceptance)
                self.assertNotIn("fake-private", repr(result))
            self.assertEqual(len(server.received), 4)

    def test_reused_connection_restores_timeout_budget_per_request(self):
        with Server() as server:
            server.delay = .12
            client = server.client(timeout=.2)
            self.addCleanup(client.close)
            client.verify()
            for _ in range(2):
                self.assertEqual(client.submit(b"{}", approved=True).acceptance, "accepted")
            self.assertEqual(len(server.received), 2)


class FinancialTests(OfflineCase):
    def build(self, draft=None, symbol=None, market=None, funds=100000000, quantity=1000, price=1000, origin=poc.DESKTOP):
        d, s, m, *_ = fixtures()
        return poc.build_buy(draft or d, symbol or s, market or m, funds, quantity, price, origin)

    def test_decimal_ceiling_payload_and_draft_immutability(self):
        draft, symbol, market, *_ = fixtures()
        before = copy.deepcopy(draft)
        order = self.build(draft=draft)
        self.assertEqual(order.total, 1000469)
        expected = {"order": {"price": 1000, "quantity": 1000, "side": 0, "validityType": 0,
                              "createDateTime": "11/8/2026, 8:45:00 AM", "commission": Decimal("0.00036875"),
                              "symbolIsin": ISIN, "symbolName": "TEST", "orderModelType": 1,
                              "totalValue": 1000469, "orderFrom": 34}}
        self.assertEqual(order.payload(AT), expected)
        encoded = poc.decimal_json(order.payload(AT))
        self.assertIn('"commission":0.00036875', encoded)
        self.assertNotIn("fake-draft", encoded)
        self.assertEqual(draft, before)
        self.assertEqual(self.build(origin=poc.MOBILE).order_from, 33)
        symbol["csize"] = "2.000000000000000001"
        self.assertEqual(self.build(symbol=symbol).total, 2000938)

    def test_financial_and_identity_safeguards(self):
        draft, symbol, market, *_ = fixtures()
        mutations = [("draft", "side", 1), ("draft", "side", False), ("draft", "validityType", 1),
                     ("draft", "symbolIsin", "incorrect"), ("symbol", "symbolIsin", "IRTEST000002"),
                     ("symbol", "isActive", False), ("symbol", "canBuy", None),
                     ("symbol", "marketUnit", 999), ("symbol", "buyCommission", None),
                     ("symbol", "buyCommission", "1"), ("symbol", "hidePrice", None),
                     ("symbol", "csize", "0"), ("symbol", "minDealablePrice", 3),
                     ("symbol", "minDealableCount", 3), ("symbol", "minValidBuyVolume", 2000),
                     ("market", "maxValidBuyVolume", 900), ("market", "lowAllowedPrice", 1001),
                     ("market", "highAllowedPrice", 999), ("market", "stateCode", "halted")]
        for which, key, value in mutations:
            with self.subTest(which=which, key=key):
                data = dict(draft=copy.deepcopy(draft), symbol=copy.deepcopy(symbol), market=copy.deepcopy(market))
                data[which][key] = value
                with self.assertRaises(poc.Blocked):
                    self.build(**data)
        for kwargs in (dict(quantity=5000, symbol={**symbol, "csize": 10}), dict(quantity=100), dict(funds=1000000), dict(price="NaN"),
                       dict(price=1000.0), dict(quantity=True), dict(origin="https://example.com")):
            with self.subTest(kwargs=kwargs), self.assertRaises(poc.Blocked):
                self.build(**kwargs)

    def test_preflight_has_no_broker_calendar_or_trading_hour_dependency(self):
        draft, symbol, market = fixtures()
        symbol.pop("tradingTimeType")
        values = {poc.SYMBOLS: {"symbols": [symbol]}, poc.MARKET: [market],
                  poc.MONEY: {"buyPowerT2": 100000000}}
        client = Mock(origin=poc.DESKTOP)
        client.read.side_effect = lambda path, *args: values[path]
        fresh = poc.preflight(client, draft, 1000, 1000)
        self.assertEqual(fresh.order.total, 1000469)
        self.assertEqual([c.args[0] for c in client.read.call_args_list], [poc.SYMBOLS, poc.MARKET, poc.MONEY])
        # User's chosen future start is valid even before ordinary market entry.
        early = AT.replace(hour=8, minute=44, second=58)
        self.assertGreater(poc.monotonic_target(early, now=early - timedelta(minutes=1), clock=lambda: 0), 0)

    def test_changed_stale_unconfirmed_preflight_cannot_dispatch(self):
        client = Mock(verified=True, live_enabled=True, origin=poc.DESKTOP)
        order = self.build()
        now = time.perf_counter_ns()
        window = poc.Window.from_inputs()
        fresh = poc.Preflight(order, now)
        with patch.object(poc, "dispatch", side_effect=AssertionError("must not dispatch")):
            for value, confirmed, start in ((fresh, False, now + 1000000),
                                            (replace(fresh, order=replace(order, quantity=2000)), True, now + 1000000),
                                            (replace(fresh, checked_ns=now - poc.MAX_PREFLIGHT_NS), True, now + 1000000),
                                            (fresh, True, now - 1)):
                with self.assertRaises(poc.Blocked):
                    poc.live_dispatch(client, order, value, window, start, confirmed=confirmed)


class SchedulingTests(OfflineCase):
    def test_late_scheduler_notification_does_not_add_another_delay(self):
        class NotificationClock(FakeClock):
            pending_delay = False

            def __call__(self):
                if threading.current_thread().name.startswith("native-order-"):
                    self.pending_delay = True
                elif self.pending_delay:
                    self.advance(.05)
                    self.pending_delay = False
                return super().__call__()

        clock = NotificationClock()
        report = poc.dispatch(simulated_submit(lambda _: poc.HttpResult("mock")), b"{}",
                              poc.Window.from_inputs(1, 340), 0, approved=True, clock=clock,
                              pause=clock.advance, cancel=FakeCancel(clock))
        self.assertEqual([a.initiated_ns for a in report.attempts], [0, 340_000_000, 680_000_000])

    def test_workers_are_prestarted_and_reused_across_attempts(self):
        clock = FakeClock()
        worker_objects = set()
        created = []
        original_start = threading.Thread.start

        def start(worker):
            if worker.name.startswith("native-order-"):
                created.append(worker)
            return original_start(worker)

        def call(_):
            self.assertEqual(len(created), 2)
            worker_objects.add(threading.current_thread())
            return poc.HttpResult("mock")

        with patch.object(threading.Thread, "start", start):
            report = poc.dispatch(simulated_submit(call), b"{}", poc.Window.from_inputs(1, 100), 0,
                                  approved=True, concurrency=2, clock=clock, pause=clock.advance,
                                  cancel=FakeCancel(clock))
        self.assertEqual(len(report.attempts), 10)
        self.assertTrue(all(a.result.category == "mock" for a in report.attempts))
        self.assertEqual(len(created), 2)
        self.assertLessEqual(len(worker_objects), 2)

    def test_live_spacing_cannot_be_configured_below_po_reported_minimum(self):
        order = poc.build_buy(*fixtures(), 100000000, 1000, 1000, poc.DESKTOP)
        fresh = poc.Preflight(order, time.perf_counter_ns())
        client = Mock(verified=True, live_enabled=True, origin=poc.DESKTOP)
        with patch.object(poc, "dispatch", side_effect=AssertionError("must not dispatch")):
            with self.assertRaisesRegex(poc.Blocked, "live_interval_below_300_ms"):
                poc.live_dispatch(client, order, fresh, poc.Window.from_inputs(1, 299),
                                  time.perf_counter_ns() + 1_000_000_000, confirmed=True)

    def test_ms_conversion_estimates_and_exclusive_end(self):
        for seconds, interval, count in ((3, 340, 9), (5, 350, 15), (2, 1000, 2), (1, 1000, 1)):
            with self.subTest(seconds=seconds, interval=interval):
                window = poc.Window.from_inputs(seconds, interval)
                self.assertEqual(window.interval_ns, interval * 1_000_000)
                self.assertEqual(window.attempts, count)
                clock = FakeClock()
                report = poc.dispatch(simulated_submit(lambda _: poc.HttpResult("mock")), b"{}", window, 0,
                                      approved=True, clock=clock, pause=clock.advance, cancel=FakeCancel(clock))
                stamps = [a.initiated_ns for a in report.attempts]
                self.assertEqual(len(stamps), count)
                self.assertTrue(all(t < window.duration_ns for t in stamps))
                self.assertTrue(all(b - a >= window.interval_ns for a, b in zip(stamps, stamps[1:])))
        for duration, gap in ((0, 350), (1, 0), (1, "0.5"), ("NaN", 350), ("0.0000000001", 350)):
            with self.assertRaises(poc.Blocked):
                poc.Window.from_inputs(duration, gap)

    def test_no_catch_up_burst_after_scheduler_delay(self):
        clock = FakeClock()
        seen = []

        def submit(_):
            seen.append(clock())
            if len(seen) == 1:
                clock.jump = 900_000_000
            return poc.HttpResult("mock")

        report = poc.dispatch(simulated_submit(submit), b"{}", poc.Window.from_inputs(2, 340), 0,
                              approved=True, clock=clock, pause=clock.advance, cancel=FakeCancel(clock))
        stamps = [a.initiated_ns for a in report.attempts]
        self.assertLess(len(stamps), 6)
        self.assertTrue(all(b - a >= 340_000_000 for a, b in zip(stamps, stamps[1:])))

    def test_monotonic_deadline_local_date_no_rollover(self):
        self.assertEqual(poc.monotonic_target(AT + timedelta(seconds=1), now=AT, clock=lambda: 123), 1000000123)
        for target in (AT, AT - timedelta(seconds=1), AT + timedelta(days=1), AT.replace(tzinfo=None)):
            with self.assertRaises(poc.Blocked):
                poc.monotonic_target(target, now=AT)

    def test_cancel_no_confirmation_and_unknown_outcome_not_retried(self):
        submit = Mock(side_effect=RuntimeError("Authorization: fake-private-secret"))
        window = poc.Window.from_inputs(1, 1000)
        with self.assertRaises(poc.Blocked):
            poc.dispatch(submit, b"fake-private-payload", window, 0)
        clock = FakeClock()
        report = poc.dispatch(simulated_submit(submit), b"fake-private-payload", window, 0, approved=True,
                              clock=clock, pause=clock.advance, cancel=FakeCancel(clock))
        submit.assert_called_once()
        diagnostic = json.dumps(report.diagnostics())
        self.assertNotIn("fake-private", diagnostic)
        self.assertEqual(report.attempts[0].result.acceptance, "unknown")
        cancel = threading.Event()
        cancel.set()
        report = poc.dispatch(submit, b"{}", window, time.perf_counter_ns(), approved=True, cancel=cancel)
        self.assertEqual(len(report.attempts), 0)

    def test_bounded_concurrency_cutoff_outstanding_and_no_blind_abort(self):
        release = threading.Event()

        def slow(_):
            release.wait(2)
            return poc.HttpResult("mock", 200, "accepted")

        start = time.perf_counter_ns()
        report = poc.dispatch(simulated_submit(slow), b"{}", poc.Window.from_inputs("0.2", 30), start,
                              approved=True, concurrency=2, drain_seconds=.01)
        self.assertLess((time.perf_counter_ns() - start) / 1e9, .6)
        self.assertEqual(len(report.attempts), 2)
        self.assertGreater(report.capacity_skips, 0)
        self.assertTrue(all(a.result is None for a in report.attempts))
        self.assertIn("outstanding_unknown", json.dumps(report.diagnostics()))
        release.set()
        deadline = time.perf_counter() + 1
        while any(a.result is None for a in report.attempts) and time.perf_counter() < deadline:
            time.sleep(.005)
        self.assertTrue(all(a.result.acceptance == "accepted" for a in report.attempts))

    def test_cutoff_rechecked_at_native_handoff_not_worker_creation(self):
        clock = FakeClock()

        def delayed_setup(_, begin):
            clock.advance(2)
            self.assertFalse(begin())
            return poc.HttpResult("initiation_cancelled_or_cutoff")

        report = poc.dispatch(delayed_setup, b"{}", poc.Window.from_inputs(1, 340), 0,
                              approved=True, clock=clock, pause=clock.advance, cancel=FakeCancel(clock))
        self.assertEqual(report.scheduled_attempts, 1)
        self.assertEqual(report.attempts, [])
        self.assertEqual(report.non_initiated, ["initiation_cancelled_or_cutoff"])

    def test_failed_verification_is_not_counted_as_an_http_initiation(self):
        clock = FakeClock()
        report = poc.dispatch(lambda body, begin: poc.HttpResult("native_verification_required"), b"{}",
                              poc.Window.from_inputs(1, 340), 0, approved=True,
                              clock=clock, pause=clock.advance, cancel=FakeCancel(clock))
        self.assertEqual(report.scheduled_attempts, 1)
        self.assertEqual(report.attempts, [])
        self.assertEqual(report.non_initiated, ["native_verification_required"])


class IntegrationTests(OfflineCase):
    def test_blocking_request_send_call_does_not_serialize_next_post_call(self):
        with Server() as server:
            client = server.client()
            self.addCleanup(client.close)
            client.verify()
            client.warm_connections(3, time.perf_counter_ns() + 1_000_000_000)
            calls, returns = [], []
            original_request = poc.http.client.HTTPConnection.request

            def blocked_send(conn, method, path, **kwargs):
                if path == poc.ORDER:
                    calls.append(time.perf_counter_ns())
                    time.sleep(.8)  # Hold the HTTP send call, not response handling.
                result = original_request(conn, method, path, **kwargs)
                if path == poc.ORDER:
                    returns.append(time.perf_counter_ns())
                return result

            with patch.object(poc.http.client.HTTPConnection, "request", blocked_send):
                report = poc.dispatch(lambda body, begin: client.submit(body, approved=True, on_initiated=begin),
                                      b"{}", poc.Window.from_inputs(1, 340), time.perf_counter_ns() + 50_000_000,
                                      approved=True, concurrency=3)
            self.assertEqual(len(calls), 3)
            self.assertEqual(len(server.received), 3)
            self.assertLess(calls[-1], returns[0])
            self.assertTrue(all(b - a >= 340_000_000 for a, b in zip(
                [a.initiated_ns for a in report.attempts], [a.initiated_ns for a in report.attempts][1:])))
            self.assertTrue(all(a.result.acceptance == "accepted" for a in report.attempts))
            print("SEND_PHASE_EVIDENCE " + json.dumps(dict(received=3, request_calls_ns=calls,
                  request_returns_ns=returns, all_calls_before_first_return=calls[-1] < returns[0])))

    def test_two_second_responses_keep_all_nine_paced_calls_with_warmed_connections(self):
        with Server() as server:
            server.delay = 2
            client = server.client()
            self.addCleanup(client.close)
            client.verify()
            window = poc.Window.from_inputs(3, 340)
            capacity = client.dispatch_capacity(window)
            client.warm_connections(capacity, time.perf_counter_ns() + 1_000_000_000)
            order = poc.build_buy(*fixtures(), 100000000, 1000, 1000, poc.DESKTOP)
            fresh = poc.Preflight(order, time.perf_counter_ns())
            with patch.object(client, "_connection", side_effect=AssertionError("cold connection in dispatch")), \
                    patch.object(poc.http.client.HTTPConnection, "connect", side_effect=AssertionError("cold TCP setup")):
                report = poc.live_dispatch(client, order, fresh, window, time.perf_counter_ns() + 50_000_000,
                                           confirmed=True)
            stamps = [a.initiated_ns for a in report.attempts]
            gaps = [(b - a) / 1e6 for a, b in zip(stamps, stamps[1:])]
            self.assertEqual(len(server.received), 9)
            self.assertEqual(len(stamps), 9)
            self.assertEqual(report.capacity_skips, 0)
            self.assertGreaterEqual(min(gaps), 340)
            self.assertGreaterEqual(server.max_active, 6)
            self.assertTrue(all(a.result.acceptance == "accepted" for a in report.attempts))
            print("SLOW_RESPONSE_EVIDENCE " + json.dumps(dict(received=9, worker_capacity=capacity,
                  capacity_skips=report.capacity_skips, client_gap_ms=gaps, max_concurrent=server.max_active,
                  client_monotonic_ns=stamps, server_monotonic_ns=[s for s, _ in server.received])))

    def test_cancel_drains_transmitted_request_and_dropped_ack_never_replays(self):
        with Server() as server:
            server.delay = .2
            cancel = threading.Event()
            server.cancel_on_receive = cancel
            client = server.client()
            self.addCleanup(client.close)
            client.verify()
            report = poc.dispatch(lambda body, begin: client.submit(body, approved=True, on_initiated=begin),
                                  b"{}", poc.Window.from_inputs(1, 100), time.perf_counter_ns(),
                                  approved=True, cancel=cancel)
            self.assertEqual(len(server.received), 1)
            self.assertEqual(len(report.attempts), 1)
            self.assertEqual(report.attempts[0].result.acceptance, "accepted")
            server.cancel_on_receive = None
            server.drop_order_response = True
            outcome = client.submit(b"{}", approved=True)
            self.assertEqual(outcome.category, "transport_failure")
            self.assertEqual(outcome.acceptance, "unknown")
            self.assertEqual(len(server.received), 2)

    def test_three_seconds_340ms_real_received_count_and_timestamps(self):
        with Server() as server, patch.object(poc, "authenticate_browser", side_effect=AssertionError("no browser")):
            server.delay = .6  # Longer than interval: responses must overlap.
            client = server.client()
            self.addCleanup(client.close)
            client.verify()
            start = time.perf_counter_ns() + 50_000_000
            report = poc.dispatch(lambda body, begin: client.submit(body, approved=True, on_initiated=begin), b'{"fake":"offline-only"}',
                                  poc.Window.from_inputs(3, 340), start, approved=True)
            arrivals = [stamp for stamp, _ in server.received]
            initiations = [a.initiated_ns for a in report.attempts]
            self.assertEqual(len(arrivals), 9)
            self.assertEqual(len(initiations), 9)
            self.assertTrue(all(start <= t < start + 3_000_000_000 for t in initiations))
            gaps = [(b - a) / 1e6 for a, b in zip(initiations, initiations[1:])]
            server_gaps = [(b - a) / 1e6 for a, b in zip(arrivals, arrivals[1:])]
            self.assertGreaterEqual(min(gaps), 340)
            self.assertGreaterEqual(server.max_active, 2)
            self.assertTrue(all(a.result.acceptance == "accepted" for a in report.attempts))
            self.assertEqual(report.diagnostics()["attempts"][-1]["execution"], "unknown")
            completions = [a.result.completed_ns for a in report.attempts]
            self.assertGreater(completions[-1], start + 3_000_000_000)
            print("HTTP_EVIDENCE " + json.dumps(dict(received=len(arrivals), initiated=len(initiations),
                  client_monotonic_ns=initiations, server_monotonic_ns=arrivals,
                  client_gap_ms=gaps, server_gap_ms=server_gaps, max_concurrent=server.max_active,
                  client_completion_ns=completions, cutoff_ns=start + 3_000_000_000,
                  completed_after_cutoff=completions[-1] > start + 3_000_000_000, mock_acceptances_only=True)))

    def test_real_timeout_failed_connection_cancellation_and_throttling_never_replay(self):
        with Server() as server:
            server.delay = .2
            client = server.client(timeout=.05)
            self.addCleanup(client.close)
            client.verify()
            outcome = client.submit(b"{}", approved=True)
            self.assertEqual(outcome.category, "transport_timeout")
            self.assertEqual(len(server.received), 1)
            server.delay = 0
            server.order_status = 429
            client.verify()
            report = poc.dispatch(lambda body, begin: client.submit(body, approved=True, on_initiated=begin), b"{}",
                                  poc.Window.from_inputs("0.5", 100), time.perf_counter_ns(), approved=True)
            self.assertEqual(len(report.attempts), 1)
            self.assertEqual(report.attempts[0].result.category, "broker_throttled")
            self.assertEqual(len(server.received), 2)
        # The chosen ephemeral listener is now closed; one initiation, no replay.
        closed = poc.NativeHttp(auth(), api_origin=server.origin, loopback=True, timeout=3, live_enabled=True)
        self.addCleanup(closed.close)
        closed.verified = True
        self.assertEqual(closed.submit(b"{}", approved=True).category, "transport_failure")
        cancel = threading.Event()

        def cancel_on_first(_):
            cancel.set()
            return poc.HttpResult("mock")

        report = poc.dispatch(simulated_submit(cancel_on_first), b"{}", poc.Window.from_inputs(1, 100),
                              time.perf_counter_ns(), approved=True, cancel=cancel)
        self.assertEqual(len(report.attempts), 1)


class CommandTests(OfflineCase):
    def test_header_documents_exact_real_run_and_optional_diagnostics(self):
        self.assertIn("python POC/easytrader_direct_http_poc.py --authenticate --live\n", poc.__doc__)
        self.assertIn("--authenticate --live --diagnostics", poc.__doc__)
        self.assertIn("No test server or simulated", poc.__doc__)

    def test_diagnostics_is_opt_in_and_never_contains_auth_material(self):
        for args in ([], ["--diagnostics"]):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(poc.main(args), 0)
            json_lines = [line for line in out.getvalue().splitlines() if line.startswith("{")]
            self.assertEqual(len(json_lines), int(bool(args)))
            self.assertNotIn(FAKE_TOKEN, out.getvalue())
            self.assertNotIn(FAKE_COOKIE, out.getvalue())
            if json_lines:
                self.assertEqual(json.loads(json_lines[0])["order_requests"], 0)

    def test_real_command_path_reports_broker_rejections_without_technical_json_by_default(self):
        for debug in (False, True):
            with self.subTest(diagnostics=debug), Server() as server:
                server.ack = {"isSuccessful": False, "message": "محدوده زمانی سفارش معتبر نمی‌باشد!",
                              "private": "fake-private-account"}
                client = server.client()
                with patch.object(poc, "authenticate_browser", return_value=auth()), \
                        patch.object(poc, "NativeHttp", return_value=client), \
                        patch.object(poc, "local_target", return_value=AT), \
                        patch.object(poc, "monotonic_target", side_effect=lambda _: time.perf_counter_ns() + 500_000_000), \
                        patch.object(poc, "confirm_order", return_value=True), \
                        patch("builtins.input", side_effect=["1", "", "", "0.5", "340"]), \
                        contextlib.redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(poc.main(["--authenticate", "--live"] + (["--diagnostics"] if debug else [])), 0)
                self.assertEqual(len(server.received), 2)
                text = out.getvalue()
                self.assertIn("Starts in", text)
                self.assertIn("Requests initiated: 2 / planned 2", text)
                self.assertIn("accepted 0 | rejected 2 | unknown 0", text)
                self.assertIn("order time window is invalid", text)
                self.assertNotIn("fake-private", text)
                json_lines = [line for line in text.splitlines() if line.startswith("{")]
                self.assertEqual(len(json_lines), int(debug))
                if debug:
                    details = json.loads(json_lines[0])
                    self.assertEqual(details["local_initiations"], 2)
                    self.assertTrue(all(a["rejection_reason"] == "market_entry_time" for a in details["attempts"]))

    def test_early_start_warns_once_before_countdown_and_native_posts(self):
        with Server() as server:
            client = server.client()
            output = io.StringIO()
            original_wait = poc.wait_until

            def wait_after_warning(*args, **kwargs):
                self.assertEqual(output.getvalue().count("WARNING: " + poc.MARKET_TIME_WARNING), 1)
                return original_wait(*args, **kwargs)

            with patch.object(poc, "authenticate_browser", return_value=auth()), \
                    patch.object(poc, "NativeHttp", return_value=client), \
                    patch.object(poc, "local_target", return_value=AT.replace(hour=8, minute=44, second=58)), \
                    patch.object(poc, "monotonic_target", side_effect=lambda _: time.perf_counter_ns() + 500_000_000), \
                    patch.object(poc, "confirm_order", return_value=True), \
                    patch.object(poc, "wait_until", side_effect=wait_after_warning), \
                    patch("builtins.input", side_effect=["1", "", "", "0.5", "340"]), \
                    contextlib.redirect_stdout(output):
                self.assertEqual(poc.main(["--authenticate", "--live"]), 0)
            self.assertEqual(len(server.received), 2)
            self.assertIn("planned independent requests=2", output.getvalue())
            self.assertIn("potential aggregate exposure=2000938 IRR", output.getvalue())
            self.assertIn("Starts in", output.getvalue())
            self.assertIn("accepted 2 | rejected 0 | unknown 0", output.getvalue())
            self.assertNotIn('"attempts":', output.getvalue())

    def test_full_readonly_preflight_has_no_order_posts(self):
        with Server() as server:
            client = server.client(live_enabled=False)
            with patch.object(poc, "authenticate_browser", return_value=auth()), \
                    patch.object(poc, "NativeHttp", return_value=client), \
                    patch.object(poc, "local_target", return_value=AT.replace(hour=17)), \
                    patch.object(poc, "confirm_order", side_effect=AssertionError("no live confirmation")), \
                    patch("builtins.input", side_effect=["1", "", "", "3", "340"]), \
                    contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(poc.main(["--authenticate", "--preflight"]), 0)
            self.assertEqual(server.received, [])
            self.assertEqual(out.getvalue().count("WARNING: " + poc.MARKET_TIME_WARNING), 1)
            self.assertIn("No order POSTs were sent", out.getvalue())
            self.assertNotIn('"order_requests":', out.getvalue())

    def test_default_and_live_without_auth_have_zero_network(self):
        with patch.object(poc, "authenticate_browser", side_effect=AssertionError("no authentication")), \
                patch.object(poc.NativeHttp, "_exchange", side_effect=AssertionError("no network")):
            for args, status in (([], 0), (["--live"], 2)):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    self.assertEqual(poc.main(args), status)
                self.assertNotIn(FAKE_TOKEN, out.getvalue())
                self.assertNotIn(FAKE_COOKIE, out.getvalue())

    def test_readonly_failure_is_explicit_and_never_enables_dispatch(self):
        client = Mock()
        client.verify.side_effect = poc.Blocked("authentication_rejected")
        client.read_outcome = "authentication_rejected"
        with patch.object(poc, "authenticate_browser", return_value=auth()), \
                patch.object(poc, "NativeHttp", return_value=client), \
                patch.object(poc, "live_dispatch", side_effect=AssertionError("dispatch forbidden")), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(poc.main(["--authenticate", "--live"]), 2)
        client.close.assert_called_once()
        self.assertIn("authentication rejected", out.getvalue())


class TraceTests(OfflineCase):
    def new_trace(self, **kwargs):
        trace = poc.RunTrace(poc.secrets.token_hex(8), **kwargs)
        self.addCleanup(trace.close)
        return trace

    def events(self, trace):
        trace.close()
        raw = trace.path.read_text(encoding="utf-8")
        self.assertTrue(raw.endswith("\n"))
        events = [json.loads(line) for line in raw.splitlines()]
        self.assertEqual([e["sequence"] for e in events], list(range(1, len(events) + 1)))
        self.assertTrue(all(e["run_id"] == trace.run_id for e in events))
        for event in events:
            self.assertIsNotNone(datetime.fromisoformat(event["local_timestamp"]).tzinfo)
        return events

    def fake_dispatch(self, trace, submit, **kwargs):
        clock = FakeClock()
        return poc.dispatch(submit, b"fake-private-payload", poc.Window.from_inputs(1, 350), 0,
                            approved=True, clock=clock, pause=clock.advance, cancel=FakeCancel(clock),
                            trace=trace, **kwargs)

    def test_live_flag_alone_creates_trace_before_authorization_failure(self):
        with patch.object(poc, "authenticate_browser") as login, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(poc.main(["--live"]), 2)
        login.assert_not_called()
        paths = list(Path(self.trace_directory.name).glob("*.jsonl"))
        self.assertEqual(len(paths), 1)
        events = [json.loads(line) for line in paths[0].read_text(encoding="utf-8").splitlines()]
        self.assertEqual([e["event"] for e in events], ["run_started", "run_aborted"])

    def test_non_live_commands_do_not_create_trace(self):
        with patch.object(poc, "RunTrace") as sink, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(poc.main([]), 0)
            self.assertEqual(poc.main(["--diagnostics"]), 0)
        sink.assert_not_called()
        self.assertEqual(list(Path(self.trace_directory.name).iterdir()), [])

    def test_unique_run_ids_filenames_and_exclusive_collision_handling(self):
        first = self.new_trace()
        first.close()
        original = first.path.read_bytes()
        second = self.new_trace()
        collision = poc.RunTrace(first.run_id)
        self.addCleanup(collision.close)
        self.assertNotEqual(first.run_id, second.run_id)
        self.assertEqual(len({first.path, second.path, collision.path}), 3)
        self.assertEqual(first.path.read_bytes(), original)
        self.assertRegex(first.path.name, r"^opening_order_\d{8}_\d{6}_" + first.run_id + r"\.jsonl$")
        self.events(second)
        self.events(collision)

    def test_full_live_lifecycle_uses_existing_run_id_without_diagnostics(self):
        with Server() as server:
            client = server.client()
            with patch.object(poc, "authenticate_browser", return_value=auth()), \
                    patch.object(poc, "NativeHttp", return_value=client), \
                    patch.object(poc, "local_target", return_value=AT), \
                    patch.object(poc, "monotonic_target", side_effect=lambda _: time.perf_counter_ns() + 500_000_000), \
                    patch.object(poc, "confirm_order", return_value=True), \
                    patch.object(poc.secrets, "token_hex", return_value="0123456789abcdef"), \
                    patch("builtins.input", side_effect=["1", "", "", "0.5", "340"]), \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(poc.main(["--authenticate", "--live"]), 0)
            self.assertEqual(len(server.received), 2)
        path, = Path(self.trace_directory.name).glob("*.jsonl")
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        names = [e["event"] for e in events]
        lifecycle = ["run_started", "authentication_started", "authentication_completed",
                     "native_verification_completed", "window_configured", "preflight_completed", "user_confirmation",
                     "connection_warmup_started", "connection_warmup_completed", "final_preflight_started",
                     "final_preflight_completed", "connection_refresh_started", "connection_refresh_completed",
                     "dispatch_started", "dispatch_window_ended", "drain_started", "drain_completed",
                     "dispatch_report_snapshot", "run_completed"]
        self.assertEqual([n for n in names if n in lifecycle], lifecycle)
        self.assertTrue(all(e["run_id"] == "0123456789abcdef" for e in events))
        self.assertFalse(any(line.startswith("{") for line in output.getvalue().splitlines()))
        self.assertEqual(sum(n == "attempt_initiated" for n in names), 2)
        self.assertEqual(sum(n == "attempt_result_completed" for n in names), 2)

    def test_preflight_after_prompt_uses_fresh_socket_and_reports_failed_read(self):
        for disconnect in (False, True):
            with self.subTest(disconnect=disconnect), Server() as server:
                client = server.client()
                handler = server.httpd.RequestHandlerClass
                original_request = poc.http.client.HTTPConnection.request
                original_handle = handler.handle_api
                reads = {}

                def request(connection, method, path, *args, **kwargs):
                    reads[path] = connection
                    if path == poc.SYMBOLS and connection is reads[poc.DRAFTS]:
                        raise poc.http.client.RemoteDisconnected("fake-idle-socket")
                    return original_request(connection, method, path, *args, **kwargs)

                def handle(connection):
                    if disconnect and connection.path == poc.SYMBOLS:
                        connection.close_connection = True
                        connection.connection.shutdown(socket.SHUT_RDWR)
                        return
                    original_handle(connection)

                with patch.object(handler, "handle_api", new=handle), \
                        patch.object(poc.http.client.HTTPConnection, "request", new=request), \
                        patch.object(poc, "authenticate_browser", return_value=auth()), \
                        patch.object(poc, "NativeHttp", return_value=client), \
                        patch.object(poc, "local_target", return_value=AT), \
                        patch.object(poc, "confirm_order", return_value=False), \
                        patch("builtins.input", side_effect=["1", "", "", "1", "1000"]), \
                        contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(poc.main(["--authenticate", "--live", "--diagnostics"]), 2 if disconnect else 0)

                self.assertIsNot(reads[poc.DRAFTS], reads[poc.SYMBOLS])
                self.assertEqual(server.received, [])
                details = json.loads(next(line for line in output.getvalue().splitlines() if line.startswith("{")))
                path, = Path(self.trace_directory.name).glob(f"*_{details['run_id']}*.jsonl")
                events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
                self.assertFalse(any(e["event"] == "dispatch_started" for e in events))
                if disconnect:
                    failure = next(e for e in events if e["event"] == "preflight_failed")
                    self.assertEqual(details["stop"], "transport_failure")
                    for record in (failure, details):
                        self.assertEqual(record["preflight_phase"], "initial")
                        self.assertEqual(record["read_operation"], "symbols")
                        self.assertEqual(record["exchange_phase"], "headers")
                else:
                    self.assertEqual(details["stop"], "confirmation_cancelled")

    def test_final_preflight_closed_connection_is_replaced_before_dispatch(self):
        for refresh_fails in (False, True):
            with self.subTest(refresh_fails=refresh_fails), Server() as server:
                client = server.client()
                handler = server.httpd.RequestHandlerClass
                original_send = handler.send
                original_connect = poc.http.client.HTTPConnection.connect
                money_reads = 0
                closed = threading.Event()
                connections_after_close = []

                def send(connection, status, body, kind="application/json", extra=None):
                    nonlocal money_reads
                    if connection.path == poc.MONEY:
                        money_reads += 1
                        if money_reads == 3:
                            extra = {**(extra or {}), "Connection": "close"}
                            connection.close_connection = True
                            closed.set()
                    return original_send(connection, status, body, kind, extra)

                def connect(connection):
                    if closed.is_set():
                        connections_after_close.append(threading.current_thread().name)
                        if refresh_fails:
                            raise OSError("fake-offline-refresh-failure")
                    return original_connect(connection)

                with patch.object(handler, "send", new=send), \
                        patch.object(poc.http.client.HTTPConnection, "connect", new=connect), \
                        patch.object(poc, "authenticate_browser", return_value=auth()), \
                        patch.object(poc, "NativeHttp", return_value=client), \
                        patch.object(poc, "local_target", return_value=AT), \
                        patch.object(poc, "monotonic_target", side_effect=lambda _: time.perf_counter_ns() + 900_000_000), \
                        patch.object(poc, "confirm_order", return_value=True), \
                        patch("builtins.input", side_effect=["1", "", "", "1", "1000"]), \
                        contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(poc.main(["--authenticate", "--live", "--diagnostics"]), 2 if refresh_fails else 0)
                self.assertTrue(closed.is_set())
                self.assertEqual(connections_after_close, ["native-connect"])
                self.assertEqual(len(server.received), 0 if refresh_fails else 1)
                details = json.loads(next(line for line in output.getvalue().splitlines() if line.startswith("{")))
                path, = Path(self.trace_directory.name).glob(f"*_{details['run_id']}*.jsonl")
                events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
                names = [e["event"] for e in events]
                if refresh_fails:
                    self.assertEqual(details["stop"], "transport_failure")
                    self.assertNotIn("dispatch_started", names)
                    self.assertNotIn("attempt_initiated", names)
                else:
                    self.assertLess(names.index("connection_refresh_completed"), names.index("dispatch_started"))
                    ready = next(e for e in events if e["event"] == "connection_ready")
                    self.assertTrue(ready["reused_connection"])

    def test_four_second_window_stops_waiting_at_cutoff_after_twelve_attempts(self):
        clock = FakeClock()
        trace = self.new_trace()
        window = poc.Window.from_inputs(4, 350)
        start = 100_000_000
        cutoff = start + window.duration_ns
        report = poc.dispatch(simulated_submit(lambda _: poc.HttpResult("broker_response", 200, "accepted")),
                              b"{}", window, start, approved=True, concurrency=12, clock=clock,
                              pause=clock.advance, cancel=FakeCancel(clock), trace=trace)

        self.assertEqual(report.stop, "cutoff")
        self.assertEqual(report.scheduled_attempts, 12)
        self.assertEqual(report.capacity_skips, 0)
        self.assertEqual([attempt.initiated_ns for attempt in report.attempts],
                         [start + index * window.interval_ns for index in range(12)])
        self.assertEqual(report.diagnostics()["snapshot_monotonic_ns"], cutoff)

    def test_four_second_window_reports_mixed_transport_outcomes_by_slot(self):
        trace = self.new_trace()
        with Server() as server:
            server.order_responses = [
                (200, {"isSuccessful": False, "message": "محدوده زمانی سفارش معتبر نمی‌باشد!"}, .6, False),
                (200, {"isSuccessful": True, "id": "fake-offline-broker-id"}, .6, False),
                (200, {}, 0, True),
                (400, {"private": "fake-offline-response-body"}, 0, False),
            ]
            client = server.client()
            self.addCleanup(client.close)
            draft = client.verify()[0]
            window = poc.Window.from_inputs(4, 350)
            order = poc.preflight(client, draft, 1000, 1000).order
            client.warm_connections(client.dispatch_capacity(window), time.perf_counter_ns() + 2_000_000_000)
            fresh = poc.preflight(client, draft, 1000, 1000)
            start = time.perf_counter_ns() + 150_000_000
            client.warm_connections(client.dispatch_capacity(window), start)
            report = poc.live_dispatch(client, order, fresh, window, start, confirmed=True, trace=trace)
            self.assertEqual(len(server.received), 12)
            self.assertGreaterEqual(server.max_active, 2)
        details = report.diagnostics()
        rows = details["rows"]
        self.assertEqual([row["state"] for row in rows[:4]], ["rejected", "accepted", "unknown", "unknown"])
        self.assertEqual(rows[0]["rejection_reason"], "market_entry_time")
        self.assertEqual(rows[2]["transport"], "transport_failure")
        self.assertEqual(rows[3]["http_status"], 400)
        events = self.events(trace)
        first = [e["event"] for e in events if e.get("scheduled_attempt") == 1]
        self.assertEqual(first, ["attempt_assigned", "connection_ready", "attempt_initiated",
                                 "http_request_returned", "http_headers_received", "attempt_result_completed"])
        failed = next(e for e in events if e["event"] == "http_exchange_failed")
        self.assertEqual((failed["scheduled_attempt"], failed["exchange_phase"]), (3, "headers"))
        snapshot = next(e for e in events if e["event"] == "dispatch_report_snapshot")
        self.assertEqual(snapshot["initiated_attempts"], details["local_initiations"])
        self.assertEqual(snapshot["completed_unknown_outcomes"], details["completed_unknown_outcomes"])
        self.assertEqual(snapshot["pending_attempts"], details["pending_attempts"])
        with contextlib.redirect_stdout(io.StringIO()) as output:
            poc.print_live_summary(report)
        self.assertIn("accepted 9 | rejected 1 | unknown 2", output.getvalue())
        self.assertIn("Pending after drain: 0", output.getvalue())
        raw = trace.path.read_text(encoding="utf-8")
        self.assertNotIn("fake-offline-broker-id", raw)
        self.assertNotIn("fake-offline-response-body", raw)

    def test_attempt_correlation_timestamps_gaps_and_snapshot_counts(self):
        trace = self.new_trace()
        outcomes = iter([poc.HttpResult("broker_response", 200, "accepted"),
                         poc.HttpResult("broker_response", 200, "rejected", rejection_reason="market_entry_time"),
                         poc.HttpResult("transport_timeout", 504)])
        report = self.fake_dispatch(trace, simulated_submit(lambda _: next(outcomes)))
        events = self.events(trace)
        starts = [e for e in events if e["event"] == "attempt_initiated"]
        results = [e for e in events if e["event"] == "attempt_result_completed"]
        self.assertEqual([e["attempt_number"] for e in starts], [1, 2, 3])
        self.assertEqual([e["attempt_number"] for e in results], [1, 2, 3])
        self.assertEqual([e["initiation_monotonic_ns"] for e in starts], [a.initiated_ns for a in report.attempts])
        self.assertEqual([e["scheduled_monotonic_ns"] for e in starts], [0, 350_000_000, 700_000_000])
        self.assertEqual([e["gap_ns"] for e in starts], [None, 350_000_000, 350_000_000])
        self.assertEqual([e["http_status"] for e in results], [200, 200, 504])
        self.assertEqual([e["broker_acceptance"] for e in results], ["accepted", "rejected", "unknown"])
        self.assertEqual(results[1]["rejection_category"], "market_entry_time")
        self.assertEqual(results[2]["transport"], "transport_timeout")
        self.assertTrue(all(e["elapsed_ns"] == e["completion_monotonic_ns"] - starts[i]["initiation_monotonic_ns"]
                            for i, e in enumerate(results)))
        snapshot = next(e for e in events if e["event"] == "dispatch_report_snapshot")
        self.assertEqual(snapshot["planned_attempts"], report.planned)
        self.assertEqual(snapshot["scheduled_attempts"], report.scheduled_attempts)
        self.assertEqual(snapshot["initiated_attempts"], len(report.attempts))
        self.assertEqual(snapshot["capacity_skips"], report.capacity_skips)
        self.assertEqual(snapshot["worker_capacity"], report.worker_capacity)
        self.assertEqual(snapshot["http_responses_observed"], 3)
        self.assertEqual(snapshot["completed_broker_acknowledgements"], 2)
        self.assertEqual(snapshot["completed_unknown_outcomes"], 1)
        self.assertEqual(snapshot["pending_attempts"], 0)
        self.assertEqual(snapshot["workers_still_running"], 0)

    def test_http_result_completion_timestamp_is_preserved(self):
        trace = self.new_trace()
        clock = FakeClock()
        result = poc.HttpResult("malformed_acknowledgement", 200, completed_ns=123)
        poc.dispatch(simulated_submit(lambda _: result), b"{}", poc.Window.from_inputs(1, 1000), 0,
                     approved=True, trace=trace, clock=clock, pause=clock.advance, cancel=FakeCancel(clock))
        event = next(e for e in self.events(trace) if e["event"] == "attempt_result_completed")
        self.assertEqual(event["completion_monotonic_ns"], 123)
        self.assertEqual(event["elapsed_ns"], 123)
        self.assertEqual(event["broker_acceptance"], "unknown")

    def test_completed_unknown_and_pending_alive_worker_are_distinct_without_extra_drain(self):
        trace = self.new_trace()
        release = threading.Event()
        finished = threading.Event()
        calls = 0

        def submit(_, begin):
            nonlocal calls
            self.assertTrue(begin())
            calls += 1
            if calls == 1:
                return poc.HttpResult("transport_timeout", completed_ns=time.perf_counter_ns())
            release.wait(2)
            finished.set()
            return poc.HttpResult("broker_response", 200, "accepted", time.perf_counter_ns())

        try:
            start = time.perf_counter_ns()
            report = poc.dispatch(submit, b"{}", poc.Window.from_inputs("0.12", 40), start,
                                  approved=True, concurrency=1, drain_seconds=.01, trace=trace)
            self.assertLess((time.perf_counter_ns() - start) / 1e9, .6)
            self.assertEqual(len(report.attempts), 2)
            events = self.events(trace)
            completed = [e for e in events if e["event"] == "attempt_result_completed"]
            pending = [e for e in events if e["event"] == "attempt_pending_at_snapshot"]
            self.assertEqual(len(completed), 1)
            self.assertEqual(completed[0]["transport"], "transport_timeout")
            self.assertEqual(completed[0]["broker_acceptance"], "unknown")
            self.assertEqual(pending[0]["attempt_number"], 2)
            self.assertTrue(pending[0]["pending_at_snapshot"])
            self.assertTrue(pending[0]["worker_alive"])
            self.assertFalse(pending[0]["completed_result_available"])
            self.assertEqual(pending[0]["completion_observation"], "until_trace_close")
            self.assertNotIn("transport", pending[0])
            snapshot = next(e for e in events if e["event"] == "dispatch_report_snapshot")
            self.assertEqual(snapshot["completed_unknown_outcomes"], 1)
            self.assertEqual(snapshot["pending_attempts"], 1)
            self.assertEqual(snapshot["workers_still_running"], 1)
            self.assertEqual(snapshot["capacity_skips"], 1)
            self.assertEqual(sum(e["event"] == "capacity_skipped" for e in events), 1)
            self.assertIn("drain_deadline_reached", [e["event"] for e in events])
            self.assertNotIn("drain_completed", [e["event"] for e in events])
        finally:
            release.set()
            self.assertTrue(finished.wait(1))

    def test_late_completion_is_recorded_while_trace_remains_open(self):
        trace = self.new_trace()
        release = threading.Event()
        done = threading.Event()

        def submit(_):
            release.wait(2)
            return poc.HttpResult("broker_response", 200, "accepted")

        try:
            report = poc.dispatch(simulated_submit(submit), b"{}", poc.Window.from_inputs("0.01", 100),
                                  time.perf_counter_ns(), approved=True, drain_seconds=0, trace=trace)
            self.assertIsNone(report.attempts[0].result)
            original_result = trace.result

            def observe(*args, **kwargs):
                original_result(*args, **kwargs)
                done.set()

            with patch.object(trace, "result", side_effect=observe):
                release.set()
                self.assertTrue(done.wait(1))
            self.assertEqual(report.diagnostics()["rows"][0]["state"], "pending")
            self.assertEqual(report.diagnostics()["pending_attempts"], 1)
            names = [e["event"] for e in self.events(trace)]
            self.assertLess(names.index("dispatch_report_snapshot"), names.index("attempt_result_completed"))
        finally:
            release.set()

    def test_non_initiated_outcome_has_schedule_correlation_and_no_attempt_number(self):
        trace = self.new_trace()
        report = self.fake_dispatch(trace, lambda body, begin: poc.HttpResult("native_verification_required"))
        events = self.events(trace)
        event = next(e for e in events if e["event"] == "non_initiated_outcome")
        self.assertEqual(event["scheduled_attempt"], 1)
        self.assertEqual(event["scheduled_monotonic_ns"], 0)
        self.assertEqual(event["transport"], "native_verification_required")
        self.assertNotIn("attempt_number", event)
        self.assertEqual(report.attempts, [])
        self.assertFalse(any(e["event"] == "attempt_initiated" for e in events))

    def test_concurrent_writing_preserves_all_events_and_single_writer(self):
        trace = self.new_trace()
        original = trace._write
        disk_threads = []

        def write(record):
            disk_threads.append(threading.current_thread().name)
            original(record)

        with patch.object(trace, "_write", side_effect=write):
            producers = [threading.Thread(target=lambda n=n: [trace.emit("attempt_initiated", attempt_number=n * 50 + i)
                                                             for i in range(50)]) for n in range(8)]
            for producer in producers:
                producer.start()
            for producer in producers:
                producer.join(1)
                self.assertFalse(producer.is_alive())
            events = self.events(trace)
        self.assertEqual(len(events), 401)
        self.assertEqual({e["attempt_number"] for e in events[1:]}, set(range(400)))
        self.assertEqual(set(disk_threads), {"run-trace-writer"})
        self.assertIsNone(trace.failure)
        self.assertEqual(trace.unwritten_events, 0)

    def test_initialization_failure_prevents_authentication_and_first_post(self):
        with patch.object(Path, "open", side_effect=OSError("fake-private-token")), \
                patch.object(poc, "authenticate_browser") as login, \
                patch.object(poc.NativeHttp, "submit") as submit, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(poc.main(["--authenticate", "--live"]), 2)
        login.assert_not_called()
        submit.assert_not_called()
        self.assertIn("trace initialization failed", output.getvalue())
        self.assertNotIn("fake-private-token", output.getvalue())

    def test_initial_validation_write_failure_is_sanitized_and_prevents_post(self):
        with patch.object(poc.RunTrace, "_write", side_effect=OSError(FAKE_TOKEN)), \
                patch.object(poc.NativeHttp, "submit") as submit, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(poc.main(["--authenticate", "--live"]), 2)
        submit.assert_not_called()
        self.assertNotIn(FAKE_TOKEN, output.getvalue())

    def test_writer_failure_stops_future_attempts_and_flushes_retained_events_on_close(self):
        trace = self.new_trace()
        failed = threading.Event()
        original = trace._write

        def fail_on_initiation(record):
            if record["event"] == "attempt_initiated":
                failed.set()
                raise OSError("fake-private-writer-error")
            original(record)

        def submit(_):
            self.assertTrue(failed.wait(1))
            # The writer sets failure immediately after the failing write.
            with trace._condition:
                trace._condition.wait_for(lambda: trace._failure is not None, timeout=1)
            return poc.HttpResult("broker_response", 200, "accepted")

        with patch.object(trace, "_write", side_effect=fail_on_initiation):
            report = self.fake_dispatch(trace, simulated_submit(submit), concurrency=1)
        self.assertEqual(len(report.attempts), 1)
        self.assertEqual(report.stop, "trace_writer_failed")
        events = self.events(trace)
        self.assertEqual(sum(e["event"] == "attempt_initiated" for e in events), 1)
        self.assertEqual(sum(e["event"] == "attempt_result_completed" for e in events), 1)
        self.assertEqual(trace.unwritten_events, 0)
        self.assertNotIn("fake-private-writer-error", trace.path.read_text())

    def test_exhausted_queue_stops_dispatch_without_dropping_buffered_events(self):
        trace = self.new_trace(capacity=1)
        entered, release = threading.Event(), threading.Event()
        original = trace._write

        def blocked(record):
            entered.set()
            release.wait(2)
            original(record)

        try:
            with patch.object(trace, "_write", side_effect=blocked):
                trace.emit("authentication_started")
                self.assertTrue(entered.wait(1))
                self.assertFalse(trace.emit("authentication_completed"))
                cancel = threading.Event()
                trace.bind_cancel(cancel)
                self.assertTrue(cancel.is_set())
                submit = Mock()
                with self.assertRaisesRegex(poc.Blocked, "trace_queue_exhausted"):
                    self.fake_dispatch(trace, submit)
                submit.assert_not_called()
                release.set()
                events = self.events(trace)
            self.assertEqual([e["event"] for e in events],
                             ["run_started", "authentication_started", "authentication_completed"])
            self.assertEqual(trace.unwritten_events, 0)
        finally:
            release.set()

    def test_blocked_disk_writer_does_not_wait_in_dispatch_scheduler_or_workers(self):
        trace = self.new_trace()
        entered, release = threading.Event(), threading.Event()
        original = trace._write

        def blocked(record):
            entered.set()
            release.wait(2)
            original(record)

        try:
            with patch.object(trace, "_write", side_effect=blocked):
                trace.emit("authentication_started")
                self.assertTrue(entered.wait(1))
                report = self.fake_dispatch(trace, simulated_submit(lambda _: poc.HttpResult("broker_response", 200, "accepted")))
                self.assertFalse(release.is_set())
                self.assertEqual(len(report.attempts), 3)
                self.assertTrue(all(a.result is not None for a in report.attempts))
                self.assertEqual([a.initiated_ns for a in report.attempts], [0, 350_000_000, 700_000_000])
                self.assertIsNone(trace.failure)
                release.set()
                events = self.events(trace)
            self.assertEqual(sum(e["event"] == "attempt_result_completed" for e in events), 3)
        finally:
            release.set()

    def test_authentication_failure_flushes_abort_without_private_exception_text(self):
        with patch.object(poc, "authenticate_browser", side_effect=RuntimeError(FAKE_TOKEN)), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(poc.main(["--authenticate", "--live"]), 2)
        path, = Path(self.trace_directory.name).glob("*.jsonl")
        raw = path.read_text(encoding="utf-8")
        events = [json.loads(line) for line in raw.splitlines()]
        self.assertEqual([e["event"] for e in events], ["run_started", "authentication_started", "run_aborted"])
        self.assertEqual(events[-1]["stop_category"], "unexpected_failure_no_retry")
        self.assertNotIn(FAKE_TOKEN, raw + output.getvalue())

    def test_close_failure_has_failure_exit_status_and_explicit_unwritten_count(self):
        draft, symbol, market = fixtures()
        order = poc.build_buy(draft, symbol, market, 100000000, 1000, 1000, poc.DESKTOP)
        client = Mock(read_outcome="verified_money_and_drafts")
        client.verify.return_value = [draft]
        original = poc.RunTrace._write

        def fail_final(trace, record):
            if record["event"] == "run_aborted":
                raise OSError("fake-private-final-flush")
            original(trace, record)

        with patch.object(poc.RunTrace, "_write", new=fail_final), \
                patch.object(poc, "authenticate_browser", return_value=auth()), \
                patch.object(poc, "NativeHttp", return_value=client), \
                patch.object(poc, "preflight", return_value=poc.Preflight(order, 0)), \
                patch.object(poc, "local_target", return_value=AT), \
                patch.object(poc, "confirm_order", return_value=False), \
                patch("builtins.input", side_effect=["1", "", "", "0.5", "340"]), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(poc.main(["--authenticate", "--live", "--diagnostics"]), 2)
        client.submit.assert_not_called()
        client.close.assert_called_once()
        text = output.getvalue()
        self.assertIn("trace writer failed", text)
        self.assertIn("Trace events not persisted: 1", text)
        self.assertNotIn("fake-private-final-flush", text)
        diagnostics = json.loads(next(line for line in text.splitlines() if line.startswith("{")))
        self.assertEqual(diagnostics["stop"], "trace_writer_failed")
        self.assertEqual(diagnostics["trace_unwritten_events"], 1)

    def test_partial_line_is_rolled_back_before_final_flush(self):
        trace = self.new_trace()
        failed = threading.Event()
        original = trace._file.write

        def partial(line):
            original(line[:10])
            failed.set()
            raise OSError("fake-private-partial-write")

        with patch.object(trace._file, "write", side_effect=partial):
            trace.emit("authentication_started")
            self.assertTrue(failed.wait(1))
            with trace._condition:
                self.assertTrue(trace._condition.wait_for(lambda: trace._failure is not None, timeout=1))
        self.assertEqual([e["event"] for e in self.events(trace)], ["run_started", "authentication_started"])
        self.assertEqual(trace.failure, "trace_writer_failed")
        self.assertEqual(trace.unwritten_events, 0)

    def test_terminal_event_seals_admission_for_late_worker_results(self):
        trace = self.new_trace()
        trace.emit("attempt_pending_at_snapshot", attempt_number=1, pending_at_snapshot=True,
                   completed_result_available=False, worker_alive=True,
                   completion_observation="until_trace_close")
        trace.close(outcome="completed", stop_category="cutoff")
        self.assertFalse(trace.emit("attempt_result_completed", attempt_number=1))
        names = [e["event"] for e in self.events(trace)]
        self.assertEqual(names, ["run_started", "attempt_pending_at_snapshot", "run_completed"])

    def test_allowlist_excludes_private_fields_categories_and_exception_messages(self):
        trace = self.new_trace()
        private = "fake-private-token-cookie-broker-id-message"
        result = poc.HttpResult(private, 200, private, 123, private)
        self.fake_dispatch(trace, simulated_submit(lambda _: result))
        trace.result("non_initiated_outcome", result, scheduled_attempt=4)
        self.assertFalse(trace.emit("run_aborted", payload=private))
        events = self.events(trace)
        raw = trace.path.read_text(encoding="utf-8")
        self.assertNotIn(private, raw)
        self.assertNotIn("fake-private-payload", raw)
        results = [e for e in events if e["event"] == "attempt_result_completed"]
        self.assertTrue(all(e["transport"] == "other_transport_outcome" for e in results))
        self.assertTrue(all(e["broker_acceptance"] == "unknown" for e in results))
        self.assertTrue(all(e["rejection_category"] is None for e in results))
        self.assertEqual(trace.failure, "trace_event_invalid")

    def test_loopback_http_traces_only_sanitized_completion_facts(self):
        for ack, expected in (({"isSuccessful": True, "id": "fake-private-broker-id"}, "accepted"),
                              ({"isSuccessful": False, "message": "fake-private-message"}, "rejected"),
                              ({"isSuccessful": True, "private": "fake-private-response"}, "unknown")):
            with self.subTest(expected=expected), Server() as server:
                server.ack = {**ack, "account": "fake-private-account", "balance": "fake-private-balance"}
                client = server.client()
                self.addCleanup(client.close)
                client.verify()
                trace = self.new_trace()
                report = poc.dispatch(lambda body, begin: client.submit(body, approved=True, on_initiated=begin),
                                      b'{"private":"fake-private-payload"}', poc.Window.from_inputs("0.01", 100),
                                      time.perf_counter_ns(), approved=True, trace=trace)
                event = next(e for e in self.events(trace) if e["event"] == "attempt_result_completed")
                self.assertEqual(len(server.received), 1)
                self.assertEqual(report.attempts[0].result.acceptance, expected)
                self.assertEqual(event["broker_acceptance"], expected)
                self.assertEqual(event["http_status"], 200)
                self.assertGreater(event["elapsed_ns"], 0)
                raw = trace.path.read_text(encoding="utf-8")
                for secret in (FAKE_TOKEN, FAKE_COOKIE, ISIN, "fake-private", "TEST", "Authorization", "buyPowerT2"):
                    self.assertNotIn(secret, raw)

    def boundary_dispatch(self, client, trace, *, prepare=None):
        clock = FakeClock()
        callbacks, post_calls = [], []
        original_request = poc.http.client.HTTPConnection.request

        def request(connection, method, path, *args, **kwargs):
            if method == "POST" and path == poc.ORDER:
                post_calls.append(clock())
            return original_request(connection, method, path, *args, **kwargs)

        def submit(body, begin):
            # Inspect only the pacing cell: rejected admission must not change
            # it. HTTP calls, received orders, report and JSONL are checked too.
            last = dict(zip(begin.__code__.co_freevars, begin.__closure__))["last"]

            def boundary():
                if prepare is not None:
                    prepare()
                before = last.cell_contents
                allowed = begin()
                callbacks.append((allowed, before, last.cell_contents))
                return allowed

            return client.submit(body, approved=True, on_initiated=boundary)

        with patch.object(poc.http.client.HTTPConnection, "request", new=request):
            report = poc.dispatch(submit, b"{}", poc.Window.from_inputs(1, 350), 0,
                                  approved=True, concurrency=1, trace=trace, clock=clock,
                                  pause=clock.advance, cancel=FakeCancel(clock))
        return report, callbacks, post_calls

    def assert_rejected_boundary(self, server, trace, report, callbacks, post_calls, category):
        self.assertEqual(post_calls, [])
        self.assertEqual(server.received, [])
        self.assertEqual(callbacks, [(False, None, None)])
        self.assertEqual(report.attempts, [])
        self.assertEqual(report.scheduled_attempts, 1)
        self.assertEqual(report.capacity_skips, 0)
        self.assertEqual(report.non_initiated, ["initiation_cancelled_or_cutoff"])
        self.assertEqual(report.stop, category)
        events = self.events(trace)
        self.assertFalse(any(e["event"] == "attempt_initiated" for e in events))
        non_initiated = [e for e in events if e["event"] == "non_initiated_outcome"]
        self.assertEqual(len(non_initiated), 1)
        self.assertEqual(non_initiated[0]["scheduled_attempt"], 1)
        self.assertEqual(non_initiated[0]["transport"], "initiation_cancelled_or_cutoff")
        snapshot = next(e for e in events if e["event"] == "dispatch_report_snapshot")
        self.assertEqual(snapshot["trace_failure"], category)
        self.assertEqual(snapshot["initiated_attempts"], 0)
        self.assertEqual(snapshot["scheduled_attempts"], 1)
        self.assertEqual(snapshot["capacity_skips"], 0)
        self.assertEqual(snapshot["pending_attempts"], 0)
        self.assertEqual(snapshot["workers_still_running"], 0)
        return events

    def test_initiation_emit_refusal_prevents_http_post_and_preserves_pacing(self):
        for category in ("trace_writer_failed", "trace_queue_exhausted", "trace_event_invalid"):
            with self.subTest(category=category), Server() as server:
                client = server.client()
                self.addCleanup(client.close)
                client.verify()
                trace = self.new_trace()
                original_emit = trace.emit

                def refuse(event, **fields):
                    if event == "attempt_initiated":
                        with trace._condition:
                            trace._fail(category)
                        return False
                    return original_emit(event, **fields)

                with patch.object(trace, "emit", side_effect=refuse):
                    report, callbacks, post_calls = self.boundary_dispatch(client, trace)
                self.assert_rejected_boundary(server, trace, report, callbacks, post_calls, category)

    def test_full_queue_at_initiation_admission_preserves_buffer_and_cleanup_reserve(self):
        with Server() as server:
            client = server.client()
            self.addCleanup(client.close)
            client.verify()
            trace = self.new_trace(capacity=5)
            entered, release = threading.Event(), threading.Event()
            original_write = trace._write
            buffered = []

            def blocked(record):
                entered.set()
                if not release.wait(5):
                    raise AssertionError("Writer release was not signalled")
                original_write(record)

            def fill_at_boundary():
                self.assertTrue(entered.wait(5))
                with trace._condition:
                    for event in ("authentication_started", "authentication_completed", "native_verification_completed"):
                        self.assertTrue(trace.emit(event))
                    self.assertEqual(len(trace._pending), trace._capacity)
                    self.assertIsNone(trace._failure)
                    buffered.extend(dict(event) for event in trace._pending)

            try:
                with patch.object(trace, "_write", side_effect=blocked):
                    report, callbacks, post_calls = self.boundary_dispatch(client, trace, prepare=fill_at_boundary)
                    self.assertEqual(post_calls, [])
                    with trace._condition:
                        pending = list(trace._pending)
                        self.assertEqual(pending[:5], buffered)
                        self.assertGreater(len(pending), trace._capacity)
                        self.assertTrue(any(e["event"] == "non_initiated_outcome" for e in pending))
                        self.assertTrue(any(e["event"] == "dispatch_report_snapshot" for e in pending))
                    release.set()
                    events = self.assert_rejected_boundary(server, trace, report, callbacks, post_calls,
                                                           "trace_queue_exhausted")
                self.assertEqual(events[1:6], buffered)
                self.assertEqual(trace.unwritten_events, 0)
            finally:
                release.set()

    def writer_failure_at_boundary(self, *, admit_first):
        with Server() as server:
            client = server.client()
            self.addCleanup(client.close)
            client.verify()
            trace = self.new_trace()
            writing, release, published = (threading.Event() for _ in range(3))
            original_write, original_fail, original_admit = trace._write, trace._fail, trace.admit_initiation
            decisions = []

            def fail_write(record):
                if record["event"] == "dispatch_started":
                    writing.set()
                    if not release.wait(5):
                        raise AssertionError("Initiation boundary was not reached")
                    raise OSError("fake-offline-writer-failure")
                original_write(record)

            def publish(category):
                original_fail(category)
                if category == "trace_writer_failed":
                    published.set()

            def admission(**fields):
                # This gate runs before taking the trace condition, while the
                # dispatch lock is held. The writer must publish without needing
                # that lock. The opposite ordering tests an admitted request.
                self.assertTrue(writing.wait(5))
                if admit_first:
                    decision = original_admit(**fields)
                release.set()
                self.assertTrue(published.wait(5))
                if not admit_first:
                    decision = original_admit(**fields)
                decisions.append(decision)
                return decision

            try:
                with patch.object(trace, "_write", side_effect=fail_write), \
                        patch.object(trace, "_fail", side_effect=publish), \
                        patch.object(trace, "admit_initiation", side_effect=admission):
                    report, callbacks, post_calls = self.boundary_dispatch(client, trace)
                self.assertTrue(writing.is_set())
                self.assertTrue(published.is_set())
                self.assertEqual(decisions, [admit_first])
                if not admit_first:
                    self.assert_rejected_boundary(server, trace, report, callbacks, post_calls, "trace_writer_failed")
                    return

                # Admission succeeded before publication. The request remains
                # in-flight even though failure precedes the actual HTTP call.
                self.assertEqual(callbacks, [(True, None, 0)])
                self.assertEqual(post_calls, [0])
                self.assertEqual(len(server.received), 1)
                self.assertEqual(len(report.attempts), 1)
                self.assertEqual(report.attempts[0].result.acceptance, "accepted")
                self.assertEqual(report.attempts[0].result.status, 200)
                self.assertEqual(report.scheduled_attempts, 1)
                self.assertEqual(report.capacity_skips, 0)
                self.assertEqual(report.non_initiated, [])
                self.assertEqual(report.stop, "trace_writer_failed")
                self.assertFalse(original_admit(attempt_number=2))
                events = self.events(trace)
                starts = [e for e in events if e["event"] == "attempt_initiated"]
                results = [e for e in events if e["event"] == "attempt_result_completed"]
                self.assertEqual([e["attempt_number"] for e in starts], [1])
                self.assertEqual([e["attempt_number"] for e in results], [1])
                self.assertEqual(results[0]["broker_acceptance"], "accepted")
                self.assertEqual(results[0]["http_status"], 200)
                snapshot = next(e for e in events if e["event"] == "dispatch_report_snapshot")
                self.assertEqual(snapshot["trace_failure"], "trace_writer_failed")
                self.assertEqual(snapshot["initiated_attempts"], 1)
                self.assertEqual(snapshot["completed_broker_acknowledgements"], 1)
                self.assertEqual(snapshot["http_responses_observed"], 1)
                self.assertEqual(snapshot["pending_attempts"], 0)
                self.assertEqual(snapshot["workers_still_running"], 0)
                self.assertEqual(trace.unwritten_events, 0)
            finally:
                release.set()

    def test_writer_failure_published_at_boundary_rejects_initiation_without_post(self):
        self.writer_failure_at_boundary(admit_first=False)

    def test_admitted_initiation_survives_subsequent_writer_failure_and_records_result(self):
        self.writer_failure_at_boundary(admit_first=True)


class ConsoleTests(OfflineCase):
    def test_countdown_elapsed_and_request_count_are_read_from_monotonic_state(self):
        clock = FakeClock()
        console = poc.LiveConsole(2_000_000_000, poc.Window.from_inputs(3, 340), threading.Event(),
                                  stream=io.StringIO(), clock=clock, poll_cancel=lambda: False)
        self.assertIn("Starts in 00:00:02.000000", console.frame())
        clock.advance(2.5)
        console.stage = "Ready"
        console.report = poc.DispatchReport(9, attempts=[poc.Attempt(1, 2_000_000_000)])
        frame = console.frame()
        self.assertIn("Sending", frame)
        self.assertIn("Elapsed 00:00:00.500000", frame)
        self.assertIn("Left 00:00:02.500000", frame)
        self.assertIn("Requests 1", frame)
        clock.advance(3)
        self.assertIn("Finishing", console.frame())
        self.assertIn("Left 00:00:00.000000", console.frame())
        self.assertLess(len(console.frame()), 80)

    def test_escape_cancels_future_work_without_a_browser_call(self):
        cancel = threading.Event()
        with poc.LiveConsole(time.perf_counter_ns() + 1_000_000_000, poc.Window.from_inputs(), cancel,
                             stream=io.StringIO(), poll_cancel=lambda: True):
            self.assertTrue(cancel.wait(.5))

    def test_summary_distinguishes_acknowledgements_and_unknown_execution(self):
        report = poc.DispatchReport(4, attempts=[
            poc.Attempt(1, 1, poc.HttpResult("broker_response", 200, "accepted")),
            poc.Attempt(2, 2, poc.HttpResult("broker_response", 200, "rejected", rejection_reason="market_entry_time")),
            poc.Attempt(3, 3),
            poc.Attempt(4, 4, poc.HttpResult("broker_response", 200, "rejected", rejection_reason="unspecified"))])
        with contextlib.redirect_stdout(io.StringIO()) as out:
            poc.print_live_summary(report)
        self.assertIn("accepted 1 | rejected 2 | unknown 0", out.getvalue())
        self.assertIn("Pending after drain: 1", out.getvalue())
        self.assertIn("Execution/fills were not verified", out.getvalue())
        self.assertIn("no cause was assumed", out.getvalue())
        self.assertNotIn('"attempts":', out.getvalue())

    def test_slow_console_output_does_not_throttle_http_calls(self):
        class SlowConsole(io.StringIO):
            def isatty(self):
                return True

            def write(self, value):
                if value.startswith("\r"):
                    time.sleep(.4)
                return super().write(value)

        with Server() as server:
            client = server.client()
            self.addCleanup(client.close)
            client.verify()
            client.warm_connections(3, time.perf_counter_ns() + 1_000_000_000)
            start, cancel = time.perf_counter_ns() + 100_000_000, threading.Event()
            window = poc.Window.from_inputs(1, 340)
            with poc.LiveConsole(start, window, cancel, stream=SlowConsole(), poll_cancel=lambda: False) as progress:
                report = poc.dispatch(lambda body, begin: client.submit(body, approved=True, on_initiated=begin),
                                      b"{}", window, start, approved=True, concurrency=3, progress=progress)
            self.assertEqual(len(server.received), 3)
            self.assertEqual(len(report.attempts), 3)
            self.assertEqual(report.capacity_skips, 0)
            stamps = [a.initiated_ns for a in report.attempts]
            self.assertTrue(all(b - a >= 340_000_000 for a, b in zip(stamps, stamps[1:])))


if __name__ == "__main__":
    unittest.main(verbosity=2)
