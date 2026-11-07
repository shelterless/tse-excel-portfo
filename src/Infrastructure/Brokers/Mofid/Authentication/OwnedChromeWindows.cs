using System.Runtime.InteropServices;
using TseExcel.Application.Trading.OpeningOrders;

namespace TseExcel.Infrastructure.Brokers.Mofid;

internal static class OwnedChromeWindows
{
    // The PID must come from the dedicated browser's CDP connection, never a name/title search.
    internal static Task HideAsync(uint processId, CancellationToken token) => HideAsync(processId, Snapshot,
        window => ShowWindowAsync(window, 0), IsWindowVisible, token);

    internal static async Task HideAsync(uint processId, Func<IReadOnlyList<(nint Window, uint Process)>> snapshot,
        Func<nint, bool> hide, Func<nint, bool> visible, CancellationToken token)
    {
        if (processId == 0) throw new OpeningOrderException("Owned Chrome process could not be verified.", OpeningOrderError.Authentication);
        nint[] windows = snapshot().Where(x => x.Process == processId).Select(x => x.Window).ToArray();
        foreach (nint window in windows)
        {
            token.ThrowIfCancellationRequested();
            if (visible(window) && !hide(window)) throw Failure();
        }
        // ShowWindowAsync posts to Chrome's UI thread. Verify its effect without blocking that thread.
        for (int check = 0; check < 50; check++)
        {
            token.ThrowIfCancellationRequested();
            if (windows.All(window => !visible(window))) return;
            await Task.Delay(20, token).ConfigureAwait(false);
        }
        throw Failure();
    }

    private static OpeningOrderException Failure() => new("Owned Chrome windows could not be hidden.", OpeningOrderError.Authentication);

    private static IReadOnlyList<(nint Window, uint Process)> Snapshot()
    {
        var windows = new List<(nint, uint)>();
        if (!EnumWindows((window, _) => { GetWindowThreadProcessId(window, out uint process); windows.Add((window, process)); return true; }, 0))
            throw Failure();
        return windows;
    }

    private delegate bool EnumWindow(nint window, nint parameter);
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool EnumWindows(EnumWindow callback, nint parameter);
    [DllImport("user32.dll")]
    private static extern uint GetWindowThreadProcessId(nint window, out uint processId);
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool ShowWindowAsync(nint window, int command);
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool IsWindowVisible(nint window);
}
