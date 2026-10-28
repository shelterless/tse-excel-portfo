using System.Text;
using System.Text.Json;

namespace TseExcel.AddIn;

internal static class WorkbookJsonFile
{
    internal static bool CreateIfMissing(string jsonPath)
    {
        FileStream stream;
        try
        {
            // CreateNew is atomic: a file appearing before this call cannot be overwritten.
            stream = new FileStream(jsonPath, FileMode.CreateNew, FileAccess.Write, FileShare.None);
        }
        catch (IOException) when (File.Exists(jsonPath))
        {
            return false;
        }

        using (stream)
        {
            stream.Write("{}"u8);
        }

        return true;
    }

    internal static string Read(string jsonPath)
    {
        string content = File.ReadAllText(jsonPath, new UTF8Encoding(false, true));
        using JsonDocument document = JsonDocument.Parse(content);
        return content;
    }
}
