using System.Runtime.InteropServices;
using TseExcel.AddIn.ExcelInterop;
using Xunit;

namespace TseExcel.AddIn.Tests;

public class ExcelWorkbookTests
{
    [Fact]
    public void GetActiveFullName_RejectsMissingActiveWorkbook()
    {
        var adapter = new ExcelWorkbook(() => new ApplicationStub());
        Assert.Equal("No active workbook. Open or create a workbook first.",
            Assert.Throws<InvalidOperationException>(() => adapter.GetActiveFullName()).Message);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData(" ")]
    public void GetActiveFullName_RejectsUnsavedWorkbookBeforeReadingFullName(string? directory)
    {
        var adapter = new ExcelWorkbook(() => new ApplicationStub
        {
            ActiveWorkbook = new UnsavedWorkbookStub { Path = directory }
        });
        Assert.Equal("Save the active workbook to a filesystem path first.",
            Assert.Throws<InvalidOperationException>(() => adapter.GetActiveFullName()).Message);
    }

    [Fact]
    public void GetActiveFullName_ReadsCurrentApplicationAndWorkbookOnCallingThread()
    {
        int thread = Environment.CurrentManagedThreadId;
        var application = new ApplicationStub { ActiveWorkbook = new SavedWorkbookStub(@"C:\First.xlsx") };
        int calls = 0;
        var adapter = new ExcelWorkbook(() =>
        {
            Assert.Equal(thread, Environment.CurrentManagedThreadId);
            calls++;
            return application;
        });

        Assert.Equal(@"C:\First.xlsx", adapter.GetActiveFullName());
        application = new ApplicationStub { ActiveWorkbook = new SavedWorkbookStub(@"C:\Second.xlsx") };
        Assert.Equal(@"C:\Second.xlsx", adapter.GetActiveFullName());
        Assert.Equal(2, calls);
    }

    [Fact]
    public void GetActiveFullName_PropagatesComFailure()
    {
        var failure = new COMException("Excel is unavailable.");
        var adapter = new ExcelWorkbook(() => throw failure);
        Assert.Same(failure, Assert.Throws<COMException>(() => adapter.GetActiveFullName()));
    }

    // Public stubs let the production dynamic binder exercise the same property access as COM.
    public sealed class ApplicationStub
    {
        public object? ActiveWorkbook { get; init; }
    }

    public sealed class SavedWorkbookStub(string fullName)
    {
        public string Path => @"C:\";
        public string FullName => fullName;
    }

    public sealed class UnsavedWorkbookStub
    {
        public string? Path { get; init; }
        public string FullName => throw new InvalidOperationException("FullName must not be read.");
    }
}
