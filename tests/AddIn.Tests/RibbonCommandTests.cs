using System.Runtime.InteropServices;
using System.Security;
using System.Text;
using System.Text.Json;
using System.Windows.Forms;
using Microsoft.CSharp.RuntimeBinder;
using TseExcel.AddIn.Ribbon;
using TseExcel.Application.WorkbookJson;
using Xunit;

namespace TseExcel.AddIn.Tests;

public class RibbonCommandTests
{
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void Create_DisplaysEstablishedOutcomeMessage(bool created)
    {
        var store = new StoreStub { Created = created };
        var messages = new List<(string, MessageBoxIcon)>();
        var ribbon = new TseExcelRibbon(new WorkbookJsonCommands(store), () => "Book.xlsx",
            (text, icon) => messages.Add((text, icon)));
        Assert.Empty(store.Workbooks);

        ribbon.OnCreateJson(null!);

        string expected = created ? "JSON created:\nBook.xlsx.json" :
            "JSON already exists and was left unchanged:\nBook.xlsx.json";
        Assert.Equal([(expected, MessageBoxIcon.Information)], messages);
        Assert.Equal(1, store.CreateCalls);
        Assert.Equal(0, store.ReadCalls);
    }

    [Fact]
    public void Callbacks_ResolveWorkbookAtEachClickOnTheCallingThread()
    {
        string active = "First.xlsx";
        int thread = Environment.CurrentManagedThreadId;
        var store = new StoreStub();
        var messages = new List<(string, MessageBoxIcon)>();
        var ribbon = new TseExcelRibbon(new WorkbookJsonCommands(store), () =>
        {
            Assert.Equal(thread, Environment.CurrentManagedThreadId);
            return active;
        }, (text, icon) =>
        {
            Assert.Equal(thread, Environment.CurrentManagedThreadId);
            messages.Add((text, icon));
        });
        ribbon.GetCustomUI("Microsoft.Excel.Workbook");
        Assert.Empty(store.Workbooks);

        ribbon.OnCreateJson(null!);
        active = "Second.xlsx";
        ribbon.OnShowJson(null!);
        active = "First.xlsx";
        ribbon.OnShowJson(null!);

        Assert.Equal(["First.xlsx", "Second.xlsx", "First.xlsx"], store.Workbooks);
        Assert.Equal((store.Content, MessageBoxIcon.Information), messages[1]);
        Assert.Equal((store.Content, MessageBoxIcon.Information), messages[2]);
        Assert.Equal(1, store.CreateCalls);
        Assert.Equal(2, store.ReadCalls);
    }

    [Theory]
    [InlineData("json", "The JSON file is malformed.\nFailure.")]
    [InlineData("encoding", "The JSON file contains invalid text encoding.\nFailure.")]
    [InlineData("missing", "File not found. Save the workbook and use Create JSON if needed.\nBook.json")]
    [InlineData("io", "Unable to complete the workbook JSON command.\nFailure.")]
    [InlineData("access", "Unable to complete the workbook JSON command.\nFailure.")]
    [InlineData("security", "Unable to complete the workbook JSON command.\nFailure.")]
    [InlineData("argument", "Unable to complete the workbook JSON command.\nFailure.")]
    [InlineData("unsupported", "Unable to complete the workbook JSON command.\nFailure.")]
    [InlineData("invalid", "Unable to complete the workbook JSON command.\nFailure.")]
    [InlineData("com", "Unable to complete the workbook JSON command.\nFailure.")]
    [InlineData("binder", "Unable to complete the workbook JSON command.\nFailure.")]
    public void Callbacks_PreserveErrorMessagesAndWarningIcons(string kind, string expected)
    {
        Exception failure = kind switch
        {
            "json" => new JsonException("Failure."),
            "encoding" => new DecoderFallbackException("Failure."),
            "missing" => new FileNotFoundException("Failure.", "Book.json"),
            "io" => new IOException("Failure."),
            "access" => new UnauthorizedAccessException("Failure."),
            "security" => new SecurityException("Failure."),
            "argument" => new ArgumentException("Failure."),
            "unsupported" => new NotSupportedException("Failure."),
            "invalid" => new InvalidOperationException("Failure."),
            "com" => new COMException("Failure."),
            "binder" => new RuntimeBinderException("Failure."),
            _ => throw new ArgumentOutOfRangeException(nameof(kind))
        };
        var store = new StoreStub { Failure = failure };
        var messages = new List<(string, MessageBoxIcon)>();
        var ribbon = new TseExcelRibbon(new WorkbookJsonCommands(store), () => "Book.xlsx",
            (text, icon) => messages.Add((text, icon)));

        ribbon.OnCreateJson(null!);
        ribbon.OnShowJson(null!);

        Assert.Equal([(expected, MessageBoxIcon.Warning), (expected, MessageBoxIcon.Warning)], messages);
    }

    [Fact]
    public void WorkbookAdapterFailure_IsDisplayedBeforeAnyPersistence()
    {
        var store = new StoreStub();
        var messages = new List<(string, MessageBoxIcon)>();
        var ribbon = new TseExcelRibbon(new WorkbookJsonCommands(store),
            () => throw new InvalidOperationException("No active workbook. Open or create a workbook first."),
            (text, icon) => messages.Add((text, icon)));

        ribbon.OnCreateJson(null!);
        ribbon.OnShowJson(null!);

        Assert.Empty(store.Workbooks);
        Assert.Equal(2, messages.Count);
        Assert.All(messages, message => Assert.Equal((
            "Unable to complete the workbook JSON command.\nNo active workbook. Open or create a workbook first.",
            MessageBoxIcon.Warning), message));
    }

    private sealed class StoreStub : IWorkbookJsonStore
    {
        internal List<string?> Workbooks { get; } = [];
        internal bool Created { get; init; }
        internal Exception? Failure { get; init; }
        internal int CreateCalls { get; private set; }
        internal int ReadCalls { get; private set; }
        internal string Content => "{\r\n  \"message\": \"سلام\"\r\n}\r\n";

        public string ResolvePath(string? workbookFullName)
        {
            Workbooks.Add(workbookFullName);
            return workbookFullName + ".json";
        }

        public bool CreateIfMissing(string jsonPath)
        {
            CreateCalls++;
            if (Failure is not null) throw Failure;
            return Created;
        }

        public string Read(string jsonPath)
        {
            ReadCalls++;
            if (Failure is not null) throw Failure;
            return Content;
        }
    }
}
