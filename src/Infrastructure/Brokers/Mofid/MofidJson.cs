using System.Text.Json;
using TseExcel.Application.Trading.OpeningOrders;

namespace TseExcel.Infrastructure.Brokers.Mofid;

internal static class MofidJson
{
    internal static JsonElement Required(JsonElement value, string field) => value.ValueKind == JsonValueKind.Object &&
        value.TryGetProperty(field, out JsonElement result) ? result : throw Invalid();
    internal static decimal Number(JsonElement value, string field, bool positive = false)
    {
        JsonElement item = Required(value, field);
        if (item.ValueKind != JsonValueKind.Number || !item.TryGetDecimal(out decimal number) || number < 0 || (positive && number == 0))
            throw Invalid();
        return number;
    }
    internal static long Integer(JsonElement value, string field, bool positive = false)
    {
        decimal number = Number(value, field, positive);
        if (number != decimal.Truncate(number) || number > long.MaxValue) throw Invalid();
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
        return matches.Length == 1 ? matches[0] : throw Invalid();
    }
    internal static OpeningOrderException Invalid() => new("Mofid response does not match the verified contract.");
}
