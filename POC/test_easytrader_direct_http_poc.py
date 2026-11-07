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
import socket
import ssl
import threading
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
                        owner.received.append((time.perf_counter_ns(), body))
                        owner.active += 1
                        owner.max_active = max(owner.active, owner.max_active)
                    if owner.cancel_on_receive is not None:
                        owner.cancel_on_receive.set()
                    try:
                        time.sleep(owner.delay)
                        if owner.drop_order_response:
                            self.close_connection = True
                            self.connection.shutdown(socket.SHUT_RDWR)
                        else:
                            self.send(owner.order_status, owner.ack)
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
        for kwargs in (dict(quantity=5000), dict(quantity=100), dict(funds=1000000), dict(price="NaN"),
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
            self.assertIn('"order_requests": 0', out.getvalue())

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
        self.assertIn("authentication_rejected", out.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
