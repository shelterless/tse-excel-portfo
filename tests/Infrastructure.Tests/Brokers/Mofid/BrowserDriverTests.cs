using Microsoft.Playwright;
using TseExcel.Application.Trading.OpeningOrders;
using TseExcel.Infrastructure.Brokers.Mofid;
using Xunit;

namespace TseExcel.Infrastructure.Tests.Brokers.Mofid;

public class BrowserDriverTests
{
    [Fact]
    public async Task PackedAssemblyDriverLookup_UsesExplicitDirectoryAndRestoresProcessEnvironment()
    {
        string? previous = Environment.GetEnvironmentVariable(MofidBrowserDriver.SearchPathVariable);
        var playwright = ChromeSessionTests.ApiProxy.Create<IPlaywright>((_, _) => null);
        IPlaywright result = await MofidBrowserDriver.CreateAsync(AppContext.BaseDirectory, () =>
        {
            Assert.Equal(AppContext.BaseDirectory, Environment.GetEnvironmentVariable(MofidBrowserDriver.SearchPathVariable));
            return Task.FromResult(playwright);
        });
        Assert.Same(playwright, result);
        Assert.Equal(previous, Environment.GetEnvironmentVariable(MofidBrowserDriver.SearchPathVariable));
        await Assert.ThrowsAsync<InvalidOperationException>(() => MofidBrowserDriver.CreateAsync(AppContext.BaseDirectory,
            () => throw new InvalidOperationException("Fixture startup failure.")));
        Assert.Equal(previous, Environment.GetEnvironmentVariable(MofidBrowserDriver.SearchPathVariable));
        await Assert.ThrowsAsync<OpeningOrderException>(() => MofidBrowserDriver.CreateAsync("relative-driver-path"));
    }
}
