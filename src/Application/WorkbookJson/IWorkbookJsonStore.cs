namespace TseExcel.Application.WorkbookJson;

/// <summary>Persistence boundary for JSON belonging to a saved workbook.</summary>
public interface IWorkbookJsonStore
{
    /// <summary>Validates the saved workbook and resolves its adjacent JSON path without writing files.</summary>
    string ResolvePath(string? workbookFullName);

    /// <summary>Atomically creates minimal JSON, returning false without changing an existing file.</summary>
    bool CreateIfMissing(string jsonPath);

    /// <summary>Returns the original text after validating its encoding and JSON syntax.</summary>
    string Read(string jsonPath);
}
