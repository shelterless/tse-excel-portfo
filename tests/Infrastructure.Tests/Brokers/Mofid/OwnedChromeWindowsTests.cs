using TseExcel.Application.Trading.OpeningOrders;
using TseExcel.Infrastructure.Brokers.Mofid;
using Xunit;

namespace TseExcel.Infrastructure.Tests.Brokers.Mofid;

public class OwnedChromeWindowsTests
{
    [Fact]
    public async Task Hide_OnlyTouchesWindowsFromVerifiedOwnedProcessIncludingMinimizedWindows()
    {
        var hidden = new List<nint>(); var visible = new HashSet<nint> { 1, 2, 3 };
        await OwnedChromeWindows.HideAsync(42, () => new (nint, uint)[] { (1, 42), (2, 42), (3, 999), (4, 42) },
            window => { hidden.Add(window); visible.Remove(window); return true; }, visible.Contains, CancellationToken.None);
        Assert.Equal(new nint[] { 1, 2 }, hidden); Assert.Equal(new nint[] { 3 }, visible);
    }

    [Fact]
    public async Task Hide_RejectsUnverifiedProcessAndHonorsCancellationAndNativeFailure()
    {
        IReadOnlyList<(nint, uint)> Windows() => new (nint, uint)[] { (1, 42) };
        await Assert.ThrowsAsync<OpeningOrderException>(() => OwnedChromeWindows.HideAsync(0, Windows, _ => throw new Exception(), _ => true, CancellationToken.None));
        using var cancellation = new CancellationTokenSource(); cancellation.Cancel();
        await Assert.ThrowsAnyAsync<OperationCanceledException>(() => OwnedChromeWindows.HideAsync(42, Windows, _ => throw new Exception(), _ => true, cancellation.Token));
        var error = await Assert.ThrowsAsync<OpeningOrderException>(() => OwnedChromeWindows.HideAsync(42, Windows, _ => false, _ => true, CancellationToken.None));
        Assert.Equal(OpeningOrderError.Authentication, error.Error);
    }
}
