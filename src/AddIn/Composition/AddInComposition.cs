using TseExcel.Application.WorkbookJson;
using TseExcel.Infrastructure.Storage.Json;

namespace TseExcel.AddIn.Composition;

internal static class AddInComposition
{
    internal static WorkbookJsonCommands CreateWorkbookJsonCommands() => new(new WorkbookJsonStore());
}
