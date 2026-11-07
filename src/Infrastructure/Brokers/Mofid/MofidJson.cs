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
        if (value.ValueKind != JsonValueKind.Object || !value.TryGetProperty(field, out JsonElement item)) throw InvalidNumber();
        string text = item.ValueKind switch
        {
            JsonValueKind.Number => item.GetRawText(),
            JsonValueKind.String when allowString => item.GetString()!,
            _ => throw InvalidNumber()
        };
        // Strings are enabled only for verified fee metadata, in plain invariant decimal notation.
        string[] exponentParts = text.Split(['e', 'E']);
        if (exponentParts.Length > 2 || (item.ValueKind == JsonValueKind.String && exponentParts.Length != 1)) throw InvalidNumber();
        int exponent = 0;
        if (exponentParts.Length == 2 && !int.TryParse(exponentParts[1], NumberStyles.AllowLeadingSign, CultureInfo.InvariantCulture, out exponent))
            throw InvalidNumber();
        string mantissa = exponentParts[0];
        string[] decimalParts = mantissa.Split('.');
        if (decimalParts.Length > 2 || decimalParts.Any(part => part.Length == 0 || part.Any(c => c is < '0' or > '9'))) throw InvalidNumber();
        int dot = mantissa.IndexOf('.');
        long scale = (dot < 0 ? 0 : mantissa.Length - dot - 1L) - exponent;
        string digits = mantissa.Replace(".", "", StringComparison.Ordinal).TrimStart('0');
        if (digits.Length == 0) return positive ? throw InvalidNumber() : 0m;
        // Remove insignificant zeroes before checking decimal's 96-bit coefficient and 28-place scale.
        int trailing = digits.Length - digits.TrimEnd('0').Length;
        digits = digits[..(digits.Length - trailing)];
        scale -= trailing;
        if (scale < 0)
        {
            if (digits.Length - scale > 29) throw InvalidNumber();
            digits += new string('0', checked((int)-scale));
            scale = 0;
        }
        if (scale > 28 || digits.Length > 29) throw InvalidNumber();
        BigInteger coefficient = BigInteger.Parse(digits, CultureInfo.InvariantCulture);
        if (coefficient > (BigInteger.One << 96) - 1) throw InvalidNumber();
        decimal number = new(unchecked((int)(uint)(coefficient & uint.MaxValue)),
            unchecked((int)(uint)((coefficient >> 32) & uint.MaxValue)),
            unchecked((int)(uint)(coefficient >> 64)), false, (byte)scale);
        return number;
    }
    internal static long Integer(JsonElement value, string field, bool positive = false)
    {
        decimal number = Number(value, field, positive);
        if (number != decimal.Truncate(number) || number > long.MaxValue) throw InvalidNumber();
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
    internal static OpeningOrderException InvalidNumber() => new("A required financial value is invalid or not exactly representable.", OpeningOrderError.InvalidNumericValue);
    internal static OpeningOrderException Invalid() => new("Mofid response does not match the verified contract.", OpeningOrderError.MalformedResponse);
}
