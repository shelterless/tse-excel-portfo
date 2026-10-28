using TseExcel.Application.WorkbookJson;
using Xunit;

namespace TseExcel.Application.Tests;

public class WorkbookJsonCommandsTests
{
    [Fact]
    public void Constructor_RejectsMissingStore() =>
        Assert.Throws<ArgumentNullException>(() => new WorkbookJsonCommands(null!));

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void Create_ResolvesBeforeCreatingAndReturnsOutcome(bool created)
    {
        var store = new RecordingStore { Created = created };
        var commands = new WorkbookJsonCommands(store);
        Assert.Empty(store.Calls);

        WorkbookJsonCreation result = commands.Create("First.xlsx");

        Assert.Equal(new WorkbookJsonCreation("First.xlsx.json", created), result);
        Assert.Equal(["resolve:First.xlsx", "create:First.xlsx.json"], store.Calls);
    }

    [Fact]
    public void Read_ResolvesEveryWorkbookAndReturnsExactTextWithoutCreating()
    {
        var store = new RecordingStore();
        var commands = new WorkbookJsonCommands(store);

        Assert.Equal(store.Content, commands.Read("First.xlsx"));
        Assert.Equal(store.Content, commands.Read("Second.xlsx"));

        Assert.Equal(["resolve:First.xlsx", "read:First.xlsx.json",
            "resolve:Second.xlsx", "read:Second.xlsx.json"], store.Calls);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void InvalidWorkbook_StopsBeforePersistence(bool create)
    {
        var failure = new ArgumentException("Invalid workbook.");
        var store = new RecordingStore { ResolveFailure = failure };
        var commands = new WorkbookJsonCommands(store);

        Exception? actual = Record.Exception(() =>
        {
            if (create) commands.Create(null);
            else commands.Read(null);
        });

        Assert.Same(failure, actual);
        Assert.Equal(["resolve:"], store.Calls);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void PersistenceFailure_PropagatesWithoutRetryOrFallback(bool create)
    {
        var failure = new IOException("Unavailable storage.");
        var store = new RecordingStore { PersistenceFailure = failure };
        var commands = new WorkbookJsonCommands(store);

        Exception? actual = Record.Exception(() =>
        {
            if (create) commands.Create("Book.xlsx");
            else commands.Read("Book.xlsx");
        });

        Assert.Same(failure, actual);
        Assert.Equal(["resolve:Book.xlsx", create ? "create:Book.xlsx.json" : "read:Book.xlsx.json"], store.Calls);
    }

    private sealed class RecordingStore : IWorkbookJsonStore
    {
        internal List<string> Calls { get; } = [];
        internal bool Created { get; init; }
        internal string Content { get; } = "{\r\n  \"message\": \"سلام\"\r\n}\r\n";
        internal Exception? ResolveFailure { get; init; }
        internal Exception? PersistenceFailure { get; init; }

        public string ResolvePath(string? workbookFullName)
        {
            Calls.Add($"resolve:{workbookFullName}");
            if (ResolveFailure is not null) throw ResolveFailure;
            return workbookFullName + ".json";
        }

        public bool CreateIfMissing(string jsonPath)
        {
            Calls.Add($"create:{jsonPath}");
            if (PersistenceFailure is not null) throw PersistenceFailure;
            return Created;
        }

        public string Read(string jsonPath)
        {
            Calls.Add($"read:{jsonPath}");
            if (PersistenceFailure is not null) throw PersistenceFailure;
            return Content;
        }
    }
}
