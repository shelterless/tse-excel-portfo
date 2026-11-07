using TseExcel.Application.WorkbookJson;
using TseExcel.Infrastructure.Storage.Json;
using TseExcel.AddIn.Trading.OpeningOrders;
using TseExcel.Infrastructure.Brokers.Mofid;
using ExcelDna.Integration;

namespace TseExcel.AddIn.Composition;

internal static class AddInComposition
{
    private static readonly Lazy<MofidOpeningOrderBroker> Broker = new(() =>
        new MofidOpeningOrderBroker(Path.GetDirectoryName(ExcelDnaUtil.XllPath) ??
            throw new InvalidOperationException("The add-in directory is unavailable.")));
    private static readonly Lazy<OpeningOrderPresenter> OpeningOrders = new(() => new OpeningOrderPresenter(Broker.Value));
    internal static WorkbookJsonCommands CreateWorkbookJsonCommands() => new(new WorkbookJsonStore());
    internal static Action<bool> CreateOpeningOrderAction() => loginOnly => OpeningOrders.Value.Show(loginOnly);
    internal static void CloseMofidSession()
    {
        if (Broker.IsValueCreated) Broker.Value.DisposeAsync().AsTask().GetAwaiter().GetResult();
    }
}
