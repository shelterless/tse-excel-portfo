using System.Globalization;
using System.Text.Json;
using TseExcel.Application.Trading.OpeningOrders;
using TseExcel.Infrastructure.Brokers.Mofid;
using Xunit;
using static TseExcel.Infrastructure.Tests.Brokers.Mofid.MofidBrokerTests;

namespace TseExcel.Infrastructure.Tests.Brokers.Mofid;

public class MofidMetadataTests
{
    [Theory]
    [InlineData("0.00036875")]
    [InlineData("\"0.00036875\"")]
    public async Task DraftToDetails_VerifiedCommissionRepresentationsProduceExactEditableOrder(string commission)
    {
        var browser = new FakeBrowser();
        browser.Payloads[MofidRead.Symbols] = SymbolJson.Replace("0.001", commission);
        await using var broker = new MofidOpeningOrderBroker(browser, new FixedTime());
        OpeningDraft draft = Assert.Single(await broker.GetDraftsAsync(CancellationToken.None));
        InstrumentFees fees = await broker.GetFeesAsync(draft, CancellationToken.None);
        var initial = fees.CreateOrder(draft, draft.Quantity, draft.UnitPriceIrr);
        var edited = fees.CreateOrder(draft, 22, 56593);
        Assert.Equal(.00036875m, fees.CommissionRate);
        Assert.Null(fees.ContractSize);
        Assert.Equal(2_000_738m, initial.TotalIrr);
        Assert.Equal(1_245_506m, edited.TotalIrr);
        Assert.Equal(1000, draft.Quantity); Assert.Equal(2000m, draft.UnitPriceIrr);
        Assert.Equal(new[] { MofidRead.Drafts, MofidRead.Symbols }, browser.Reads);
        Assert.Equal(0, browser.Dispatches);
    }

    [Theory]
    [InlineData("null")]
    [InlineData("missing")]
    [InlineData("2.5")]
    [InlineData("\"2.5\"")]
    public async Task Fees_PreserveNullableSizeAndVerifiedDecimalMetadata(string size)
    {
        var browser = new FakeBrowser();
        browser.Payloads[MofidRead.Symbols] = SymbolJson.Replace("\"hidePrice\":0", "\"hidePrice\":\"0.125\"");
        browser.Payloads[MofidRead.Symbols] = size == "missing"
            ? browser.Payloads[MofidRead.Symbols].Replace("\"csize\":null,", "")
            : browser.Payloads[MofidRead.Symbols].Replace("\"csize\":null", "\"csize\":" + size);
        await using var broker = new MofidOpeningOrderBroker(browser, new FixedTime());
        InstrumentFees fees = await broker.GetFeesAsync(Draft(), CancellationToken.None);
        Assert.Equal(.125m, fees.HiddenPriceIrr);
        Assert.Equal(size is "null" or "missing" ? (decimal?)null : 2.5m, fees.ContractSize);
        Assert.Equal(size is "null" or "missing" ? 2_002_125m : 5_005_313m,
            fees.CreateOrder(Draft(), 1000, 2000).TotalIrr);
    }

    [Theory]
    [InlineData("0.0000000000000000000000000001", "0.0000000000000000000000000001")]
    [InlineData("1e-28", "0.0000000000000000000000000001")]
    [InlineData("79228162514264337593543950335", "79228162514264337593543950335")]
    [InlineData("7.9228162514264337593543950335", "7.9228162514264337593543950335")]
    [InlineData("1.00000000000000000000000000000", "1")]
    [InlineData("100e-30", "0.0000000000000000000000000001")]
    [InlineData("1e3", "1000")]
    [InlineData("1E+3", "1000")]
    [InlineData("0e9999", "0")]
    public void Numbers_AreExactAtDecimalBoundaries(string token, string expected)
    {
        using var document = JsonDocument.Parse("{\"value\":" + token + "}");
        Assert.Equal(decimal.Parse(expected, CultureInfo.InvariantCulture), MofidJson.Number(document.RootElement, "value"));
        if (token.IndexOfAny(['e', 'E']) < 0)
        {
            using var quoted = JsonDocument.Parse(JsonSerializer.Serialize(new { value = token }));
            Assert.Equal(decimal.Parse(expected, CultureInfo.InvariantCulture), MofidJson.Number(quoted.RootElement, "value", allowString: true));
        }
    }

    [Theory]
    [InlineData("null")]
    [InlineData("true")]
    [InlineData("[]")]
    [InlineData("\"\"")]
    [InlineData("\" 0.001\"")]
    [InlineData("\"1,234\"")]
    [InlineData("\"0,001\"")]
    [InlineData("\"NaN\"")]
    [InlineData("\"Infinity\"")]
    [InlineData("\"1e-3\"")]
    [InlineData("\"+1\"")]
    [InlineData("\".001\"")]
    [InlineData("\"-0.001\"")]
    [InlineData("-0.001")]
    [InlineData("1e-29")]
    [InlineData("0.10000000000000000000000000001")]
    [InlineData("79228162514264337593543950336")]
    [InlineData("7.92281625142643375935439503351")]
    [InlineData("1e999999999999")]
    public void Numbers_RejectInvalidOrRoundedRepresentationsWithoutEchoingValues(string token)
    {
        using var document = JsonDocument.Parse("{\"value\":" + token + "}");
        var error = Assert.Throws<OpeningOrderException>(() => MofidJson.Number(document.RootElement, "value", allowString: true));
        Assert.Equal(OpeningOrderError.InvalidNumericValue, error.Error);
        Assert.Equal("A required financial value is invalid or not exactly representable.", error.Message);
    }

    [Fact]
    public void Numbers_RejectMissingZeroWhenPositiveAndUnverifiedStringFields()
    {
        using var missing = JsonDocument.Parse("{}");
        using var zero = JsonDocument.Parse("{\"value\":0}");
        using var text = JsonDocument.Parse("{\"value\":\"0.001\"}");
        Assert.Equal(OpeningOrderError.InvalidNumericValue, Assert.Throws<OpeningOrderException>(() => MofidJson.Number(missing.RootElement, "value")).Error);
        Assert.Throws<OpeningOrderException>(() => MofidJson.Number(zero.RootElement, "value", true));
        Assert.Throws<OpeningOrderException>(() => MofidJson.Number(text.RootElement, "value"));
    }

    [Theory]
    [InlineData("fr-FR")]
    [InlineData("fa-IR")]
    public void Metadata_ParsingIsInvariant(string culture)
    {
        CultureInfo previous = CultureInfo.CurrentCulture;
        try
        {
            CultureInfo.CurrentCulture = new CultureInfo(culture);
            using var document = JsonDocument.Parse("{\"value\":\"0.00036875\"}");
            Assert.Equal(.00036875m, MofidJson.Number(document.RootElement, "value", allowString: true));
        }
        finally { CultureInfo.CurrentCulture = previous; }
    }

    [Theory]
    [InlineData("{\"symbols\":[]}", OpeningOrderError.MissingInstrumentMetadata)]
    [InlineData("{\"symbols\":[{\"symbolIsin\":\"IRO1OTHER001\"}]}", OpeningOrderError.MissingInstrumentMetadata)]
    [InlineData("{\"symbols\":{}}", OpeningOrderError.MalformedResponse)]
    public async Task Metadata_FailsClosedWithSpecificCategory(string json, OpeningOrderError category)
    {
        var browser = new FakeBrowser(); browser.Payloads[MofidRead.Symbols] = json;
        await using var broker = new MofidOpeningOrderBroker(browser, new FixedTime());
        var error = await Assert.ThrowsAsync<OpeningOrderException>(() => broker.GetFeesAsync(Draft(), CancellationToken.None));
        Assert.Equal(category, error.Error); Assert.Equal(0, browser.Dispatches);
    }

    [Fact]
    public async Task Metadata_RejectsDuplicateIdentityOrChangedInstrumentName()
    {
        var browser = new FakeBrowser();
        await using var broker = new MofidOpeningOrderBroker(browser, new FixedTime());
        using var document = JsonDocument.Parse(SymbolJson);
        string symbol = document.RootElement.GetProperty("symbols")[0].GetRawText();
        browser.Payloads[MofidRead.Symbols] = "{\"symbols\":[" + symbol + "," + symbol + "]}";
        Assert.Equal(OpeningOrderError.MalformedResponse,
            (await Assert.ThrowsAsync<OpeningOrderException>(() => broker.GetFeesAsync(Draft(), CancellationToken.None))).Error);
        browser.Payloads[MofidRead.Symbols] = SymbolJson.Replace("Fixture", "Changed");
        Assert.Equal(OpeningOrderError.MalformedResponse,
            (await Assert.ThrowsAsync<OpeningOrderException>(() => broker.GetFeesAsync(Draft(), CancellationToken.None))).Error);
    }

    [Theory]
    [InlineData(1, 1000)]
    [InlineData(18, 10000)]
    public async Task ExistingSafetyCap_StillBlocksFeeInclusiveOrdinaryAndBaseMarketMinimums(int marketUnit, long quantity)
    {
        var browser = new FakeBrowser();
        browser.Payloads[MofidRead.Symbols] = SymbolJson.Replace("\"marketUnit\":3", "\"marketUnit\":" + marketUnit);
        await using var broker = new MofidOpeningOrderBroker(browser, new FixedTime());
        var order = new InstrumentFees(.001m, 0, null).CreateOrder(Draft(), quantity, 5000);
        Assert.Equal(5_000_000m, MofidOpeningOrderBroker.MaximumOrderValueIrr);
        var error = await Assert.ThrowsAsync<OpeningOrderException>(() => broker.ValidateAsync(Draft(), order, Settings(), CancellationToken.None));
        Assert.Equal("Order value fails the verified notional, safety cap or buying-power check.", error.Message);
        Assert.Equal(0, browser.Dispatches);
    }
}
