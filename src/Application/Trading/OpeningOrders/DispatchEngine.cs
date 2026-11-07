using System.Collections.Concurrent;
using System.Diagnostics;
using System.Globalization;

namespace TseExcel.Application.Trading.OpeningOrders;

public interface IDispatchClock
{
    DateTimeOffset LocalNow { get; }
    TimeSpan Elapsed { get; }
    Task WaitUntilAsync(TimeSpan deadline, CancellationToken cancellationToken);
}

public sealed class SystemDispatchClock : IDispatchClock
{
    private readonly long origin = Stopwatch.GetTimestamp();
    public DateTimeOffset LocalNow => DateTimeOffset.Now;
    public TimeSpan Elapsed => Stopwatch.GetElapsedTime(origin);

    public async Task WaitUntilAsync(TimeSpan deadline, CancellationToken cancellationToken)
    {
        while (Elapsed < deadline)
        {
            cancellationToken.ThrowIfCancellationRequested();
            TimeSpan remaining = deadline - Elapsed;
            if (remaining > TimeSpan.FromMilliseconds(3))
                await Task.Delay(remaining - TimeSpan.FromMilliseconds(2), cancellationToken).ConfigureAwait(false);
            else Thread.SpinWait(64);
        }
        cancellationToken.ThrowIfCancellationRequested();
    }
}

public sealed record DispatchRecord(long Attempt, DateTimeOffset Timestamp, bool LocalFailure)
{
    public string Format() => Timestamp.ToString("HH:mm:ss.ffffff", CultureInfo.InvariantCulture) +
        " | #" + Attempt.ToString("D6", CultureInfo.InvariantCulture) + (LocalFailure ? " | خطای آغاز" : "");
}

public sealed record DispatchSummary(long InitiatedAttempts, long InitiationFailures, TimeSpan Elapsed, bool Cancelled);

public sealed class DispatchProgress
{
    private readonly ConcurrentQueue<DispatchRecord> records = new();
    private long initiated, failures, sequence, elapsedTicks, remainingTicks;
    public long InitiatedAttempts => Interlocked.Read(ref initiated);
    public long InitiationFailures => Interlocked.Read(ref failures);
    public TimeSpan Elapsed => TimeSpan.FromTicks(Interlocked.Read(ref elapsedTicks));
    public TimeSpan Remaining => TimeSpan.FromTicks(Math.Max(0, Interlocked.Read(ref remainingTicks)));
    public IReadOnlyList<DispatchRecord> Drain(int maximum = 1000)
    {
        if (maximum <= 0) throw new ArgumentOutOfRangeException(nameof(maximum));
        var result = new List<DispatchRecord>();
        while (result.Count < maximum && records.TryDequeue(out DispatchRecord? record)) result.Add(record);
        return result;
    }
    internal void Update(TimeSpan elapsed, TimeSpan remaining)
    {
        Interlocked.Exchange(ref elapsedTicks, elapsed.Ticks);
        Interlocked.Exchange(ref remainingTicks, remaining.Ticks);
    }
    internal void Add(LocalInitiation result)
    {
        if (!result.Initiated && !result.LocalFailure) return;
        long number = Interlocked.Increment(ref sequence);
        if (result.Initiated) Interlocked.Increment(ref initiated);
        if (result.LocalFailure) Interlocked.Increment(ref failures);
        records.Enqueue(new(number, result.Timestamp, result.LocalFailure));
    }
}

public sealed class DispatchEngine(IDispatchClock clock)
{
    public Task<DispatchSummary> RunAsync(DispatchSettings settings, IOrderDispatch dispatch,
        DispatchProgress progress, CancellationToken cancellationToken) => Task.Run(async () =>
    {
        TimeSpan requestedAt = clock.Elapsed + (settings.Start - clock.LocalNow);
        TimeSpan cutoff = requestedAt + settings.Duration;
        bool cancelled = false;
        TimeSpan elapsed = TimeSpan.Zero;
        try
        {
            // Countdown and intervals share a monotonic timebase after this wall-clock conversion.
            while (clock.Elapsed < requestedAt)
            {
                progress.Update(TimeSpan.Zero, requestedAt - clock.Elapsed);
                await clock.WaitUntilAsync(Min(requestedAt, clock.Elapsed + TimeSpan.FromMilliseconds(25)), cancellationToken).ConfigureAwait(false);
            }
            if (clock.Elapsed >= cutoff) throw new OpeningOrderException("Dispatch window expired before initiation.");
            while (clock.Elapsed < cutoff)
            {
                cancellationToken.ThrowIfCancellationRequested();
                LocalInitiation result = await dispatch.InitiateAsync(clock.LocalNow, cancellationToken).ConfigureAwait(false);
                progress.Add(result);
                elapsed = clock.Elapsed - requestedAt;
                progress.Update(elapsed, cutoff - clock.Elapsed);
                // Start the minimum gap after local bridge acknowledgement, so bridge latency cannot compress it.
                await clock.WaitUntilAsync(Min(cutoff, clock.Elapsed + settings.Interval), cancellationToken).ConfigureAwait(false);
            }
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested) { cancelled = true; }
        finally
        {
            elapsed = clock.Elapsed > requestedAt ? clock.Elapsed - requestedAt : TimeSpan.Zero;
            progress.Update(elapsed, TimeSpan.Zero);
            await dispatch.DisposeAsync().ConfigureAwait(false);
        }
        return new DispatchSummary(progress.InitiatedAttempts, progress.InitiationFailures, elapsed, cancelled);
    }, CancellationToken.None);

    private static TimeSpan Min(TimeSpan a, TimeSpan b) => a < b ? a : b;
}
