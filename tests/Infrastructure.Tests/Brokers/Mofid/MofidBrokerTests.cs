using System.Text.Json;
using TseExcel.Application.Trading.OpeningOrders;
using TseExcel.Domain.Trading.Orders;
using TseExcel.Infrastructure.Brokers.Mofid;
using Xunit;

namespace TseExcel.Infrastructure.Tests.Brokers.Mofid;

public class MofidBrokerTests
{
    internal const string DraftJson = """
        [{"id":"9007199254740993","symbolIsin":"IRO1TEST0001","symbolName":"Fixture","side":0,"quantity":1000,"price":2000,"validityType":0}]
        """;
    internal const string SymbolJson = """
        {"symbols":[{"symbolIsin":"IRO1TEST0001","symbolName":"Fixture","buyCommission":0.001,"hidePrice":0,"csize":null,
        "isActive":true,"canBuy":true,"marketUnit":3,"minDealablePrice":1,"minDealableCount":1,
        "minValidBuyVolume":1,"maxValidBuyVolume":100000,"tradingTimeType":1}]}
        """;
    internal const string MarketJson = """
        [{"symbolIsin":"IRO1TEST0001","stateCode":"A","lowAllowedPrice":100,"highAllowedPrice":10000}]
        """;
    internal const string CalendarJson = """
        {"items":[{"tradingTimeType":1,"days":[1,2,3,4,5],"startPreTradingTime":"08:45","endPreTradingTime":"09:00",
        "startTradingTime":"09:00","endTradingTime":"12:30"}]}
        """;
    internal const string SessionJson = """
        {"serverTime":"2026-11-07T08:44:50+03:30","startSessionTimeStamp":"2026-11-07T08:00:00+03:30"}
        """;
    internal static readonly DateTimeOffset Now = new(2026, 11, 7, 8, 44, 50, TimeSpan.FromHours(3.5));
    internal static DispatchSettings Settings() => new(Now.AddSeconds(8), 5, 350);
    internal static OpeningDraft Draft() => new("fixture", "IRO1TEST0001", "Fixture", OrderSide.Buy, 1000, 2000, 0);
    internal static OrderTerms Order() => new InstrumentFees(.001m, 0, null).CreateOrder(Draft(), 1000, 2000);

    [Fact]
    public async Task DraftRead_PreservesExactIdsSidesAndSnapshotWithoutMutatingBrokerDrafts()
    {
        var browser = new FakeBrowser();
        browser.Payloads[MofidRead.Drafts] = DraftJson.Replace("\"side\":0", "\"side\":1");
        await using var broker = new MofidOpeningOrderBroker(browser, new FixedTime());
        IReadOnlyList<OpeningDraft> drafts = await broker.GetDraftsAsync(CancellationToken.None);
        OpeningDraft draft = Assert.Single(drafts);
        Assert.Equal("9007199254740993", draft.Id); Assert.Equal(OrderSide.Sell, draft.Side);
        Assert.Equal(1000, draft.Quantity); Assert.Equal(2000, draft.UnitPriceIrr);
        Assert.Equal(new[] { MofidRead.Drafts }, browser.Reads);
        Assert.Equal(1, browser.AuthCalls);
        Assert.Equal(0, browser.Dispatches);
    }

    [Theory]
    [InlineData("{}")]
    [InlineData("[{}]")]
    [InlineData("[{\"id\":\"x\",\"symbolIsin\":\"IRO1TEST0001\",\"symbolName\":\"Fixture\",\"side\":4,\"quantity\":1,\"price\":1}]")]
    public async Task DraftRead_RejectsMalformedOrUnknownSide(string json)
    {
        var browser = new FakeBrowser(); browser.Payloads[MofidRead.Drafts] = json;
        await using var broker = new MofidOpeningOrderBroker(browser, new FixedTime());
        await Assert.ThrowsAsync<OpeningOrderException>(() => broker.GetDraftsAsync(CancellationToken.None));
        Assert.Equal(0, browser.Dispatches);
    }

    [Theory]
    [InlineData("\"buyCommission\":0.001", "\"buyCommission\":null")]
    [InlineData("\"buyCommission\":0.001", "\"buyCommission\":1")]
    [InlineData("\"hidePrice\":0", "\"hidePrice\":-1")]
    [InlineData("\"csize\":null", "\"csize\":0")]
    [InlineData("\"buyCommission\":0.001,", "")]
    public async Task Fees_RejectMissingOrInvalidMetadata(string before, string after)
    {
        var browser = new FakeBrowser(); browser.Payloads[MofidRead.Symbols] = SymbolJson.Replace(before, after);
        await using var broker = new MofidOpeningOrderBroker(browser, new FixedTime());
        await Assert.ThrowsAsync<OpeningOrderException>(() => broker.GetFeesAsync(Draft(), CancellationToken.None));
    }

    [Fact]
    public async Task FreshPreflight_UsesVerifiedReadsAndCreatesOnlyNewBuyPayload()
    {
        var browser = new FakeBrowser();
        await using var broker = new MofidOpeningOrderBroker(browser, new FixedTime());
        var draft = Draft(); var order = Order(); var settings = Settings();
        await broker.ValidateAsync(draft, order, settings, CancellationToken.None);
        await using IOrderDispatch dispatch = await broker.OpenDispatchAsync(order, settings.Start + settings.Duration, CancellationToken.None);
        Assert.Equal(new[] { MofidRead.Symbols, MofidRead.Market, MofidRead.Money, MofidRead.Calendar, MofidRead.Session }, browser.Reads);
        JsonElement payload = JsonDocument.Parse(browser.OrderPayload!).RootElement.GetProperty("order");
        Assert.Equal(0, payload.GetProperty("side").GetInt32());
        Assert.Equal(0, payload.GetProperty("validityType").GetInt32());
        Assert.Equal(1, payload.GetProperty("orderModelType").GetInt32());
        Assert.Equal(34, payload.GetProperty("orderFrom").GetInt32());
        Assert.Equal(2_002_000m, payload.GetProperty("totalValue").GetDecimal());
        Assert.False(payload.TryGetProperty("id", out _));
        Assert.Equal(1000, draft.Quantity);
        await Assert.ThrowsAsync<OpeningOrderException>(() => broker.OpenDispatchAsync(order, settings.Start + settings.Duration, CancellationToken.None));
    }

    [Theory]
    [InlineData((int)MofidRead.Symbols, "\"buyCommission\":0.001", "\"buyCommission\":0.002")]
    [InlineData((int)MofidRead.Symbols, "\"canBuy\":true", "\"canBuy\":false")]
    [InlineData((int)MofidRead.Symbols, "\"marketUnit\":3", "\"marketUnit\":99")]
    [InlineData((int)MofidRead.Market, "\"stateCode\":\"A\"", "\"stateCode\":\"H\"")]
    [InlineData((int)MofidRead.Market, "\"lowAllowedPrice\":100", "\"lowAllowedPrice\":3000")]
    [InlineData((int)MofidRead.Money, "10000000", "0")]
    [InlineData((int)MofidRead.Session, "2026-11-07", "2026-11-06")]
    [InlineData((int)MofidRead.Calendar, "\"days\":[1,2,3,4,5]", "\"days\":[2,3]")]
    public async Task Preflight_InvalidOrChangedEvidenceCannotReachDispatch(int read, string before, string after)
    {
        var browser = new FakeBrowser(); var kind = (MofidRead)read;
        browser.Payloads[kind] = browser.Payloads[kind].Replace(before, after);
        await using var broker = new MofidOpeningOrderBroker(browser, new FixedTime());
        await Assert.ThrowsAsync<OpeningOrderException>(() => broker.ValidateAsync(Draft(), Order(), Settings(), CancellationToken.None));
        Assert.Equal(0, browser.Dispatches);
    }

    [Fact]
    public async Task SellAndUnvalidatedAndStaleOrdersAreGatedBeforeTransport()
    {
        var browser = new FakeBrowser(); var time = new FixedTime();
        await using var broker = new MofidOpeningOrderBroker(browser, time);
        OrderTerms buy = Order(); OpeningDraft sell = Draft() with { Side = OrderSide.Sell };
        await Assert.ThrowsAsync<OpeningOrderException>(() => broker.GetFeesAsync(sell, CancellationToken.None));
        await Assert.ThrowsAsync<OpeningOrderException>(() => broker.ValidateAsync(sell, buy, Settings(), CancellationToken.None));
        await Assert.ThrowsAsync<OpeningOrderException>(() => broker.OpenDispatchAsync(buy, Settings().Start + Settings().Duration, CancellationToken.None));
        Assert.Throws<OpeningOrderException>(() => MofidOpeningOrderBroker.Payload(new InstrumentFees(0, 0, null).CreateOrder(sell, 1000, 2000)));
        await broker.ValidateAsync(Draft(), buy, Settings(), CancellationToken.None);
        time.Advance(TimeSpan.FromSeconds(16));
        await Assert.ThrowsAsync<OpeningOrderException>(() => broker.OpenDispatchAsync(buy, Settings().Start + Settings().Duration, CancellationToken.None));
        Assert.Equal(0, browser.Dispatches);
    }

    [Fact]
    public void Calendar_RequiresVerifiedOverlapButAllowsApprovedPreopeningStart()
    {
        using JsonDocument all = JsonDocument.Parse(SymbolJson), calendar = JsonDocument.Parse(CalendarJson), session = JsonDocument.Parse(SessionJson);
        JsonElement symbol = all.RootElement.GetProperty("symbols")[0];
        MofidOpeningOrderBroker.ValidateCalendar(symbol, calendar.RootElement, session.RootElement, Settings());
        Assert.Throws<OpeningOrderException>(() => MofidOpeningOrderBroker.ValidateCalendar(symbol, calendar.RootElement, session.RootElement,
            new(Now.AddMinutes(-10), 5, 350)));
    }

    [Fact]
    public void ReadContracts_UseOnlyVerifiedEndpointsAndBodies()
    {
        var symbols = ChromeMofidBrowser.ReadRequest(MofidRead.Symbols, null);
        Assert.Equal("POST", symbols.Method); Assert.Equal("/symbols/api/symbols/all", symbols.Path);
        Assert.Equal("{\"hash\":\"null\"}", symbols.Body);
        Assert.Equal("[\"IRO1TEST0001\"]", ChromeMofidBrowser.ReadRequest(MofidRead.Market, "IRO1TEST0001").Body);
        Assert.Throws<OpeningOrderException>(() => ChromeMofidBrowser.ReadRequest((MofidRead)100, null));
        Assert.Throws<OpeningOrderException>(() => ChromeMofidBrowser.ReadRequest(MofidRead.Market, null));
    }

    internal sealed class FixedTime : TimeProvider
    {
        private TimeSpan elapsed;
        public override DateTimeOffset GetUtcNow() => (Now + elapsed).ToUniversalTime();
        public override long GetTimestamp() => elapsed.Ticks;
        public override long TimestampFrequency => TimeSpan.TicksPerSecond;
        internal void Advance(TimeSpan value) => elapsed += value;
    }

    internal sealed class FakeBrowser : IMofidBrowser
    {
        internal Dictionary<MofidRead, string> Payloads { get; } = new()
        {
            [MofidRead.Drafts] = DraftJson, [MofidRead.Symbols] = SymbolJson, [MofidRead.Market] = MarketJson,
            [MofidRead.Money] = "{\"buyPowerT2\":10000000}", [MofidRead.Calendar] = CalendarJson, [MofidRead.Session] = SessionJson
        };
        internal List<MofidRead> Reads { get; } = [];
        internal int AuthCalls { get; private set; }
        internal int Dispatches { get; private set; }
        internal string? OrderPayload { get; private set; }
        public Task AuthenticateAsync(bool refresh, CancellationToken cancellationToken) { AuthCalls++; return Task.CompletedTask; }
        public Task<JsonElement> ReadAsync(MofidRead read, string? symbolIsin, CancellationToken cancellationToken)
        {
            cancellationToken.ThrowIfCancellationRequested(); Reads.Add(read);
            using JsonDocument document = JsonDocument.Parse(Payloads[read]);
            return Task.FromResult(document.RootElement.Clone());
        }
        public Task<IOrderDispatch> OpenDispatchAsync(string payload, DateTimeOffset cutoff, CancellationToken cancellationToken)
        { Dispatches++; OrderPayload = payload; return Task.FromResult<IOrderDispatch>(new FakeDispatch()); }
        public ValueTask DisposeAsync() => ValueTask.CompletedTask;
    }
    private sealed class FakeDispatch : IOrderDispatch
    {
        public Task<LocalInitiation> InitiateAsync(DateTimeOffset timestamp, CancellationToken cancellationToken) => Task.FromResult(new LocalInitiation(true, timestamp, false));
        public ValueTask DisposeAsync() => ValueTask.CompletedTask;
    }
}
