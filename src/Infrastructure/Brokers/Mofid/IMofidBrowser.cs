using System.Text.Json;
using TseExcel.Application.Trading.OpeningOrders;

namespace TseExcel.Infrastructure.Brokers.Mofid;

internal enum MofidRead { Drafts, Symbols, Market, Money, Calendar, Session }

internal interface IMofidBrowser : IAsyncDisposable
{
    Task AuthenticateAsync(bool refresh, CancellationToken cancellationToken);
    Task<JsonElement> ReadAsync(MofidRead read, string? symbolIsin, CancellationToken cancellationToken);
    Task<IOrderDispatch> OpenDispatchAsync(string payload, DateTimeOffset cutoff, CancellationToken cancellationToken);
}
