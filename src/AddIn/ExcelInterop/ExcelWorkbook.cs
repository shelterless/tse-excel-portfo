namespace TseExcel.AddIn.ExcelInterop;

internal sealed class ExcelWorkbook(Func<object> getApplication)
{
    // Called synchronously from a Ribbon callback on Excel's UI thread; never cache COM objects or paths.
    internal string? GetActiveFullName()
    {
        // Late binding stays at the COM boundary; the application receives only a typed path.
        dynamic application = getApplication();
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
        return fullName;
    }
}
