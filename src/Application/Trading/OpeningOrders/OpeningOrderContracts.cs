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

public sealed class OpeningOrderException : Exception
{
    public OpeningOrderException(string message) : base(message) { }
}
