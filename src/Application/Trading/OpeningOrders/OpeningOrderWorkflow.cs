using TseExcel.Domain.Trading.Orders;

namespace TseExcel.Application.Trading.OpeningOrders;

public sealed class OpeningOrderWorkflow(IOpeningOrderBroker broker, IDispatchClock clock)
{
    public async Task<DispatchSummary> ExecuteConfirmedAsync(OpeningDraft draft, OrderTerms order,
        DispatchSettings settings, bool explicitlyConfirmed, DispatchProgress progress, CancellationToken cancellationToken)
    {
        if (!explicitlyConfirmed) throw new OpeningOrderException("Explicit confirmation is required for every execution.");
        if (draft.Side != OrderSide.Buy || order.Side != OrderSide.Buy || draft.SymbolIsin != order.SymbolIsin || draft.ValidityType != 0)
            throw new OpeningOrderException("Only a matching ordinary DAY BUY is enabled.");
        if (clock.LocalNow >= settings.Start) throw new OpeningOrderException("The approved local start time has passed.");
        TimeSpan refreshAt = clock.Elapsed + (settings.Start - clock.LocalNow) - TimeSpan.FromSeconds(5);
        while (clock.Elapsed < refreshAt)
        {
            progress.Update(TimeSpan.Zero, settings.Start - clock.LocalNow);
            await clock.WaitUntilAsync(Min(refreshAt, clock.Elapsed + TimeSpan.FromMilliseconds(25)), cancellationToken).ConfigureAwait(false);
        }
        await broker.ValidateAsync(draft, order, settings, cancellationToken).ConfigureAwait(false);
        cancellationToken.ThrowIfCancellationRequested();
        if (clock.LocalNow >= settings.Start) throw new OpeningOrderException("Preflight completed after the approved start time.");
        IOrderDispatch dispatch = await broker.OpenDispatchAsync(order, settings.Start + settings.Duration, cancellationToken).ConfigureAwait(false);
        return await new DispatchEngine(clock).RunAsync(settings, dispatch, progress, cancellationToken).ConfigureAwait(false);
    }

    private static TimeSpan Min(TimeSpan a, TimeSpan b) => a < b ? a : b;
}
