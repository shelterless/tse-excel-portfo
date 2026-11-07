using System.Text.Json;
using Microsoft.Playwright;
using TseExcel.Infrastructure.Brokers.Mofid;
using Xunit;
using static TseExcel.Infrastructure.Tests.Brokers.Mofid.ChromeSessionTests;

namespace TseExcel.Infrastructure.Tests.Brokers.Mofid;

public class OfflineChromeAcceptanceTests
{
    [Fact]
    [Trait("Category", "OfflineChrome")]
    public async Task OwnedChrome_ClosesLoginAndAuxiliaryPagesHidesTransportAndRetainsAuthenticatedContext()
    {
        // Real installed Chrome and Win32 visibility; every context request is fulfilled locally.
        // No credentials, brokerage connections, real orders or personal Chrome profiles are used.
        using IPlaywright real = await Playwright.CreateAsync();
        IBrowser? owned = null;
        IBrowserContext? authenticated = null;
        IPage? login = null;
        IPage? auxiliary = null;
        int moneyReads = 0, hides = 0;
        async Task<IBrowserContext> NewContext(BrowserNewContextOptions options)
        {
            authenticated = await owned!.NewContextAsync(options);
            await authenticated.RouteAsync("**/*", async route =>
            {
                string url = route.Request.Url;
                if (url == ChromeMofidBrowser.ClientOrigin + "/")
                {
                    await route.FulfillAsync(new() { ContentType = "text/html", Body = """
                        <!doctype html><title>Offline acceptance fixture</title>
                        <script>
                        if (!sessionStorage.getItem('fixture-login')) {
                          sessionStorage.setItem('fixture-login', 'verified');
                          window.open('about:blank', '_blank', 'popup,width=300,height=200');
                        }
                        fetch('https://api-mts.orbis.easytrader.ir/easy/api/money', {credentials:'include'});
                        </script>
                        """ });
                    return;
                }
                if (url == ChromeMofidBrowser.ApiOrigin + "/easy/api/money")
                {
                    Interlocked.Increment(ref moneyReads);
                    await route.FulfillAsync(new() { ContentType = "application/json", Body = "{\"buyPowerT2\":10000000}",
                        Headers = new Dictionary<string, string> { ["Access-Control-Allow-Origin"] = ChromeMofidBrowser.ClientOrigin,
                            ["Access-Control-Allow-Credentials"] = "true" } });
                    return;
                }
                if (url == ChromeMofidBrowser.ApiOrigin + "/easy/api/draft")
                {
                    await route.FulfillAsync(new() { ContentType = "application/json", Body = "[]",
                        Headers = new Dictionary<string, string> { ["Access-Control-Allow-Origin"] = ChromeMofidBrowser.ClientOrigin,
                            ["Access-Control-Allow-Credentials"] = "true" } });
                    return;
                }
                // Browser fetches with non-simple headers require an offline CORS preflight.
                if (route.Request.Method == "OPTIONS")
                {
                    await route.FulfillAsync(new() { Status = 204, Headers = new Dictionary<string, string>
                    { ["Access-Control-Allow-Origin"] = ChromeMofidBrowser.ClientOrigin, ["Access-Control-Allow-Credentials"] = "true",
                        ["Access-Control-Allow-Headers"] = "cache-control", ["Access-Control-Allow-Methods"] = "GET" } });
                    return;
                }
                await route.AbortAsync();
            });
            authenticated.Page += (_, page) => { if (login is null && authenticated.Pages.Count > 1) login = page; else if (authenticated.Pages.Count > 2) auxiliary = page; };
            return authenticated;
        }
        async Task<IBrowser> Launch(BrowserTypeLaunchOptions options)
        {
            owned = await real.Chromium.LaunchAsync(options);
            return ApiProxy.Create<IBrowser>((method, args) => method.Name == "NewContextAsync"
                ? NewContext((BrowserNewContextOptions)args![0]!) : method.Invoke(owned, args));
        }
        var type = ApiProxy.Create<IBrowserType>((method, args) => method.Name == "LaunchAsync"
            ? Launch((BrowserTypeLaunchOptions)args![0]!) : method.Invoke(real.Chromium, args));
        var playwright = ApiProxy.Create<IPlaywright>((method, args) => method.Name switch
        { "get_Chromium" => type, "Dispose" => null, _ => method.Invoke(real, args) });
        await using var browser = new ChromeMofidBrowser(() => Task.FromResult(playwright), async (process, token) =>
        {
            await OwnedChromeWindows.HideAsync(process, token);
            hides++;
        });
        await browser.AuthenticateAsync(false, CancellationToken.None);
        Assert.NotNull(login); Assert.True(login.IsClosed);
        Assert.NotNull(auxiliary); Assert.True(auxiliary.IsClosed);
        Assert.Equal(1, hides); Assert.NotNull(authenticated);
        IPage transport = Assert.Single(authenticated.Pages);
        Assert.Equal("verified", await transport.EvaluateAsync<string>("() => sessionStorage.getItem('fixture-login')"));
        Assert.Equal(JsonValueKind.Array, (await browser.ReadAsync(MofidRead.Drafts, null, CancellationToken.None)).ValueKind);
        await browser.AuthenticateAsync(false, CancellationToken.None);
        Assert.Equal(1, hides); Assert.Single(owned!.Contexts); Assert.True(moneyReads >= 3);
    }
}
