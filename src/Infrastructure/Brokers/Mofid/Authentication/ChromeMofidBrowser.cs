using System.Text.Json;
using Microsoft.Playwright;
using TseExcel.Application.Trading.OpeningOrders;

namespace TseExcel.Infrastructure.Brokers.Mofid;

internal sealed class ChromeMofidBrowser : IMofidBrowser
{
    private readonly Func<Task<IPlaywright>> createPlaywright;
    private readonly Func<uint, CancellationToken, Task> hideOwnedWindows;
    internal ChromeMofidBrowser(string driverDirectory) : this(() => MofidBrowserDriver.CreateAsync(driverDirectory)) { }
    internal ChromeMofidBrowser(Func<Task<IPlaywright>> createPlaywright,
        Func<uint, CancellationToken, Task>? hideOwnedWindows = null)
    { this.createPlaywright = createPlaywright; this.hideOwnedWindows = hideOwnedWindows ?? OwnedChromeWindows.HideAsync; }
    internal const string ClientOrigin = "https://d.easytrader.ir";
    internal const string ApiOrigin = "https://api-mts.orbis.easytrader.ir";
    private readonly SemaphoreSlim sessionGate = new(1, 1);
    private readonly object headerLock = new();
    private Dictionary<string, string> headers = new(StringComparer.OrdinalIgnoreCase);
    private IPlaywright? playwright;
    private IBrowser? browser;
    private IBrowserContext? context;
    private IPage? transportPage;
    private bool authenticated;

    internal static BrowserTypeLaunchOptions LaunchOptions() => new() { Channel = "chrome", Headless = false };

    public async Task AuthenticateAsync(bool refresh, CancellationToken cancellationToken)
    {
        await sessionGate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            if (!refresh && authenticated)
            {
                try
                {
                    JsonElement money = await ReadAsync(MofidRead.Money, null, cancellationToken).ConfigureAwait(false);
                    MofidJson.Number(money, "buyPowerT2");
                    return;
                }
                catch (OpeningOrderException) { authenticated = false; }
            }
            await CloseBrowserAsync().ConfigureAwait(false);
            playwright = await createPlaywright().ConfigureAwait(false);
            // A dedicated installed Chrome process; never attach to the user's browsing session.
            browser = await playwright.Chromium.LaunchAsync(LaunchOptions()).ConfigureAwait(false);
            context = await browser.NewContextAsync(new() { ServiceWorkers = ServiceWorkerPolicy.Block, AcceptDownloads = false }).ConfigureAwait(false);
            context.Request += CaptureHeaders;
            transportPage = await context.NewPageAsync().ConfigureAwait(false);

            // The login popup has its own window. The retained page uses the exact same ephemeral context.
            IPage login = await context.RunAndWaitForPageAsync(async () =>
                await transportPage.EvaluateAsync("() => { window.open('about:blank', '_blank', 'popup,width=1000,height=780'); }").ConfigureAwait(false),
                new() { Timeout = 30_000 }).ConfigureAwait(false);
            await MinimizeOwnedWindowAsync(transportPage).ConfigureAwait(false);
            Task<IResponse> signedIn = login.WaitForResponseAsync(response => response.Request.Method == "GET" &&
                response.Url.Split('?')[0] == ApiOrigin + "/easy/api/money" && response.Status == 200 &&
                !response.FromServiceWorker && response.Headers.TryGetValue("content-type", out string? contentType) &&
                contentType.Split(';')[0].Trim().Equals("application/json", StringComparison.OrdinalIgnoreCase), new() { Timeout = 300_000 });
            await login.GotoAsync(ClientOrigin + "/", new() { WaitUntil = WaitUntilState.Commit, Timeout = 30_000 }).ConfigureAwait(false);
            IResponse observed = await signedIn.WaitAsync(cancellationToken).ConfigureAwait(false);
            byte[] body = await observed.BodyAsync().ConfigureAwait(false);
            if (body.Length > 1_000_000) throw MofidJson.Invalid();
            using (JsonDocument document = JsonDocument.Parse(body)) MofidJson.Number(document.RootElement, "buyPowerT2");
            await login.WaitForLoadStateAsync(LoadState.DOMContentLoaded).ConfigureAwait(false);
            RequireClientPage(login);
            Capture(await observed.Request.AllHeadersAsync().ConfigureAwait(false));
            // sessionStorage is page-scoped even within one context; retain it only in memory.
            Dictionary<string, string> transient = await login.EvaluateAsync<Dictionary<string, string>>(
                "() => Object.fromEntries(Object.entries(sessionStorage))").ConfigureAwait(false);
            await using IAsyncDisposable storageSeed = await transportPage.AddInitScriptAsync("if (location.origin === " + JsonSerializer.Serialize(ClientOrigin) +
                ") { for (const [key, value] of Object.entries(" + JsonSerializer.Serialize(transient) +
                ")) sessionStorage.setItem(key, value); }").ConfigureAwait(false);
            authenticated = true;
            await login.CloseAsync().ConfigureAwait(false);
            // Cookies and localStorage stay in the original context; no persistent storage export.
            await transportPage.GotoAsync(ClientOrigin + "/", new() { WaitUntil = WaitUntilState.DOMContentLoaded, Timeout = 30_000 }).ConfigureAwait(false);
            JsonElement verified = await ReadAsync(MofidRead.Money, null, cancellationToken).ConfigureAwait(false);
            MofidJson.Number(verified, "buyPowerT2");
            // Authentication can open additional pages. Close all owned pages except the verified transport.
            foreach (IBrowserContext ownedContext in browser.Contexts)
                foreach (IPage page in ownedContext.Pages.ToArray())
                    if (!ReferenceEquals(page, transportPage) && !page.IsClosed) await page.CloseAsync().ConfigureAwait(false);
            RequireClientPage(transportPage);
            ICDPSession browserSession = await browser.NewBrowserCDPSessionAsync().ConfigureAwait(false);
            try
            {
                JsonElement? processes = await browserSession.SendAsync("SystemInfo.getProcessInfo").ConfigureAwait(false);
                JsonElement[] owners = processes!.Value.GetProperty("processInfo").EnumerateArray()
                    .Where(x => x.GetProperty("type").GetString() == "browser").ToArray();
                if (owners.Length != 1 || !owners[0].GetProperty("id").TryGetUInt32(out uint processId) || processId == 0)
                    throw new OpeningOrderException("Owned Chrome process could not be verified.", OpeningOrderError.Authentication);
                // Hiding the retained window removes its minimized taskbar entry without destroying its context.
                await hideOwnedWindows(processId, cancellationToken).ConfigureAwait(false);
            }
            finally { await browserSession.DetachAsync().ConfigureAwait(false); }
        }
        catch (OperationCanceledException)
        {
            await CloseBrowserAsync().ConfigureAwait(false);
            throw;
        }
        catch (Exception exception) when (exception is PlaywrightException or JsonException or OpeningOrderException or InvalidOperationException or KeyNotFoundException)
        {
            await CloseBrowserAsync().ConfigureAwait(false);
            var numeric = exception as OpeningOrderException;
            throw new OpeningOrderException("Interactive Chrome authentication did not establish a verified session.", OpeningOrderError.Authentication,
                numeric?.Field ?? OpeningOrderField.None, numeric?.NumericIssue ?? NumericIssue.None).AtStage(OpeningOrderStage.Authentication);
        }
        finally { sessionGate.Release(); }
    }

    private async Task MinimizeOwnedWindowAsync(IPage page)
    {
        ICDPSession session = await context!.NewCDPSessionAsync(page).ConfigureAwait(false);
        try
        {
            JsonElement? result = await session.SendAsync("Browser.getWindowForTarget").ConfigureAwait(false);
            int windowId = result!.Value.GetProperty("windowId").GetInt32();
            await session.SendAsync("Browser.setWindowBounds", new Dictionary<string, object>
            { ["windowId"] = windowId, ["bounds"] = new Dictionary<string, object> { ["windowState"] = "minimized" } }).ConfigureAwait(false);
        }
        finally { await session.DetachAsync().ConfigureAwait(false); }
    }

    private void CaptureHeaders(object? sender, IRequest request)
    {
        if (Uri.TryCreate(request.Url, UriKind.Absolute, out Uri? uri) && uri.GetLeftPart(UriPartial.Authority) == ApiOrigin)
            Capture(request.Headers);
    }

    private void Capture(IDictionary<string, string> observed)
    {
        string[] allowed = ["authorization", "x-device-id", "x-app-name", "x-customheader", "x-api-key", "shard"];
        var next = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach ((string key, string value) in observed)
            if (allowed.Contains(key, StringComparer.OrdinalIgnoreCase) && value.Length <= 20_000 && !value.Contains('\r') && !value.Contains('\n')) next[key] = value;
        lock (headerLock)
        {
            // Keep the last observed bearer headers when unrelated cookie-only requests occur.
            if (next.TryGetValue("authorization", out string? bearer) && bearer.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase)) headers = next;
        }
    }

    private Dictionary<string, string> RequestHeaders(bool post)
    {
        Dictionary<string, string> result;
        lock (headerLock) result = new(headers, StringComparer.OrdinalIgnoreCase);
        result["Accept"] = "application/json";
        result["Cache-Control"] = "no-cache";
        if (post) result["Content-Type"] = "application/json";
        return result;
    }

    private static void RequireClientPage(IPage page)
    {
        if (!Uri.TryCreate(page.Url, UriKind.Absolute, out Uri? uri) || uri.GetLeftPart(UriPartial.Authority) != ClientOrigin)
            throw new OpeningOrderException("The owned browser left the verified EasyTrader origin.", OpeningOrderError.Authentication);
    }

    internal static (string Path, string Method, string? Body, int MaximumBytes) ReadRequest(MofidRead read, string? isin) => read switch
    {
        MofidRead.Drafts => ("/easy/api/draft", "GET", null, 1_000_000),
        MofidRead.Symbols => ("/symbols/api/symbols/all", "POST", "{\"hash\":\"null\"}", 12_000_000),
        MofidRead.Market when isin is not null => ("/symbols/api/marketdata/v2", "POST", JsonSerializer.Serialize(new[] { isin }), 1_000_000),
        MofidRead.Money => ("/easy/api/money", "GET", null, 1_000_000),
        MofidRead.Calendar => ("/symbols/api/TradingTime", "GET", null, 1_000_000),
        MofidRead.Session => ("/easy/api/startsession", "GET", null, 1_000_000),
        _ => throw new OpeningOrderException("The requested read is outside the verified allowlist.")
    };

    public async Task<JsonElement> ReadAsync(MofidRead read, string? symbolIsin, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (!authenticated || transportPage is null) throw new OpeningOrderException("An authenticated Chrome context is required.", OpeningOrderError.Authentication);
        RequireClientPage(transportPage);
        var request = ReadRequest(read, symbolIsin);
        try
        {
            JsonElement result = await transportPage.EvaluateAsync<JsonElement>(ReadScript, new
            {
                url = ApiOrigin + request.Path, method = request.Method, body = request.Body,
                headers = RequestHeaders(request.Method == "POST"), maximumBytes = request.MaximumBytes
            }).WaitAsync(cancellationToken).ConfigureAwait(false);
            if (!result.GetProperty("ok").GetBoolean())
            {
                authenticated = false;
                OpeningOrderError error = result.TryGetProperty("authentication", out JsonElement auth) && auth.ValueKind == JsonValueKind.True
                    ? OpeningOrderError.Authentication
                    : result.TryGetProperty("malformed", out JsonElement malformed) && malformed.ValueKind == JsonValueKind.True
                        ? OpeningOrderError.MalformedResponse : OpeningOrderError.ReadFailure;
                throw new OpeningOrderException("Authenticated browser read did not return verified data.", error);
            }
            JsonElement body = result.GetProperty("body");
            if (body.ValueKind != JsonValueKind.String) throw MofidJson.Invalid();
            using JsonDocument document = JsonDocument.Parse(body.GetString()!);
            return document.RootElement.Clone();
        }
        catch (PlaywrightException)
        {
            throw new OpeningOrderException("Mofid browser read could not complete.", OpeningOrderError.ReadFailure);
        }
        catch (Exception exception) when (exception is JsonException or InvalidOperationException or KeyNotFoundException)
        {
            throw MofidJson.Invalid();
        }
    }

    internal const string ReadScript = """
        async args => {
          const controller = new AbortController();
          const timer = setTimeout(() => controller.abort(), 15000);
          try {
            const response = await fetch(args.url, {method: args.method, headers: args.headers,
              body: args.body ?? undefined, credentials: 'include', redirect: 'error',
              cache: 'no-store', signal: controller.signal});
            if (response.status === 401 || response.status === 403) return {ok:false, authentication:true};
            if (!response.ok) return {ok:false};
            if ((response.headers.get('content-type') || '').split(';')[0].trim().toLowerCase() !== 'application/json' || !response.body)
              return {ok:false, malformed:true};
            const reader = response.body.getReader();
            const chunks = []; let size = 0;
            for (;;) {
              const chunk = await reader.read(); if (chunk.done) break;
              size += chunk.value.byteLength;
              if (size > args.maximumBytes) { await reader.cancel(); return {ok:false, malformed:true}; }
              chunks.push(chunk.value);
            }
            const bytes = new Uint8Array(size); let offset = 0;
            for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
            try { return {ok:true, body:new TextDecoder('utf-8', {fatal:true}).decode(bytes)}; }
            catch { return {ok:false, malformed:true}; }
          } catch { return {ok:false}; }
          finally { clearTimeout(timer); }
        }
        """;

    internal const string PrepareDispatchScript = """
        args => {
          if (window.__tseOpening) throw new Error('An operation is already active');
          const state = {cancelled:false, payload:args.payload,
            headers:args.headers, url:args.url, cutoff:args.cutoff};
          // Stop only future initiations. Already initiated requests retain their transport lifetime.
          state.stop = () => { state.cancelled = true; };
          state.timer = setTimeout(state.stop, Math.max(0, args.cutoff - Date.now()));
          window.__tseOpening = state;
        }
        """;

    public async Task<IOrderDispatch> OpenDispatchAsync(string payload, DateTimeOffset cutoff, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (!authenticated || transportPage is null) throw new OpeningOrderException("An authenticated context is required.");
        RequireClientPage(transportPage);
        try
        {
            await transportPage.EvaluateAsync(PrepareDispatchScript, new { payload, cutoff = cutoff.ToUnixTimeMilliseconds(), headers = RequestHeaders(true), url = ApiOrigin + "/core/api/v2/order" }).ConfigureAwait(false);
            return new ChromeOrderDispatch(transportPage);
        }
        catch (PlaywrightException) { throw new OpeningOrderException("The browser could not prepare local dispatch."); }
    }

    private async Task CloseBrowserAsync()
    {
        authenticated = false;
        try { if (browser is not null) await browser.CloseAsync().ConfigureAwait(false); }
        catch (PlaywrightException) { /* Cleanup must never expose session-bearing exception text. */ }
        finally
        {
            playwright?.Dispose();
            playwright = null; browser = null; context = null; transportPage = null;
            lock (headerLock) headers.Clear();
        }
    }

    public async ValueTask DisposeAsync()
    {
        await sessionGate.WaitAsync().ConfigureAwait(false);
        try { await CloseBrowserAsync().ConfigureAwait(false); }
        finally { sessionGate.Release(); }
    }
}
