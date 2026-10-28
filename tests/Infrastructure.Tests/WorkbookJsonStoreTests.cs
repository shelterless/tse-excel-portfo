using TseExcel.Application.WorkbookJson;
using TseExcel.Infrastructure.Storage.Json;
using Xunit;

namespace TseExcel.Infrastructure.Tests;

public sealed class WorkbookJsonStoreTests : IDisposable
{
    private readonly string directory = Path.Combine(Path.GetTempPath(), "TseExcel.Tests", Guid.NewGuid().ToString("N"));

    public WorkbookJsonStoreTests() => Directory.CreateDirectory(directory);

    [Fact]
    public void Commands_UseStoreContractAndPreserveBothWorkbooksAndExistingJson()
    {
        IWorkbookJsonStore store = new WorkbookJsonStore();
        var commands = new WorkbookJsonCommands(store);
        string first = Path.Combine(directory, "First.xlsx");
        string second = Path.Combine(directory, "Second.xlsx");
        byte[] workbook = "Workbook content and formulas must not change."u8.ToArray();
        File.WriteAllBytes(first, workbook);
        File.WriteAllBytes(second, workbook);

        WorkbookJsonCreation created = commands.Create(first);
        Assert.Equal(new WorkbookJsonCreation(Path.ChangeExtension(first, ".json"), true), created);
        Assert.Equal("{}"u8.ToArray(), File.ReadAllBytes(created.JsonPath));
        Assert.Throws<FileNotFoundException>(() => commands.Read(second));
        Assert.False(File.Exists(Path.ChangeExtension(second, ".json")));

        const string existing = "{\r\n  \"existing\": true\r\n}\r\n";
        File.WriteAllText(created.JsonPath, existing);
        Assert.False(commands.Create(first).Created);
        Assert.Equal(existing, commands.Read(first));
        Assert.Equal(workbook, File.ReadAllBytes(first));
        Assert.Equal(workbook, File.ReadAllBytes(second));
    }

    [Fact]
    public void ConcurrentCreation_OnlyOneWriterCreatesAndOtherWritersPreserveIt()
    {
        IWorkbookJsonStore store = new WorkbookJsonStore();
        string path = Path.Combine(directory, "Concurrent.json");
        bool[] results = new bool[16];

        Parallel.For(0, results.Length, index => results[index] = store.CreateIfMissing(path));

        Assert.Single(results, created => created);
        Assert.Equal("{}"u8.ToArray(), File.ReadAllBytes(path));
    }

    [Fact]
    public void Commands_RejectMissingWorkbookEvenWhenAdjacentJsonExists()
    {
        var commands = new WorkbookJsonCommands(new WorkbookJsonStore());
        string missing = Path.Combine(directory, "Missing.xlsx");
        string json = Path.ChangeExtension(missing, ".json");
        byte[] original = "{\"existing\":true}"u8.ToArray();
        File.WriteAllBytes(json, original);

        Assert.Throws<FileNotFoundException>(() => commands.Create(missing));
        Assert.Throws<FileNotFoundException>(() => commands.Read(missing));
        Assert.Equal(original, File.ReadAllBytes(json));
        Assert.False(File.Exists(missing));
    }

    public void Dispose() => Directory.Delete(directory, recursive: true);
}
