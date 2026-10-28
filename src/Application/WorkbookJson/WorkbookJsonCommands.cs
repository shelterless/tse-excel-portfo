namespace TseExcel.Application.WorkbookJson;

public sealed class WorkbookJsonCommands
{
    private readonly IWorkbookJsonStore store;

    public WorkbookJsonCommands(IWorkbookJsonStore store)
    {
        ArgumentNullException.ThrowIfNull(store);
        this.store = store;
    }

    public WorkbookJsonCreation Create(string? workbookFullName)
    {
        string jsonPath = store.ResolvePath(workbookFullName);
        return new WorkbookJsonCreation(jsonPath, store.CreateIfMissing(jsonPath));
    }

    public string Read(string? workbookFullName) => store.Read(store.ResolvePath(workbookFullName));
}
