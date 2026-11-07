using System.Text.Json;
using Microsoft.Playwright;
using TseExcel.Application.Trading.OpeningOrders;

namespace TseExcel.Infrastructure.Brokers.Mofid;

internal sealed class ChromeOrderDispatch(IPage page) : IOrderDispatch
{
    private bool disposed;
    internal const string InitiateScript = """
        () => {
          const state = window.__tseOpening;
          const localMicros = () => Math.round((performance.timeOrigin + performance.now()) * 1000);
          if (!state || state.cancelled || Date.now() >= state.cutoff) return {initiated:false, failed:false, timestamp:localMicros()};
          try {
            const body = state.payload.replace('"__TSE_LOCAL_TIMESTAMP__"', JSON.stringify(new Date().toLocaleString('en-US')));
            const timestamp = localMicros();
            if (state.cancelled || Date.now() >= state.cutoff) return {initiated:false, failed:false, timestamp};
            // This promise is deliberately detached. No status, body, broker ID or result is inspected.
            void fetch(state.url, {method:'POST', headers:state.headers, body, credentials:'include',
              redirect:'error', cache:'no-store'})
              .then(response => response.body?.cancel(), () => {})
              .catch(() => {});
            return {initiated:true, failed:false, timestamp};
          } catch { return {initiated:false, failed:true, timestamp:localMicros()}; }
        }
        """;

    public async Task<LocalInitiation> InitiateAsync(DateTimeOffset timestamp, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (disposed) throw new ObjectDisposedException(nameof(ChromeOrderDispatch));
        try
        {
            // Await only the immediate local bridge acknowledgement, never a fetch response.
            JsonElement result = await page.EvaluateAsync<JsonElement>(InitiateScript).WaitAsync(TimeSpan.FromSeconds(15)).ConfigureAwait(false);
            long microseconds = result.GetProperty("timestamp").GetInt64();
            return new(result.GetProperty("initiated").GetBoolean(),
                DateTimeOffset.FromUnixTimeMilliseconds(microseconds / 1000).AddTicks(microseconds % 1000 * 10).ToLocalTime(),
                result.GetProperty("failed").GetBoolean());
        }
        catch (Exception exception) when (exception is PlaywrightException or TimeoutException or JsonException or KeyNotFoundException or InvalidOperationException)
        {
            // An uncertain bridge failure stops the entire window. It must never replay this attempt.
            throw new OpeningOrderException("Dispatch bridge interrupted; broker outcomes remain unknown. Do not replay.");
        }
    }

    internal const string StopScript = "() => { const s = window.__tseOpening; if (s) { s.stop(); clearTimeout(s.timer); delete window.__tseOpening; } }";

    public async ValueTask DisposeAsync()
    {
        if (disposed) return;
        disposed = true;
        try
        {
            await page.EvaluateAsync(StopScript)
                .WaitAsync(TimeSpan.FromSeconds(5)).ConfigureAwait(false);
        }
        catch (Exception exception) when (exception is PlaywrightException or TimeoutException)
        {
            throw new OpeningOrderException("Dispatch cleanup could not be verified; broker outcomes remain unknown.");
        }
    }
}
