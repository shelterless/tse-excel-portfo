using Microsoft.Playwright;
using TseExcel.Application.Trading.OpeningOrders;

namespace TseExcel.Infrastructure.Brokers.Mofid;

internal static class MofidBrowserDriver
{
    private static readonly SemaphoreSlim DriverGate = new(1, 1);
    internal const string SearchPathVariable = "PLAYWRIGHT_DRIVER_SEARCH_PATH";

    internal static async Task<IPlaywright> CreateAsync(string directory, Func<Task<IPlaywright>>? create = null)
    {
        // Packed Excel-DNA assemblies have no usable Assembly.Location. Use the XLL directory explicitly.
        if (!Path.IsPathFullyQualified(directory) ||
            !File.Exists(Path.Combine(directory, ".playwright", "node", "win32_x64", "node.exe")) ||
            !File.Exists(Path.Combine(directory, ".playwright", "package", "cli.js")))
            throw new OpeningOrderException("The packaged browser driver is missing beside the XLL.");
        await DriverGate.WaitAsync().ConfigureAwait(false);
        string? previous = Environment.GetEnvironmentVariable(SearchPathVariable);
        try
        {
            Environment.SetEnvironmentVariable(SearchPathVariable, directory);
            return await (create ?? Playwright.CreateAsync)().ConfigureAwait(false);
        }
        finally
        {
            Environment.SetEnvironmentVariable(SearchPathVariable, previous);
            DriverGate.Release();
        }
    }
}
