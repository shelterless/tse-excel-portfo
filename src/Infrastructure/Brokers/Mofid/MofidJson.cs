using System.Globalization;
using System.Numerics;
using System.Text.Json;
using TseExcel.Application.Trading.OpeningOrders;

namespace TseExcel.Infrastructure.Brokers.Mofid;

internal static class MofidJson
{
    internal static JsonElement Required(JsonElement value, string field) => value.ValueKind == JsonValueKind.Object &&
        value.TryGetProperty(field, out JsonElement result) ? result : throw Invalid();
    internal static decimal Number(JsonElement value, string field, bool positive = false, bool allowString = false)
    {
        OpeningOrderException Error(NumericIssue issue = NumericIssue.Representation) => InvalidNumber(field, issue);
        if (value.ValueKind != JsonValueKind.Object || !value.TryGetProperty(field, out JsonElement item)) throw Error(NumericIssue.Missing);
        if (item.ValueKind == JsonValueKind.Null) throw Error(NumericIssue.Null);
        string text = item.ValueKind switch
        {
            JsonValueKind.Number => item.GetRawText(),
            JsonValueKind.String when allowString => item.GetString()!,
            _ => throw Error()
        };
        // Opted-in financial strings use plain invariant notation, never locale/grouping or float coercion.
        string[] exponentParts = text.Split(['e', 'E']);
        if (exponentParts.Length > 2 || (item.ValueKind == JsonValueKind.String && exponentParts.Length != 1)) throw Error();
        int exponent = 0;
        if (exponentParts.Length == 2 && !int.TryParse(exponentParts[1], NumberStyles.AllowLeadingSign, CultureInfo.InvariantCulture, out exponent))
            throw Error();
        string mantissa = exponentParts[0];
        string[] decimalParts = mantissa.Split('.');
        if (decimalParts.Length > 2 || decimalParts.Any(part => part.Length == 0 || part.Any(c => c is < '0' or > '9'))) throw Error();
        int dot = mantissa.IndexOf('.');
        long scale = (dot < 0 ? 0 : mantissa.Length - dot - 1L) - exponent;
        string digits = mantissa.Replace(".", "", StringComparison.Ordinal).TrimStart('0');
        if (digits.Length == 0) return positive ? throw Error(NumericIssue.NonPositive) : 0m;
        // Remove insignificant zeroes before checking decimal's 96-bit coefficient and 28-place scale.
        int trailing = digits.Length - digits.TrimEnd('0').Length;
        digits = digits[..(digits.Length - trailing)];
        scale -= trailing;
        if (scale < 0)
        {
            if (digits.Length - scale > 29) throw Error(NumericIssue.OutOfRange);
            digits += new string('0', checked((int)-scale));
            scale = 0;
        }
        if (scale > 28 || digits.Length > 29) throw Error(NumericIssue.OutOfRange);
        BigInteger coefficient = BigInteger.Parse(digits, CultureInfo.InvariantCulture);
        if (coefficient > (BigInteger.One << 96) - 1) throw Error(NumericIssue.OutOfRange);
        decimal number = new(unchecked((int)(uint)(coefficient & uint.MaxValue)),
            unchecked((int)(uint)((coefficient >> 32) & uint.MaxValue)),
            unchecked((int)(uint)(coefficient >> 64)), false, (byte)scale);
        return number;
    }
    internal static long Integer(JsonElement value, string field, bool positive = false, bool allowString = false)
    {
        decimal number = Number(value, field, positive, allowString);
        if (number != decimal.Truncate(number)) throw InvalidNumber(field, NumericIssue.NonIntegral);
        if (number > long.MaxValue) throw InvalidNumber(field, NumericIssue.OutOfRange);
        return (long)number;
    }
    internal static string Text(JsonElement value, string field, int limit = 80)
    {
        JsonElement item = Required(value, field);
        string? text = item.ValueKind == JsonValueKind.String ? item.GetString() : null;
        if (string.IsNullOrWhiteSpace(text) || text.Length > limit || text.Any(char.IsControl)) throw Invalid();
        return text;
    }
    internal static JsonElement Match(JsonElement items, string isin)
    {
        if (items.ValueKind != JsonValueKind.Array) throw Invalid();
        JsonElement[] matches = items.EnumerateArray().Where(item =>
            item.ValueKind == JsonValueKind.Object && item.TryGetProperty("symbolIsin", out JsonElement id) &&
            id.ValueKind == JsonValueKind.String && id.GetString() == isin).ToArray();
        return matches.Length switch
        {
            1 => matches[0],
            0 => throw new OpeningOrderException("Instrument metadata is absent for the selected identity.", OpeningOrderError.MissingInstrumentMetadata),
            _ => throw Invalid()
        };
    }
    internal static OpeningOrderException InvalidNumber(string? field = null, NumericIssue issue = NumericIssue.Representation) => new(
        "A required financial value is invalid or not exactly representable.", OpeningOrderError.InvalidNumericValue,
        field switch
        {
            "buyCommission" => OpeningOrderField.BuyCommission, "hidePrice" => OpeningOrderField.HidePrice,
            "csize" => OpeningOrderField.ContractSize, "lowAllowedPrice" => OpeningOrderField.LowAllowedPrice,
            "highAllowedPrice" => OpeningOrderField.HighAllowedPrice, "minDealablePrice" => OpeningOrderField.MinDealablePrice,
            "minDealableCount" => OpeningOrderField.MinDealableCount, "minValidBuyVolume" => OpeningOrderField.MinValidBuyVolume,
            "maxValidBuyVolume" => OpeningOrderField.MaxValidBuyVolume, "buyPowerT2" => OpeningOrderField.BuyPowerT2,
            "marketUnit" => OpeningOrderField.MarketUnit, "tradingTimeType" => OpeningOrderField.TradingTimeType,
            "quantity" => OpeningOrderField.Quantity, "price" => OpeningOrderField.Price, "side" => OpeningOrderField.Side,
            "validityType" => OpeningOrderField.ValidityType, _ => OpeningOrderField.None
        }, issue);
    internal static OpeningOrderException Invalid() => new("Mofid response does not match the verified contract.", OpeningOrderError.MalformedResponse);
}
