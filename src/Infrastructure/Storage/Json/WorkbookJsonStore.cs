using TseExcel.Application.WorkbookJson;

namespace TseExcel.Infrastructure.Storage.Json;

public sealed class WorkbookJsonStore : IWorkbookJsonStore
{
    public string ResolvePath(string? workbookFullName) => WorkbookJsonPath.Resolve(workbookFullName);

    public bool CreateIfMissing(string jsonPath) => WorkbookJsonFile.CreateIfMissing(jsonPath);

    public string Read(string jsonPath) => WorkbookJsonFile.Read(jsonPath);
}
