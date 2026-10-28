using System.Text;
using System.Text.Json;
using Xunit;

using TseExcel.Infrastructure.Storage.Json;
using TseExcel.Application.WorkbookJson;

namespace TseExcel.Infrastructure.Tests;

public sealed class WorkbookJsonTests : IDisposable
{
    private readonly IWorkbookJsonStore store = new WorkbookJsonStore();
    private readonly string directory = Path.Combine(Path.GetTempPath(), "TseExcel.Tests", Guid.NewGuid().ToString("N"));

    public WorkbookJsonTests() => Directory.CreateDirectory(directory);

    [Theory]
    [InlineData("Portfolio.xlsx", "Portfolio.json")]
    [InlineData("Portfolio.xlsm", "Portfolio.json")]
    [InlineData("Portfolio.xlsb", "Portfolio.json")]
    [InlineData("Portfolio.xls", "Portfolio.json")]
    [InlineData("Portfolio.v2.xlsx", "Portfolio.v2.json")]
    [InlineData("تحلیل.xlsx", "تحلیل.json")]
    public void Resolve_UsesWorkbookBasenameWithoutCreatingFiles(string workbookName, string jsonName)
    {
        string workbookPath = CreateWorkbook(workbookName);
        byte[] original = File.ReadAllBytes(workbookPath);

        Assert.Equal(Path.Combine(directory, jsonName), store.ResolvePath(workbookPath));

        Assert.Single(Directory.GetFiles(directory));
        Assert.Equal(original, File.ReadAllBytes(workbookPath));
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData(" ")]
    [InlineData("Book1")]
    [InlineData("relative/Book.xlsx")]
    [InlineData(@"C:Book.xlsx")]
    [InlineData("https://example.com/Book.xlsx")]
    [InlineData("C:\\bad\0name.xlsx")]
    [InlineData("C:\\bad?.xlsx")]
    public void Resolve_RejectsUnsavedOrInvalidPaths(string? path)
    {
        Assert.Throws<ArgumentException>(() => store.ResolvePath(path));
        Assert.Empty(Directory.GetFileSystemEntries(directory));
    }

    [Fact]
    public void Resolve_RejectsMissingWorkbookWithoutCreatingIt()
    {
        Assert.Throws<FileNotFoundException>(() => store.ResolvePath(Path.Combine(directory, "Missing.xlsx")));
        Assert.Empty(Directory.GetFileSystemEntries(directory));
    }

    [Fact]
    public void Resolve_RejectsDirectory()
    {
        Assert.Throws<ArgumentException>(() => store.ResolvePath(directory));
        Assert.Empty(Directory.GetFileSystemEntries(directory));
    }

    [Fact]
    public void CreateIfMissing_CreatesMinimalUtf8Json()
    {
        string path = store.ResolvePath(CreateWorkbook());

        Assert.True(store.CreateIfMissing(path));

        Assert.Equal("{}"u8.ToArray(), File.ReadAllBytes(path));
        Assert.Equal("{}", store.Read(path));
    }

    [Fact]
    public void CreateIfMissing_PreservesExistingBytesEvenForMalformedJson()
    {
        string path = store.ResolvePath(CreateWorkbook());
        byte[] original = [0xEF, 0xBB, 0xBF, 0x7B, 0xFF];
        File.WriteAllBytes(path, original);

        Assert.False(store.CreateIfMissing(path));
        Assert.False(store.CreateIfMissing(path));

        Assert.Equal(original, File.ReadAllBytes(path));
    }

    [Fact]
    public void CreateIfMissing_PreservesFileAppearingAfterPathResolution()
    {
        string path = store.ResolvePath(CreateWorkbook());
        File.WriteAllText(path, "{\"existing\":true}");

        Assert.False(store.CreateIfMissing(path));
        Assert.Equal("{\"existing\":true}", File.ReadAllText(path));
    }

    [Fact]
    public void Read_ReturnsExactContentForDisplayWithoutChangingFiles()
    {
        string path = store.ResolvePath(CreateWorkbook());
        const string content = "{\r\n  \"message\": \"سلام\"\r\n}\r\n";
        File.WriteAllText(path, content, new UTF8Encoding(true));
        byte[] original = File.ReadAllBytes(path);

        Assert.Equal(content, store.Read(path));

        Assert.Equal(original, File.ReadAllBytes(path));
    }

    [Fact]
    public void Read_MissingJsonThrowsWithoutCreatingIt()
    {
        string path = store.ResolvePath(CreateWorkbook());

        Assert.Throws<FileNotFoundException>(() => store.Read(path));

        Assert.False(File.Exists(path));
    }

    [Theory]
    [InlineData("")]
    [InlineData("{")]
    [InlineData("{\"value\":}")]
    public void Read_MalformedJsonThrowsAndPreservesFile(string content)
    {
        string path = Path.Combine(directory, "Portfolio.json");
        File.WriteAllText(path, content);

        Assert.ThrowsAny<JsonException>(() => store.Read(path));

        Assert.Equal(content, File.ReadAllText(path));
    }

    [Fact]
    public void Read_InvalidUtf8ThrowsAndPreservesFile()
    {
        string path = Path.Combine(directory, "Portfolio.json");
        byte[] original = [0x7B, 0xFF, 0x7D];
        File.WriteAllBytes(path, original);

        Assert.Throws<DecoderFallbackException>(() => store.Read(path));

        Assert.Equal(original, File.ReadAllBytes(path));
    }

    [Fact]
    public void FileOperations_ReportMissingParentDirectory()
    {
        string path = Path.Combine(directory, "missing", "Portfolio.json");

        Assert.Throws<DirectoryNotFoundException>(() => store.CreateIfMissing(path));
        Assert.Throws<DirectoryNotFoundException>(() => store.Read(path));
        Assert.False(Directory.Exists(Path.GetDirectoryName(path)));
    }

    [Fact]
    public void FileOperations_ReportDirectoryAtJsonPath()
    {
        string path = Path.Combine(directory, "Portfolio.json");
        Directory.CreateDirectory(path);
        string existingFile = Path.Combine(path, "existing.txt");
        byte[] original = "Unchanged directory content."u8.ToArray();
        File.WriteAllBytes(existingFile, original);

        Exception? createException = Record.Exception(() => store.CreateIfMissing(path));
        Assert.True(createException is IOException or UnauthorizedAccessException,
            $"Expected a filesystem failure, got {createException?.GetType().FullName ?? "no exception"}.");
        Assert.False(File.Exists(path));
        Assert.Equal(new[] { path }, Directory.GetFileSystemEntries(directory));
        Assert.Equal(new[] { existingFile }, Directory.GetFileSystemEntries(path));
        Assert.Equal(original, File.ReadAllBytes(existingFile));

        Assert.Throws<UnauthorizedAccessException>(() => store.Read(path));
        Assert.False(File.Exists(path));
        Assert.Equal(new[] { path }, Directory.GetFileSystemEntries(directory));
        Assert.Equal(new[] { existingFile }, Directory.GetFileSystemEntries(path));
        Assert.Equal(original, File.ReadAllBytes(existingFile));
    }

    [Fact]
    public void Read_ReportsSharingViolation()
    {
        string path = Path.Combine(directory, "Portfolio.json");
        File.WriteAllText(path, "{}");
        using FileStream lockedFile = new(path, FileMode.Open, FileAccess.ReadWrite, FileShare.None);

        Assert.Throws<IOException>(() => store.Read(path));
    }

    [Fact]
    public void Commands_KeepWorkbooksIsolated()
    {
        string first = store.ResolvePath(CreateWorkbook("First.xlsx"));
        string second = store.ResolvePath(CreateWorkbook("Second.xlsx"));

        Assert.True(store.CreateIfMissing(first));

        Assert.False(File.Exists(second));
        Assert.Throws<FileNotFoundException>(() => store.Read(second));
        Assert.Equal("{}", store.Read(first));
    }

    private string CreateWorkbook(string name = "Portfolio.xlsx")
    {
        string path = Path.Combine(directory, name);
        File.WriteAllText(path, "Saved workbook fixture; no Excel required.");
        return path;
    }

    public void Dispose() => Directory.Delete(directory, recursive: true);
}


