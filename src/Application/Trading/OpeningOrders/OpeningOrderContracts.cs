using TseExcel.Domain.Trading.Orders;

namespace TseExcel.Application.Trading.OpeningOrders;

public sealed record OpeningDraft(string Id, string SymbolIsin, string SymbolName, OrderSide Side,
    long Quantity, decimal UnitPriceIrr, int ValidityType);

public sealed record InstrumentFees(decimal CommissionRate, decimal HiddenPriceIrr, decimal? ContractSize)
{
    public OrderTerms CreateOrder(OpeningDraft draft, long quantity, decimal price) => new(
        draft.SymbolIsin, draft.SymbolName, draft.Side, quantity, price, CommissionRate, HiddenPriceIrr, ContractSize);
}

public interface IOpeningOrderBroker : IAsyncDisposable
{
    Task AuthenticateAsync(bool refresh, CancellationToken cancellationToken);
    Task<IReadOnlyList<OpeningDraft>> GetDraftsAsync(CancellationToken cancellationToken);
    Task<InstrumentFees> GetFeesAsync(OpeningDraft draft, CancellationToken cancellationToken);
    Task ValidateAsync(OpeningDraft draft, OrderTerms order, DispatchSettings settings, CancellationToken cancellationToken);
    Task<IOrderDispatch> OpenDispatchAsync(OrderTerms order, DateTimeOffset cutoff, CancellationToken cancellationToken);
}

// Completion acknowledges only the browser's local fetch initiation, never the HTTP response.
public interface IOrderDispatch : IAsyncDisposable
{
    Task<LocalInitiation> InitiateAsync(DateTimeOffset timestamp, CancellationToken cancellationToken);
}

public readonly record struct LocalInitiation(bool Initiated, DateTimeOffset Timestamp, bool LocalFailure);

public enum OpeningOrderError
{
    General,
    Authentication,
    ReadFailure,
    MalformedResponse,
    MissingInstrumentMetadata,
    InvalidNumericValue,
    MarketClosed,
    MarketUnavailable,
    InsufficientBuyingPower,
    MinimumNotional,
    SafetyCap,
    StalePreflight,
    InvalidOrderConstraints,
    MetadataChanged
}

public enum OpeningOrderStage
{
    None, WaitingForPreflight, Preflight, Authentication, SymbolMetadata, MarketData,
    BuyingPower, Calendar, Session, PreparingDispatch, WaitingForStart, Dispatching, Completed
}

public enum OpeningOrderField
{
    None, BuyCommission, HidePrice, ContractSize, LowAllowedPrice, HighAllowedPrice,
    MinDealablePrice, MinDealableCount, MinValidBuyVolume, MaxValidBuyVolume,
    BuyPowerT2, MarketUnit, TradingTimeType, Quantity, Price, Side, ValidityType
}

public enum NumericIssue { None, Missing, Null, Representation, NonPositive, OutOfRange, NonIntegral }

public sealed class OpeningOrderException : Exception
{
    public OpeningOrderError Error { get; }
    public OpeningOrderStage Stage { get; private set; }
    public OpeningOrderField Field { get; }
    public NumericIssue NumericIssue { get; }
    public OpeningOrderException(string message, OpeningOrderError error = OpeningOrderError.General,
        OpeningOrderField field = OpeningOrderField.None, NumericIssue numericIssue = NumericIssue.None) : base(message)
    { Error = error; Field = field; NumericIssue = numericIssue; }
    public OpeningOrderException AtStage(OpeningOrderStage stage) { Stage = stage; return this; }
    // Only enums cross the diagnostic boundary; never include exception messages or broker values.
    public string SafeDiagnostic => $"stage={Stage}; field={Field}; category={Error}; numeric={NumericIssue}";
}
