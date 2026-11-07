using ExcelDna.Integration;

namespace TseExcel.AddIn.Composition;

public sealed class MofidAddInLifecycle : IExcelAddIn
{
    public void AutoOpen() { }
    public void AutoClose() => AddInComposition.CloseMofidSession();
}
