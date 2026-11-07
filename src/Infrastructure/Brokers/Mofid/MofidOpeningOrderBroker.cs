using System.Globalization;
using System.Text.Json;
using TseExcel.Application.Trading.OpeningOrders;
using TseExcel.Domain.Trading.Orders;
using static TseExcel.Infrastructure.Brokers.Mofid.MofidJson;

namespace TseExcel.Infrastructure.Brokers.Mofid;

public sealed class MofidOpeningOrderBroker : IOpeningOrderBroker
{
    private readonly IMofidBrowser browser;
    private readonly TimeProvider time;
    private OrderTerms? validatedOrder;
    private long validatedAt;
    private DateTimeOffset validatedCutoff;
    private static readonly int[] OrdinaryUnits = [1, 2, 3, 4, 5, 6, 7, 8, 18, 19, 20, 31, 32, 39, 40, 41, 42, 43, 52, 54];
    private static readonly int[] EtfUnits = [3, 4, 5, 6, 7, 8, 31, 32, 39, 43, 52, 54];
    private static readonly int[] BaseUnits = [18, 19, 20, 40, 41, 42];
    internal const decimal MaximumOrderValueIrr = 5_000_000m;

    public MofidOpeningOrderBroker(string driverDirectory) : this(new ChromeMofidBrowser(driverDirectory), TimeProvider.System) { }
    internal MofidOpeningOrderBroker(IMofidBrowser browser, TimeProvider time) { this.browser = browser; this.time = time; }

    public Task AuthenticateAsync(bool refresh, CancellationToken cancellationToken) => browser.AuthenticateAsync(refresh, cancellationToken);

    public async Task<IReadOnlyList<OpeningDraft>> GetDraftsAsync(CancellationToken cancellationToken)
    {
        await browser.AuthenticateAsync(false, cancellationToken).ConfigureAwait(false);
        JsonElement payload = await browser.ReadAsync(MofidRead.Drafts, null, cancellationToken).ConfigureAwait(false);
        if (payload.ValueKind != JsonValueKind.Array) throw Invalid();
        var drafts = new List<OpeningDraft>();
        var ids = new HashSet<string>(StringComparer.Ordinal);
        foreach (JsonElement item in payload.EnumerateArray())
        {
            JsonElement idValue = Required(item, "id");
            string id = idValue.ValueKind switch
            {
                JsonValueKind.String => Text(item, "id", 240),
                JsonValueKind.Number when idValue.TryGetInt64(out long number) => number.ToString(CultureInfo.InvariantCulture),
                _ => throw Invalid()
            };
            if (!ids.Add(id)) throw Invalid();
            long side = Integer(item, "side");
            if (side is not (0 or 1)) throw Invalid();
            int validity = item.TryGetProperty("validityType", out _) ? checked((int)Integer(item, "validityType")) : 0;
            string isin = Text(item, "symbolIsin", 12);
            if (isin.Length != 12 || isin.Any(c => !(c is >= 'A' and <= 'Z' or >= '0' and <= '9'))) throw Invalid();
            drafts.Add(new(id, isin, Text(item, "symbolName"), (OrderSide)side, Integer(item, "quantity", true), Number(item, "price", true), validity));
        }
        return drafts.AsReadOnly();
    }

    public async Task<InstrumentFees> GetFeesAsync(OpeningDraft draft, CancellationToken cancellationToken)
    {
        if (draft.Side != OrderSide.Buy) throw new OpeningOrderException("SELL fee and live-order contracts are not approved.");
        JsonElement all = await browser.ReadAsync(MofidRead.Symbols, null, cancellationToken).ConfigureAwait(false);
        return Fees(Match(Required(all, "symbols"), draft.SymbolIsin));
    }

    private static InstrumentFees Fees(JsonElement symbol)
    {
        decimal rate = Number(symbol, "buyCommission");
        if (rate >= 1) throw Invalid();
        bool hasSize = symbol.TryGetProperty("csize", out JsonElement size);
        return new(rate, Number(symbol, "hidePrice"), !hasSize || size.ValueKind == JsonValueKind.Null ? null : Number(symbol, "csize", true));
    }

    public async Task ValidateAsync(OpeningDraft draft, OrderTerms order, DispatchSettings settings, CancellationToken cancellationToken)
    {
        validatedOrder = null;
        if (draft.Side != OrderSide.Buy || order.Side != OrderSide.Buy || draft.ValidityType != 0 || draft.SymbolIsin != order.SymbolIsin)
            throw new OpeningOrderException("Only a matching ordinary DAY BUY is enabled.");
        await browser.AuthenticateAsync(false, cancellationToken).ConfigureAwait(false);
        long started = time.GetTimestamp();
        JsonElement all = await browser.ReadAsync(MofidRead.Symbols, null, cancellationToken).ConfigureAwait(false);
        JsonElement symbol = Match(Required(all, "symbols"), draft.SymbolIsin);
        if (Fees(symbol).CreateOrder(draft, order.Quantity, order.UnitPriceIrr) != order) throw new OpeningOrderException("Financial metadata changed after confirmation.");
        if (Required(symbol, "isActive").ValueKind != JsonValueKind.True || Required(symbol, "canBuy").ValueKind != JsonValueKind.True) throw Invalid();
        int unit = checked((int)Integer(symbol, "marketUnit", true));
        if (!OrdinaryUnits.Contains(unit) || Text(symbol, "symbolName") != order.SymbolName) throw Invalid();
        JsonElement market = Match(await browser.ReadAsync(MofidRead.Market, draft.SymbolIsin, cancellationToken).ConfigureAwait(false), draft.SymbolIsin);
        string state = Required(market, "stateCode").ToString();
        if (state is not ("A" or "65")) throw new OpeningOrderException("The instrument is halted, restricted or unknown.");
        decimal low = Number(market, "lowAllowedPrice"), high = Number(market, "highAllowedPrice", true);
        decimal tick = Number(symbol, "minDealablePrice", true);
        long step = Integer(symbol, "minDealableCount", true);
        long minimum = Integer(symbol, "minValidBuyVolume", true), maximum = Integer(symbol, "maxValidBuyVolume", true);
        if (market.TryGetProperty("minValidBuyVolume", out _)) minimum = Math.Max(minimum, Integer(market, "minValidBuyVolume", true));
        if (market.TryGetProperty("maxValidBuyVolume", out _)) maximum = Math.Min(maximum, Integer(market, "maxValidBuyVolume", true));
        if (low > high || order.UnitPriceIrr < low || order.UnitPriceIrr > high || order.UnitPriceIrr % tick != 0 ||
            minimum > maximum || order.Quantity < minimum || order.Quantity > maximum || order.Quantity % step != 0) throw Invalid();
        decimal minimumNotional = EtfUnits.Contains(unit) ? 1_000_000m : BaseUnits.Contains(unit) ? 50_000_000m : 5_000_000m;
        JsonElement money = await browser.ReadAsync(MofidRead.Money, null, cancellationToken).ConfigureAwait(false);
        if (checked(order.Quantity * (order.UnitPriceIrr + order.HiddenPriceIrr)) < minimumNotional ||
            order.TotalIrr > MaximumOrderValueIrr || order.TotalIrr > Number(money, "buyPowerT2"))
            throw new OpeningOrderException("Order value fails the verified notional, safety cap or buying-power check.");
        JsonElement calendar = await browser.ReadAsync(MofidRead.Calendar, null, cancellationToken).ConfigureAwait(false);
        JsonElement session = await browser.ReadAsync(MofidRead.Session, null, cancellationToken).ConfigureAwait(false);
        ValidateCalendar(symbol, calendar, session, settings);
        TimeSpan freshness = time.GetElapsedTime(started) + (settings.Start - time.GetLocalNow()) + settings.Duration;
        if (freshness > TimeSpan.FromSeconds(15) || time.GetLocalNow() >= settings.Start) throw new OpeningOrderException("Preflight data is stale for the requested window.");
        validatedOrder = order;
        validatedAt = started;
        validatedCutoff = settings.Start + settings.Duration;
    }

    internal static void ValidateCalendar(JsonElement symbol, JsonElement calendar, JsonElement session, DispatchSettings settings)
    {
        TimeZoneInfo zone = TimeZoneInfo.FindSystemTimeZoneById("Iran Standard Time");
        DateTimeOffset target = TimeZoneInfo.ConvertTime(settings.Start, zone);
        DateTimeOffset server = ApiDate(Required(session, "serverTime"), zone);
        DateTimeOffset marketDate = ApiDate(Required(session, "startSessionTimeStamp"), zone);
        if (target.Date != server.Date || server.Date != marketDate.Date) throw Invalid();
        JsonElement items = Required(calendar, "items");
        if (items.ValueKind != JsonValueKind.Array) throw Invalid();
        long type = Integer(symbol, "tradingTimeType", true);
        JsonElement[] rules = items.EnumerateArray().Where(x => Integer(x, "tradingTimeType", true) == type).ToArray();
        if (rules.Length != 1) throw Invalid();
        JsonElement rule = rules[0], days = Required(rule, "days");
        if (days.ValueKind != JsonValueKind.Array || days.GetArrayLength() == 0 ||
            days.EnumerateArray().Any(x => !x.TryGetInt32(out int day) || day is < 1 or > 7) ||
            !days.EnumerateArray().Any(x => x.GetInt32() == ((int)target.DayOfWeek + 1) % 7 + 1)) throw Invalid();
        bool overlap = false;
        foreach ((string start, string end) in new[] { ("startPreTradingTime", "endPreTradingTime"), ("startTradingTime", "endTradingTime") })
        {
            if (start == "startPreTradingTime" && Empty(rule, start) && Empty(rule, end)) continue;
            if (!TimeOnly.TryParseExact(Text(rule, start), "HH:mm", CultureInfo.InvariantCulture, DateTimeStyles.None, out TimeOnly a) ||
                !TimeOnly.TryParseExact(Text(rule, end), "HH:mm", CultureInfo.InvariantCulture, DateTimeStyles.None, out TimeOnly b) || a > b) throw Invalid();
            DateTimeOffset from = new(target.Date + a.ToTimeSpan(), target.Offset), to = new(target.Date + b.ToTimeSpan(), target.Offset);
            overlap |= settings.Start < to && settings.Start + settings.Duration > from;
        }
        if (!overlap) throw new OpeningOrderException("Dispatch window does not overlap a verified trading session.");
    }

    private static bool Empty(JsonElement item, string field) => !item.TryGetProperty(field, out JsonElement value) ||
        value.ValueKind == JsonValueKind.Null || (value.ValueKind == JsonValueKind.String && value.GetString() == "");

    private static DateTimeOffset ApiDate(JsonElement value, TimeZoneInfo zone)
    {
        if (value.ValueKind == JsonValueKind.Number && value.TryGetInt64(out long milliseconds))
            return TimeZoneInfo.ConvertTime(DateTimeOffset.FromUnixTimeMilliseconds(milliseconds), zone);
        if (value.ValueKind != JsonValueKind.String) throw Invalid();
        string text = value.GetString()!;
        if (DateTime.TryParse(text, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind, out DateTime local) && local.Kind == DateTimeKind.Unspecified)
            return new(local, zone.GetUtcOffset(local));
        if (DateTimeOffset.TryParse(text, CultureInfo.InvariantCulture, DateTimeStyles.None, out DateTimeOffset timestamp))
            return TimeZoneInfo.ConvertTime(timestamp, zone);
        throw Invalid();
    }

    internal static string Payload(OrderTerms order)
    {
        if (order.Side != OrderSide.Buy) throw new OpeningOrderException("Live SELL is disabled.");
        return JsonSerializer.Serialize(new { order = new { price = order.UnitPriceIrr, quantity = order.Quantity,
            side = 0, validityType = 0, createDateTime = "__TSE_LOCAL_TIMESTAMP__", commission = order.CommissionRate,
            symbolIsin = order.SymbolIsin, symbolName = order.SymbolName, orderModelType = 1, totalValue = order.TotalIrr, orderFrom = 34 } });
    }

    public Task<IOrderDispatch> OpenDispatchAsync(OrderTerms order, DateTimeOffset cutoff, CancellationToken cancellationToken)
    {
        if (order != validatedOrder || cutoff != validatedCutoff || time.GetElapsedTime(validatedAt) > TimeSpan.FromSeconds(15))
            throw new OpeningOrderException("A matching fresh preflight is required.");
        validatedOrder = null;
        return browser.OpenDispatchAsync(Payload(order), cutoff, cancellationToken);
    }

    public ValueTask DisposeAsync() => browser.DisposeAsync();
}
