using ExcelDna.Integration;

namespace TseExcel.AddIn;

internal static class ExcelWorkbook
{
    // Called synchronously from a Ribbon callback on Excel's UI thread.
    internal static string GetActiveJsonPath()
    {
        // Late binding stays at the COM boundary; the path/file logic uses typed .NET values.
        dynamic application = ExcelDnaUtil.Application;
        dynamic? workbook = application.ActiveWorkbook;
        if (workbook is null)
        {
            throw new InvalidOperationException("No active workbook. Open or create a workbook first.");
        }

        string? directory = workbook.Path;
        if (string.IsNullOrWhiteSpace(directory))
        {
            throw new InvalidOperationException("Save the active workbook to a filesystem path first.");
        }

        string? fullName = workbook.FullName;
        return WorkbookJsonPath.Resolve(fullName);
    }
}
