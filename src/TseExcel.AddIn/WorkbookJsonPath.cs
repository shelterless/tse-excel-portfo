namespace TseExcel.AddIn;

internal static class WorkbookJsonPath
{
    internal static string Resolve(string? workbookFullName)
    {
        if (string.IsNullOrWhiteSpace(workbookFullName) ||
            !Path.IsPathFullyQualified(workbookFullName) ||
            workbookFullName.IndexOfAny(Path.GetInvalidPathChars()) >= 0)
        {
            throw new ArgumentException("Save the active workbook to a filesystem path first.", nameof(workbookFullName));
        }

        string fullPath = Path.GetFullPath(workbookFullName);
        string fileName = Path.GetFileName(fullPath);
        if (string.IsNullOrWhiteSpace(Path.GetFileNameWithoutExtension(fullPath)) ||
            fileName.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0)
        {
            throw new ArgumentException("The workbook filename is invalid.", nameof(workbookFullName));
        }

        // GetAttributes preserves access errors instead of hiding them as a missing file.
        if ((File.GetAttributes(fullPath) & FileAttributes.Directory) != 0)
        {
            throw new ArgumentException("The workbook path must identify a saved file.", nameof(workbookFullName));
        }

        return Path.ChangeExtension(fullPath, ".json");
    }
}
