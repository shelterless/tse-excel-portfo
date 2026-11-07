using System.Reflection;
using System.Text;
using System.Text.Json;
using Microsoft.Playwright;
using TseExcel.Application.Trading.OpeningOrders;
using TseExcel.Infrastructure.Brokers.Mofid;
using Xunit;

namespace TseExcel.Infrastructure.Tests.Brokers.Mofid;

public class ChromeSessionTests
{
    [Fact]
    public async Task Login_LaunchesInstalledChromeAndClosesOnlyLoginWindowRetainingExactContext()
    {
        var fake = new BrowserFake();
        await using var session = new ChromeMofidBrowser(() => Task.FromResult(fake.Playwright));
        await session.AuthenticateAsync(false, CancellationToken.None);
        Assert.Equal("chrome", fake.Launch!.Channel); Assert.False(fake.Launch.Headless);
        Assert.Equal(1, fake.Contexts); Assert.Equal(1, fake.Popups); Assert.Equal(1, fake.LoginCloses);
        Assert.Equal(0, fake.BrowserCloses);
        Assert.Equal(ServiceWorkerPolicy.Block, fake.ContextOptions!.ServiceWorkers);
        Assert.Contains("Browser.setWindowBounds", fake.CdpCommands);
        Assert.Equal(1, fake.TransportNavigations);
        Assert.Contains("sessionStorage.setItem", fake.InitScript);
        Assert.Contains(ChromeMofidBrowser.ClientOrigin, fake.InitScript);
        JsonElement drafts = await session.ReadAsync(MofidRead.Drafts, null, CancellationToken.None);
        Assert.Equal(JsonValueKind.Array, drafts.ValueKind);
        Assert.Equal(1, fake.Contexts);
        Assert.Contains(fake.RequestArguments, args => args.GetProperty("url").GetString() == ChromeMofidBrowser.ApiOrigin + "/easy/api/draft");
        Assert.All(fake.RequestArguments, args => Assert.Equal("Bearer fixture-session", args.GetProperty("headers").GetProperty("authorization").GetString()));
    }

    [Fact]
    public async Task ValidSession_IsReusedAndInvalidReadRequiresFreshInteractiveContext()
    {
        var fake = new BrowserFake();
        await using var session = new ChromeMofidBrowser(() => Task.FromResult(fake.Playwright));
        await session.AuthenticateAsync(false, CancellationToken.None);
        await session.AuthenticateAsync(false, CancellationToken.None);
        Assert.Equal(1, fake.Contexts); Assert.Equal(1, fake.LoginCloses);
        fake.FailNextRead = true;
        await session.AuthenticateAsync(false, CancellationToken.None);
        Assert.Equal(2, fake.Contexts); Assert.Equal(2, fake.LoginCloses); Assert.Equal(1, fake.BrowserCloses);
        await session.AuthenticateAsync(true, CancellationToken.None);
        Assert.Equal(3, fake.Contexts);
    }

    [Fact]
    public async Task AuthErrors_AreSanitizedAndOwnedBrowserIsReleased()
    {
        var fake = new BrowserFake { FailNavigation = true };
        await using var session = new ChromeMofidBrowser(() => Task.FromResult(fake.Playwright));
        OpeningOrderException failure = await Assert.ThrowsAsync<OpeningOrderException>(() => session.AuthenticateAsync(false, CancellationToken.None));
        Assert.DoesNotContain("fixture-secret", failure.ToString());
        Assert.Equal(1, fake.BrowserCloses);
        await Assert.ThrowsAsync<OpeningOrderException>(() => session.ReadAsync(MofidRead.Money, null, CancellationToken.None));
    }

    [Fact]
    public async Task Cancellation_ClosesOwnedSessionWithoutStoringAuthenticationMaterial()
    {
        var fake = new BrowserFake { WaitForLogin = true };
        await using var session = new ChromeMofidBrowser(() => Task.FromResult(fake.Playwright));
        using var cancellation = new CancellationTokenSource();
        Task operation = session.AuthenticateAsync(false, cancellation.Token);
        cancellation.Cancel();
        await Assert.ThrowsAnyAsync<OperationCanceledException>(() => operation);
        Assert.Equal(1, fake.BrowserCloses);
    }

    [Fact]
    public async Task OrderBridge_AcknowledgesOnlyLocalInitiationAndNeverWaitsForBrokerBody()
    {
        long epochMicroseconds = 1_793_000_000_000_124;
        int evaluations = 0;
        var page = ApiProxy.Create<IPage>((method, args) =>
        {
            if (method.Name == "EvaluateAsync" && method.IsGenericMethod)
            {
                evaluations++;
                Assert.Equal(ChromeOrderDispatch.InitiateScript, args![0]);
                return Task.FromResult(JsonSerializer.SerializeToElement(new { initiated = true, failed = false, timestamp = epochMicroseconds }));
            }
            if (method.Name == "EvaluateAsync") return Task.FromResult<JsonElement?>(null);
            throw new InvalidOperationException("Unexpected fixture call: " + method.Name);
        });
        await using var dispatch = new ChromeOrderDispatch(page);
        LocalInitiation result = await dispatch.InitiateAsync(DateTimeOffset.Now, CancellationToken.None);
        Assert.True(result.Initiated); Assert.False(result.LocalFailure);
        Assert.Equal(epochMicroseconds * 10, (result.Timestamp.ToUniversalTime() - DateTimeOffset.UnixEpoch).Ticks);
        Assert.Equal(1, evaluations);
        Assert.DoesNotContain("await fetch", ChromeOrderDispatch.InitiateScript);
        Assert.DoesNotContain(".json(", ChromeOrderDispatch.InitiateScript);
        Assert.DoesNotContain("response.status", ChromeOrderDispatch.InitiateScript);
        Assert.Contains("credentials:'include'", ChromeOrderDispatch.InitiateScript);
        Assert.Contains("Date.now() >= state.cutoff", ChromeOrderDispatch.InitiateScript);
        await dispatch.DisposeAsync();
        await Assert.ThrowsAsync<ObjectDisposedException>(() => dispatch.InitiateAsync(DateTimeOffset.Now, CancellationToken.None));
    }

    [Fact]
    public async Task BridgeException_DoesNotLeakSecretsOrReplay()
    {
        int calls = 0;
        var page = ApiProxy.Create<IPage>((method, _) =>
        {
            calls++;
            if (method.IsGenericMethod) throw new PlaywrightException("fixture-secret");
            return Task.FromResult<JsonElement?>(null);
        });
        await using var dispatch = new ChromeOrderDispatch(page);
        OpeningOrderException failure = await Assert.ThrowsAsync<OpeningOrderException>(() => dispatch.InitiateAsync(DateTimeOffset.Now, CancellationToken.None));
        Assert.DoesNotContain("fixture-secret", failure.ToString()); Assert.Equal(1, calls);
    }

    private sealed class BrowserFake
    {
        internal IPlaywright Playwright { get; }
        internal BrowserTypeLaunchOptions? Launch { get; private set; }
        internal BrowserNewContextOptions? ContextOptions { get; private set; }
        internal int Contexts { get; private set; }
        internal int Popups { get; private set; }
        internal int LoginCloses { get; private set; }
        internal int BrowserCloses { get; private set; }
        internal int TransportNavigations { get; private set; }
        internal bool FailNextRead { get; set; }
        internal bool FailNavigation { get; init; }
        internal bool WaitForLogin { get; init; }
        internal List<string> CdpCommands { get; } = [];
        internal List<JsonElement> RequestArguments { get; } = [];
        internal string InitScript { get; private set; } = "";

        internal BrowserFake()
        {
            var auth = new Dictionary<string, string> { ["authorization"] = "Bearer fixture-session" };
            var request = ApiProxy.Create<IRequest>((method, _) => method.Name switch
            {
                "get_Method" => "GET", "get_Headers" => auth, "AllHeadersAsync" => Task.FromResult(auth),
                _ => throw new InvalidOperationException(method.Name)
            });
            var response = ApiProxy.Create<IResponse>((method, _) => method.Name switch
            {
                "get_Request" => request, "get_Url" => ChromeMofidBrowser.ApiOrigin + "/easy/api/money",
                "get_Status" => 200, "get_FromServiceWorker" => false,
                "get_Headers" => new Dictionary<string, string> { ["content-type"] = "application/json" },
                "BodyAsync" => Task.FromResult(Encoding.UTF8.GetBytes("{\"buyPowerT2\":10000000}")),
                _ => throw new InvalidOperationException(method.Name)
            });
            var cdp = ApiProxy.Create<ICDPSession>((method, args) =>
            {
                if (method.Name == "DetachAsync") return Task.CompletedTask;
                CdpCommands.Add((string)args![0]!);
                return Task.FromResult<JsonElement?>(JsonSerializer.SerializeToElement(new { windowId = 1 }));
            });
            var transport = ApiProxy.Create<IPage>((method, args) =>
            {
                if (method.Name == "get_Url") return ChromeMofidBrowser.ClientOrigin + "/";
                if (method.Name == "AddInitScriptAsync") { InitScript = (string)args![0]!; return Task.FromResult<IAsyncDisposable>(new SeedHandle()); }
                if (method.Name == "GotoAsync") { TransportNavigations++; return Task.FromResult<IResponse?>(null); }
                if (method.Name == "EvaluateAsync" && !method.IsGenericMethod) { Popups++; return Task.FromResult<JsonElement?>(null); }
                if (method.Name == "EvaluateAsync" && method.IsGenericMethod)
                {
                    JsonElement data = JsonSerializer.SerializeToElement(args![1]); RequestArguments.Add(data);
                    bool ok = !FailNextRead; FailNextRead = false;
                    string body = data.GetProperty("url").GetString()!.EndsWith("/draft", StringComparison.Ordinal) ? "[]" : "{\"buyPowerT2\":10000000}";
                    return Task.FromResult(JsonSerializer.SerializeToElement(new { ok, body }));
                }
                throw new InvalidOperationException(method.Name);
            });
            var login = ApiProxy.Create<IPage>((method, args) => method.Name switch
            {
                "get_Url" => ChromeMofidBrowser.ClientOrigin + "/",
                "GotoAsync" => FailNavigation ? Task.FromException<IResponse?>(new PlaywrightException("fixture-secret")) : Task.FromResult<IResponse?>(null),
                "WaitForLoadStateAsync" => Task.CompletedTask,
                "EvaluateAsync" when method.IsGenericMethod => Task.FromResult(new Dictionary<string, string> { ["fixture"] = "fixture-session-storage" }),
                "WaitForResponseAsync" => WaitForResponse(args, response),
                "CloseAsync" => CloseLogin(),
                _ => throw new InvalidOperationException(method.Name)
            });
            var context = ApiProxy.Create<IBrowserContext>((method, args) => method.Name switch
            {
                "add_Request" => null,
                "NewPageAsync" => Task.FromResult(transport),
                "NewCDPSessionAsync" => Task.FromResult(cdp),
                "RunAndWaitForPageAsync" => PopupAsync((Func<Task>)args![0]!, login),
                _ => throw new InvalidOperationException(method.Name)
            });
            var browser = ApiProxy.Create<IBrowser>((method, args) => method.Name switch
            {
                "NewContextAsync" => NewContext(context, args), "CloseAsync" => CloseBrowser(),
                _ => throw new InvalidOperationException(method.Name)
            });
            var browserType = ApiProxy.Create<IBrowserType>((method, args) =>
            {
                Assert.Equal("LaunchAsync", method.Name); Launch = (BrowserTypeLaunchOptions)args![0]!;
                return Task.FromResult(browser);
            });
            Playwright = ApiProxy.Create<IPlaywright>((method, _) => method.Name switch
            { "get_Chromium" => browserType, "Dispose" => null, _ => throw new InvalidOperationException(method.Name) });
        }
        private Task<IResponse> WaitForResponse(object?[]? args, IResponse response)
        {
            Assert.True(((Func<IResponse, bool>)args![0]!)(response));
            return WaitForLogin ? new TaskCompletionSource<IResponse>().Task : Task.FromResult(response);
        }
        private Task CloseLogin() { LoginCloses++; return Task.CompletedTask; }
        private Task CloseBrowser() { BrowserCloses++; return Task.CompletedTask; }
        private Task<IBrowserContext> NewContext(IBrowserContext context, object?[]? args)
        { Contexts++; ContextOptions = (BrowserNewContextOptions)args![0]!; return Task.FromResult(context); }
        private static async Task<IPage> PopupAsync(Func<Task> action, IPage login) { await action(); return login; }
    }

    public class ApiProxy : DispatchProxy
    {
        private Func<MethodInfo, object?[]?, object?> handler = null!;
        internal static T Create<T>(Func<MethodInfo, object?[]?, object?> handler) where T : class
        {
            T result = Create<T, ApiProxy>(); ((ApiProxy)(object)result).handler = handler; return result;
        }
        protected override object? Invoke(MethodInfo? targetMethod, object?[]? args) => handler(targetMethod!, args);
    }
    private sealed class SeedHandle : IAsyncDisposable
    {
        public ValueTask DisposeAsync() => ValueTask.CompletedTask;
    }
}
