using System.Globalization;
using TseExcel.Application.Trading.OpeningOrders;
using TseExcel.Domain.Trading.Orders;
using Xunit;

namespace TseExcel.Application.Tests.Trading.OpeningOrders;

public class OpeningOrderTests
{
    [Theory]
    [InlineData(2, "100.1", "0.001", "0.2", "1", "201")]
    [InlineData(3, "10", "0.01", "2", "4", "146")]
    [InlineData(1, "100000000000000000000", "0.0000000000000000000000000001", "0", "1", "100000000000000000001")]
    [InlineData(1, "0.0000000000000000000000000001", "0", "0", "1", "1")]
    public void FinancialCost_PreservesExactDecimalDigitsBeforeCeiling(long quantity, string price, string rate, string hidden, string size, string expected)
    {
        decimal Parse(string s) => decimal.Parse(s, CultureInfo.InvariantCulture);
        Assert.Equal(Parse(expected), OrderCost.Calculate(quantity, Parse(price), Parse(rate), Parse(hidden), Parse(size)));
    }

    [Theory]
    [InlineData(0, 100, 0, 0, 1)]
    [InlineData(1, 0, 0, 0, 1)]
    [InlineData(1, 1, -1, 0, 1)]
    [InlineData(1, 1, 1, 0, 1)]
    [InlineData(1, 1, 0, -1, 1)]
    [InlineData(1, 1, 0, 0, 0)]
    public void FinancialCost_RejectsInvalidInputs(long quantity, decimal price, decimal rate, decimal hidden, decimal size) =>
        Assert.Throws<ArgumentOutOfRangeException>(() => OrderCost.Calculate(quantity, price, rate, hidden, size));

    [Fact]
    public void NewTerms_PreserveDraftAndDefaultOnlyNullableContractSize()
    {
        OpeningDraft draft = Draft();
        var fees = new InstrumentFees(.001m, .5m, null);
        OrderTerms terms = fees.CreateOrder(draft, 200, 2000);
        Assert.Equal(100, draft.Quantity);
        Assert.Equal(1000m, draft.UnitPriceIrr);
        Assert.Equal(1m, terms.ContractSize);
        Assert.Equal(draft.SymbolIsin, terms.SymbolIsin);
        Assert.Equal(OrderSide.Buy, terms.Side);
        Assert.Throws<ArgumentException>(() => new OrderTerms("123", "Name", OrderSide.Buy, 1, 1, 0, 0, null));
        Assert.Throws<ArgumentOutOfRangeException>(() => fees.CreateOrder(draft, 0, 1));
        Assert.Throws<ArgumentOutOfRangeException>(() => new OrderTerms(draft.SymbolIsin, draft.SymbolName, (OrderSide)4, 1, 1, 0, 0, null));
    }

    [Fact]
    public void Timing_UsesApprovedDefaultsAndCeilingEstimate()
    {
        var settings = new DispatchSettings(DateTimeOffset.Now, DispatchSettings.DefaultDurationSeconds, DispatchSettings.DefaultIntervalMicroseconds);
        Assert.Equal(new TimeOnly(8, 44, 58), DispatchSettings.DefaultStart);
        Assert.Equal(TimeSpan.FromSeconds(5), settings.Duration);
        Assert.Equal(TimeSpan.FromTicks(3500), settings.Interval);
        Assert.Equal(14286, settings.EstimatedAttempts);
        Assert.Throws<ArgumentOutOfRangeException>(() => new DispatchSettings(settings.Start, 0, 350));
        Assert.Throws<ArgumentOutOfRangeException>(() => new DispatchSettings(settings.Start, 5, 0));
        Assert.Throws<ArgumentOutOfRangeException>(() => new DispatchSettings(settings.Start, .00000001m, 350));
        DateTimeOffset local = new DateTimeOffset(2026, 11, 7, 8, 0, 0, TimeSpan.Zero).ToLocalTime();
        var future = TimeOnly.FromDateTime(local.LocalDateTime.AddMinutes(5));
        Assert.Equal(local.AddMinutes(5), DispatchSettings.TodayLocal(future, local));
        Assert.Throws<ArgumentException>(() => DispatchSettings.TodayLocal(TimeOnly.FromDateTime(local.LocalDateTime), local));
    }

    [Fact]
    public async Task Dispatch_IsMonotonicAndDoesNotAwaitOutstandingBrokerResponses()
    {
        var clock = new FakeClock();
        var transport = new FakeDispatch(clock);
        var progress = new DispatchProgress();
        var settings = new DispatchSettings(clock.LocalNow.AddMilliseconds(1), .001m, 350);
        DispatchSummary summary = await new DispatchEngine(clock).RunAsync(settings, transport, progress, CancellationToken.None);
        Assert.Equal(3, summary.InitiatedAttempts);
        Assert.Equal(0, summary.InitiationFailures);
        Assert.True(transport.Disposed);
        Assert.False(transport.BrokerResponse.Task.IsCompleted);
        Assert.Equal(new[] { 10000L, 13500L, 17000L }, transport.MonotonicStarts.Select(x => x.Ticks));
        IReadOnlyList<DispatchRecord> records = progress.Drain();
        Assert.Equal(new long[] { 1, 2, 3 }, records.Select(x => x.Attempt));
        Assert.Equal(transport.EventTimes, records.Select(x => x.Timestamp));
        Assert.All(records, r => Assert.DoesNotContain("accepted", r.Format(), StringComparison.OrdinalIgnoreCase));
        Assert.Empty(progress.Drain());
        Assert.Equal(TimeSpan.Zero, progress.Remaining);
    }

    [Fact]
    public async Task Cancellation_StopsFutureAttemptsAndDisposesTransport()
    {
        var clock = new FakeClock();
        using var cancellation = new CancellationTokenSource();
        var transport = new FakeDispatch(clock) { OnInitiate = count => { if (count == 2) cancellation.Cancel(); } };
        var progress = new DispatchProgress();
        DispatchSummary summary = await new DispatchEngine(clock).RunAsync(new(clock.LocalNow, 5, 350), transport, progress, cancellation.Token);
        Assert.True(summary.Cancelled);
        Assert.Equal(2, summary.InitiatedAttempts);
        Assert.True(transport.Disposed);
    }

    [Fact]
    public async Task CancellationBeforeStartAndExpiredWindow_SendNothing()
    {
        var clock = new FakeClock();
        var transport = new FakeDispatch(clock);
        using var cancellation = new CancellationTokenSource(); cancellation.Cancel();
        DispatchSummary summary = await new DispatchEngine(clock).RunAsync(new(clock.LocalNow.AddSeconds(1), 5, 350), transport, new(), cancellation.Token);
        Assert.True(summary.Cancelled); Assert.Empty(transport.MonotonicStarts);
        var expired = new FakeDispatch(clock);
        await Assert.ThrowsAsync<OpeningOrderException>(() => new DispatchEngine(clock).RunAsync(new(clock.LocalNow.AddSeconds(-10), 5, 350), expired, new(), CancellationToken.None));
        Assert.True(expired.Disposed); Assert.Empty(expired.MonotonicStarts);
    }

    [Fact]
    public async Task LocalFailures_HaveSequentialRecordsAndSeparateStatistics()
    {
        var clock = new FakeClock();
        var transport = new FakeDispatch(clock) { FailFirst = true };
        var progress = new DispatchProgress();
        DispatchSummary summary = await new DispatchEngine(clock).RunAsync(new(clock.LocalNow, .001m, 350), transport, progress, CancellationToken.None);
        Assert.Equal(2, summary.InitiatedAttempts); Assert.Equal(1, summary.InitiationFailures);
        Assert.Equal(new long[] { 1, 2, 3 }, progress.Drain().Select(x => x.Attempt));
        Assert.Throws<ArgumentOutOfRangeException>(() => progress.Drain(0));
    }

    [Fact]
    public async Task UnknownBridgeFailure_IsNeverRetried()
    {
        var clock = new FakeClock();
        var transport = new FakeDispatch(clock) { ThrowOnInitiate = true };
        await Assert.ThrowsAsync<OpeningOrderException>(() => new DispatchEngine(clock).RunAsync(new(clock.LocalNow, 5, 350), transport, new(), CancellationToken.None));
        Assert.Single(transport.MonotonicStarts); Assert.True(transport.Disposed);
    }

    [Fact]
    public void CompactLog_HasSixFractionalDigitsAndOneLineRegardlessOfCurrentCulture()
    {
        var stamp = new DateTimeOffset(2026, 11, 7, 8, 44, 58, TimeSpan.FromHours(3.5)).AddTicks(1240);
        Assert.Equal("08:44:58.000124 | #000001", new DispatchRecord(1, stamp, false).Format());
        Assert.DoesNotContain('\n', new DispatchRecord(2, stamp, true).Format());
    }

    [Fact]
    public async Task Workflow_RequiresConfirmationAndBuyAndRefreshesBeforeDispatch()
    {
        var clock = new FakeClock();
        var broker = new FakeBroker(clock);
        var workflow = new OpeningOrderWorkflow(broker, clock);
        OpeningDraft draft = Draft();
        OrderTerms order = new InstrumentFees(0, 0, null).CreateOrder(draft, 100, 1000);
        var settings = new DispatchSettings(clock.LocalNow.AddSeconds(8), .001m, 350);
        await Assert.ThrowsAsync<OpeningOrderException>(() => workflow.ExecuteConfirmedAsync(draft, order, settings, false, new(), CancellationToken.None));
        await Assert.ThrowsAsync<OpeningOrderException>(() => workflow.ExecuteConfirmedAsync(draft with { Side = OrderSide.Sell }, order, settings, true, new(), CancellationToken.None));
        Assert.Equal(0, broker.Validations);
        DispatchSummary summary = await workflow.ExecuteConfirmedAsync(draft, order, settings, true, new(), CancellationToken.None);
        Assert.Equal(1, broker.Validations); Assert.Equal(TimeSpan.FromSeconds(3), broker.ValidatedAt);
        Assert.Equal(3, summary.InitiatedAttempts);
    }

    [Fact]
    public async Task Workflow_StalePreflightDoesNotOpenTransport()
    {
        var clock = new FakeClock(); var broker = new FakeBroker(clock) { AdvancePreflight = TimeSpan.FromSeconds(10) };
        OpeningDraft draft = Draft(); var order = new InstrumentFees(0, 0, null).CreateOrder(draft, 100, 1000);
        await Assert.ThrowsAsync<OpeningOrderException>(() => new OpeningOrderWorkflow(broker, clock).ExecuteConfirmedAsync(draft, order,
            new(clock.LocalNow.AddSeconds(1), 5, 350), true, new(), CancellationToken.None));
        Assert.Equal(0, broker.OpenCalls);
    }

    private static OpeningDraft Draft() => new("fixture", "IRO1TEST0001", "Fixture", OrderSide.Buy, 100, 1000, 0);

    private sealed class FakeClock : IDispatchClock
    {
        private readonly DateTimeOffset origin = new(2026, 11, 7, 8, 0, 0, TimeSpan.Zero);
        public DateTimeOffset LocalNow => origin + Elapsed;
        public TimeSpan Elapsed { get; set; }
        public Task WaitUntilAsync(TimeSpan deadline, CancellationToken cancellationToken)
        { cancellationToken.ThrowIfCancellationRequested(); if (Elapsed < deadline) Elapsed = deadline; return Task.CompletedTask; }
    }

    private sealed class FakeDispatch(FakeClock clock) : IOrderDispatch
    {
        internal List<TimeSpan> MonotonicStarts { get; } = [];
        internal List<DateTimeOffset> EventTimes { get; } = [];
        internal TaskCompletionSource BrokerResponse { get; } = new();
        internal bool Disposed { get; private set; }
        internal bool FailFirst { get; init; }
        internal bool ThrowOnInitiate { get; init; }
        internal Action<int>? OnInitiate { get; init; }
        public Task<LocalInitiation> InitiateAsync(DateTimeOffset timestamp, CancellationToken cancellationToken)
        {
            cancellationToken.ThrowIfCancellationRequested();
            MonotonicStarts.Add(clock.Elapsed); EventTimes.Add(timestamp.AddTicks(10));
            if (ThrowOnInitiate) throw new OpeningOrderException("Fixture bridge failure.");
            OnInitiate?.Invoke(MonotonicStarts.Count);
            bool failed = FailFirst && MonotonicStarts.Count == 1;
            return Task.FromResult(new LocalInitiation(!failed, EventTimes[^1], failed));
        }
        public ValueTask DisposeAsync() { Disposed = true; return ValueTask.CompletedTask; }
    }

    private sealed class FakeBroker(FakeClock clock) : IOpeningOrderBroker
    {
        internal int Validations { get; private set; }
        internal int OpenCalls { get; private set; }
        internal TimeSpan ValidatedAt { get; private set; }
        internal TimeSpan AdvancePreflight { get; init; }
        public Task ValidateAsync(OpeningDraft draft, OrderTerms order, DispatchSettings settings, CancellationToken cancellationToken)
        { Validations++; ValidatedAt = clock.Elapsed; clock.Elapsed += AdvancePreflight; return Task.CompletedTask; }
        public Task<IOrderDispatch> OpenDispatchAsync(OrderTerms order, DateTimeOffset cutoff, CancellationToken cancellationToken)
        { OpenCalls++; return Task.FromResult<IOrderDispatch>(new FakeDispatch(clock)); }
        public Task AuthenticateAsync(bool refresh, CancellationToken cancellationToken) => throw new NotSupportedException();
        public Task<IReadOnlyList<OpeningDraft>> GetDraftsAsync(CancellationToken cancellationToken) => throw new NotSupportedException();
        public Task<InstrumentFees> GetFeesAsync(OpeningDraft draft, CancellationToken cancellationToken) => throw new NotSupportedException();
        public ValueTask DisposeAsync() => ValueTask.CompletedTask;
    }
}
