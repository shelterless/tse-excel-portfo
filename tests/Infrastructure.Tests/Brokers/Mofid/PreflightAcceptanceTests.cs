using System.Globalization;
using System.Text.Json;
using TseExcel.Application.Trading.OpeningOrders;
using TseExcel.Infrastructure.Brokers.Mofid;
using Xunit;
using static TseExcel.Infrastructure.Tests.Brokers.Mofid.MofidBrokerTests;

namespace TseExcel.Infrastructure.Tests.Brokers.Mofid;

public class PreflightAcceptanceTests
{
    [Theory]
    [InlineData("\"2026-11-07T08:44:50+03:30\"")]
    [InlineData("\"2026-11-07T08:44:50\"")]
    [InlineData("\"2026-11-07T05:14:50.123Z\"")]
    [InlineData("epoch")]
    public async Task SessionDates_UseVerifiedIsoOrEpochMillisecondsWithoutHostTimezoneAssumptions(string token)
    {
        var browser = new FakeBrowser();
        browser.Payloads[MofidRead.Session] = Replace(SessionJson, "serverTime", token == "epoch" ? Now.ToUnixTimeMilliseconds().ToString(CultureInfo.InvariantCulture) : token);
        await using var broker = new MofidOpeningOrderBroker(browser, new FixedTime());
        await broker.ValidateAsync(Draft(), Order(), Settings(), CancellationToken.None);
        Assert.Equal(0, browser.Dispatches);
    }

    [Theory]
    [InlineData("null", OpeningOrderError.MalformedResponse)]
    [InlineData("true", OpeningOrderError.MalformedResponse)]
    [InlineData("\"08:44\"", OpeningOrderError.MalformedResponse)]
    [InlineData("\"not a date\"", OpeningOrderError.MalformedResponse)]
    [InlineData("9223372036854775807", OpeningOrderError.MalformedResponse)]
    [InlineData("\"2026-11-06T08:44:50+03:30\"", OpeningOrderError.StalePreflight)]
    public async Task InvalidSessionDates_FailAsSessionContractErrorsRatherThanFinancialErrors(string token, OpeningOrderError category)
    {
        var browser = new FakeBrowser(); browser.Payloads[MofidRead.Session] = Replace(SessionJson, "serverTime", token);
        await using var broker = new MofidOpeningOrderBroker(browser, new FixedTime());
        var error = await Assert.ThrowsAsync<OpeningOrderException>(() => broker.ValidateAsync(Draft(), Order(), Settings(), CancellationToken.None));
        Assert.Equal(category, error.Error); Assert.Equal(OpeningOrderStage.Session, error.Stage);
        Assert.Equal(0, browser.Dispatches);
    }
    [Theory]
    [InlineData("minDealablePrice", "\"0.000000000000000001\"")]
    [InlineData("minDealableCount", "\"1\"")]
    [InlineData("minValidBuyVolume", "\"1\"")]
    [InlineData("maxValidBuyVolume", "\"100000\"")]
    public async Task ReferenceFinancialStrings_PassExactPreflightAfterSuccessfulDetails(string field, string token)
    {
        var browser = new FakeBrowser();
        browser.Payloads[MofidRead.Symbols] = Replace(SymbolJson, field, token);
        await using var broker = new MofidOpeningOrderBroker(browser, new FixedTime());
        var fees = await broker.GetFeesAsync(Draft(), CancellationToken.None);
        var order = fees.CreateOrder(Draft(), 1000, 2000);
        await broker.ValidateAsync(Draft(), order, Settings(), CancellationToken.None);
        await using var dispatch = await broker.OpenDispatchAsync(order, Settings().Start + Settings().Duration, CancellationToken.None);
        Assert.Equal(1, browser.Dispatches);
    }

    [Theory]
    [InlineData("lowAllowedPrice", "\"0\"")]
    [InlineData("highAllowedPrice", "\"10000\"")]
    [InlineData("minValidBuyVolume", "\"1\"")]
    [InlineData("maxValidBuyVolume", "\"100000\"")]
    public async Task MarketFinancialStrings_KeepBoundsAndExactUnits(string field, string token)
    {
        var browser = new FakeBrowser(); browser.Payloads[MofidRead.Market] = Replace(MarketJson, field, token);
        await using var broker = new MofidOpeningOrderBroker(browser, new FixedTime());
        await broker.ValidateAsync(Draft(), Order(), Settings(), CancellationToken.None);
        Assert.Equal(0, browser.Dispatches);
    }

    public static IEnumerable<object[]> InvalidFinancialFields()
    {
        foreach (var (read, fields) in new[]
        {
            (MofidRead.Symbols, new[] { "buyCommission", "hidePrice", "csize", "minDealablePrice", "minDealableCount", "minValidBuyVolume", "maxValidBuyVolume" }),
            (MofidRead.Market, new[] { "lowAllowedPrice", "highAllowedPrice", "minValidBuyVolume", "maxValidBuyVolume" }),
            (MofidRead.Money, new[] { "buyPowerT2" })
        })
        foreach (string field in fields)
        foreach (string token in new[] { "null", "true", "\"private fixture data\"", "1e-29", "79228162514264337593543950336" })
        {
            if (field == "csize" && token == "null") continue;
            yield return new object[] { (int)read, field, token };
        }
    }

    [Theory]
    [MemberData(nameof(InvalidFinancialFields))]
    public async Task InvalidFinancialData_ReportsOnlyPermittedStageFieldAndCategory(int read, string field, string token)
    {
        var browser = new FakeBrowser(); var kind = (MofidRead)read;
        browser.Payloads[kind] = Replace(browser.Payloads[kind], field, token);
        await using var broker = new MofidOpeningOrderBroker(browser, new FixedTime());
        var error = await Assert.ThrowsAsync<OpeningOrderException>(() => broker.ValidateAsync(Draft(), Order(), Settings(), CancellationToken.None));
        Assert.Equal(OpeningOrderError.InvalidNumericValue, error.Error);
        Assert.NotEqual(OpeningOrderField.None, error.Field);
        Assert.Equal(kind == MofidRead.Symbols ? OpeningOrderStage.SymbolMetadata : kind == MofidRead.Market ? OpeningOrderStage.MarketData : OpeningOrderStage.BuyingPower, error.Stage);
        Assert.DoesNotContain("private fixture data", error.ToString());
        Assert.DoesNotContain(token, error.SafeDiagnostic);
        Assert.Equal(0, browser.Dispatches);
        await Assert.ThrowsAsync<OpeningOrderException>(() => broker.OpenDispatchAsync(Order(), Settings().Start + Settings().Duration, CancellationToken.None));
    }

    [Theory]
    [InlineData((int)MofidRead.Symbols, "minDealablePrice", "0", OpeningOrderError.InvalidNumericValue)]
    [InlineData((int)MofidRead.Symbols, "minDealableCount", "0", OpeningOrderError.InvalidNumericValue)]
    [InlineData((int)MofidRead.Symbols, "minDealableCount", "1.5", OpeningOrderError.InvalidNumericValue)]
    [InlineData((int)MofidRead.Symbols, "minValidBuyVolume", "0", OpeningOrderError.InvalidNumericValue)]
    [InlineData((int)MofidRead.Symbols, "maxValidBuyVolume", "0", OpeningOrderError.InvalidNumericValue)]
    [InlineData((int)MofidRead.Market, "highAllowedPrice", "0", OpeningOrderError.InvalidNumericValue)]
    [InlineData((int)MofidRead.Money, "buyPowerT2", "0", OpeningOrderError.InsufficientBuyingPower)]
    [InlineData((int)MofidRead.Money, "buyPowerT2", "\"10000000\"", OpeningOrderError.InvalidNumericValue)]
    [InlineData((int)MofidRead.Market, "stateCode", "\"H\"", OpeningOrderError.MarketUnavailable)]
    [InlineData((int)MofidRead.Market, "lowAllowedPrice", "3000", OpeningOrderError.InvalidOrderConstraints)]
    [InlineData((int)MofidRead.Market, "minValidBuyVolume", "1001", OpeningOrderError.InvalidOrderConstraints)]
    public async Task InvalidDataAndBusinessRejections_RemainDistinctAndFailClosed(int read, string field, string token, OpeningOrderError expected)
    {
        var browser = new FakeBrowser(); var kind = (MofidRead)read;
        browser.Payloads[kind] = Replace(browser.Payloads[kind], field, token);
        await using var broker = new MofidOpeningOrderBroker(browser, new FixedTime());
        var error = await Assert.ThrowsAsync<OpeningOrderException>(() => broker.ValidateAsync(Draft(), Order(), Settings(), CancellationToken.None));
        Assert.Equal(expected, error.Error); Assert.Equal(0, browser.Dispatches);
    }

    [Fact]
    public async Task MissingAndNullBounds_AreNotZeroAndCannotUseOldSuccessfulPreflight()
    {
        var browser = new FakeBrowser();
        await using var broker = new MofidOpeningOrderBroker(browser, new FixedTime());
        await broker.ValidateAsync(Draft(), Order(), Settings(), CancellationToken.None);
        browser.Payloads[MofidRead.Market] = MarketJson.Replace("\"lowAllowedPrice\":100,", "");
        var error = await Assert.ThrowsAsync<OpeningOrderException>(() => broker.ValidateAsync(Draft(), Order(), Settings(), CancellationToken.None));
        Assert.Equal(NumericIssue.Missing, error.NumericIssue); Assert.Equal(OpeningOrderField.LowAllowedPrice, error.Field);
        await Assert.ThrowsAsync<OpeningOrderException>(() => broker.OpenDispatchAsync(Order(), Settings().Start + Settings().Duration, CancellationToken.None));
        Assert.Equal(0, browser.Dispatches);
    }

    [Theory]
    [InlineData("{\"items\":[]}", OpeningOrderError.MalformedResponse)]
    [InlineData("closed-day", OpeningOrderError.MarketClosed)]
    [InlineData("closed-hours", OpeningOrderError.MarketClosed)]
    [InlineData("invalid-day", OpeningOrderError.MalformedResponse)]
    public async Task Calendar_SeparatesClosedMarketFromUnavailableContract(string fixture, OpeningOrderError expected)
    {
        var browser = new FakeBrowser();
        browser.Payloads[MofidRead.Calendar] = fixture switch
        {
            "closed-day" => CalendarJson.Replace("[1,2,3,4,5]", "[2,3]"),
            "closed-hours" => CalendarJson.Replace("08:45", "10:00").Replace("09:00", "10:10"),
            "invalid-day" => CalendarJson.Replace("[1,2,3,4,5]", "[true]"),
            _ => fixture
        };
        await using var broker = new MofidOpeningOrderBroker(browser, new FixedTime());
        var error = await Assert.ThrowsAsync<OpeningOrderException>(() => broker.ValidateAsync(Draft(), Order(), Settings(), CancellationToken.None));
        Assert.Equal(expected, error.Error); Assert.Equal(0, browser.Dispatches);
    }

    [Fact]
    public async Task MinimumNotionalAndFreshness_AreExplicitAndNeverRelaxTheSafetyCap()
    {
        var browser = new FakeBrowser(); var time = new FixedTime();
        await using var broker = new MofidOpeningOrderBroker(browser, time);
        var small = new InstrumentFees(.001m, 0, null).CreateOrder(Draft(), 1, 2000);
        var minimum = await Assert.ThrowsAsync<OpeningOrderException>(() => broker.ValidateAsync(Draft(), small, Settings(), CancellationToken.None));
        Assert.Equal(OpeningOrderError.MinimumNotional, minimum.Error);
        time.Advance(TimeSpan.FromSeconds(9));
        var stale = await Assert.ThrowsAsync<OpeningOrderException>(() => broker.ValidateAsync(Draft(), Order(), Settings(), CancellationToken.None));
        Assert.Equal(OpeningOrderError.StalePreflight, stale.Error);
        Assert.Equal(0, browser.Dispatches);
    }

    private static string Replace(string json, string field, string token)
    {
        var node = System.Text.Json.Nodes.JsonNode.Parse(json)!;
        var item = node is System.Text.Json.Nodes.JsonArray array ? array[0]! : node["symbols"] is System.Text.Json.Nodes.JsonArray symbols ? symbols[0]! : node;
        item[field] = System.Text.Json.Nodes.JsonNode.Parse(token);
        return node.ToJsonString();
    }
}
