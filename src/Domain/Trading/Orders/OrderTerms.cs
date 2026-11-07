using System.Globalization;
using System.Numerics;

namespace TseExcel.Domain.Trading.Orders;

public enum OrderSide { Buy = 0, Sell = 1 }

public sealed record OrderTerms
{
    public string SymbolIsin { get; }
    public string SymbolName { get; }
    public OrderSide Side { get; }
    public long Quantity { get; }
    public decimal UnitPriceIrr { get; }
    public decimal CommissionRate { get; }
    public decimal HiddenPriceIrr { get; }
    public decimal ContractSize { get; }
    public decimal TotalIrr { get; }

    public OrderTerms(string symbolIsin, string symbolName, OrderSide side, long quantity,
        decimal unitPriceIrr, decimal commissionRate, decimal hiddenPriceIrr, decimal? contractSize)
    {
        if (symbolIsin.Length != 12 || symbolIsin.Any(c => !(c is >= 'A' and <= 'Z' or >= '0' and <= '9')))
            throw new ArgumentException("A twelve-character ISIN is required.", nameof(symbolIsin));
        if (string.IsNullOrWhiteSpace(symbolName) || symbolName.Length > 80 || symbolName.Any(char.IsControl))
            throw new ArgumentException("A bounded instrument name is required.", nameof(symbolName));
        if (!Enum.IsDefined(side)) throw new ArgumentOutOfRangeException(nameof(side));
        if (quantity <= 0 || unitPriceIrr <= 0 || commissionRate < 0 || commissionRate >= 1 ||
            hiddenPriceIrr < 0 || contractSize <= 0)
            throw new ArgumentOutOfRangeException(nameof(quantity), "Invalid order financial terms.");
        SymbolIsin = symbolIsin;
        SymbolName = symbolName;
        Side = side;
        Quantity = quantity;
        UnitPriceIrr = unitPriceIrr;
        CommissionRate = commissionRate;
        HiddenPriceIrr = hiddenPriceIrr;
        ContractSize = contractSize ?? 1m;
        TotalIrr = OrderCost.Calculate(quantity, unitPriceIrr, commissionRate, hiddenPriceIrr, ContractSize);
    }
}

public static class OrderCost
{
    public static decimal Calculate(long quantity, decimal price, decimal rate, decimal hiddenPrice, decimal size)
    {
        if (quantity <= 0 || price <= 0 || rate < 0 || rate >= 1 || hiddenPrice < 0 || size <= 0)
            throw new ArgumentOutOfRangeException(nameof(quantity), "Invalid financial input.");
        // Integer fractions preserve every decimal digit before the final IRR ceiling.
        Fraction value = Fraction.From(price) * (Fraction.From(1m) + Fraction.From(rate));
        value = (value + Fraction.From(hiddenPrice)) * Fraction.From(size) * Fraction.From(quantity);
        BigInteger whole = BigInteger.DivRem(value.Numerator, BigInteger.Pow(10, value.Scale), out BigInteger remainder);
        return decimal.Parse((whole + (remainder.IsZero ? 0 : 1)).ToString(CultureInfo.InvariantCulture), CultureInfo.InvariantCulture);
    }

    private readonly record struct Fraction(BigInteger Numerator, int Scale)
    {
        public static Fraction From(decimal value)
        {
            int[] bits = decimal.GetBits(value);
            BigInteger numerator = (uint)bits[0] | ((BigInteger)(uint)bits[1] << 32) | ((BigInteger)(uint)bits[2] << 64);
            return new(numerator, (bits[3] >> 16) & 255);
        }
        public static Fraction operator +(Fraction a, Fraction b)
        {
            int scale = Math.Max(a.Scale, b.Scale);
            return new(a.Numerator * BigInteger.Pow(10, scale - a.Scale) + b.Numerator * BigInteger.Pow(10, scale - b.Scale), scale);
        }
        public static Fraction operator *(Fraction a, Fraction b) => new(a.Numerator * b.Numerator, a.Scale + b.Scale);
    }
}
