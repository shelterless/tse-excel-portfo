using System.Reflection.PortableExecutable;
using System.Runtime.InteropServices;
using System.Text;
using System.Xml.Linq;
using Xunit;

namespace TseExcel.AddIn.Tests;

public class PackagingContractTests
{
    [Fact]
    public void PackedX64AddIn_ContainsRibbonAssemblyAndAllThreeRuntimeReferences()
    {
        string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent!.Name;
        string output = Path.Combine(ArchitectureContractTests.FindRepositoryRoot(), "src", "AddIn", "bin",
            configuration, "net10.0-windows");
        string packed = Path.Combine(output, "publish", "AddIn-AddIn64-packed.xll");
        Assert.True(File.Exists(packed), $"Build the AddIn before testing packaging: {packed}");
        using (FileStream stream = File.OpenRead(packed))
        using (var reader = new PEReader(stream))
        {
            Assert.Equal(Machine.Amd64, reader.PEHeaders.CoffHeader.Machine);
        }

        // Load as resource data only: do not execute the XLL or require Excel to be installed.
        nint module = LoadLibraryEx(packed, 0, 0x02 | 0x20);
        Assert.NotEqual(0, module);
        try
        {
            foreach (string assembly in new[] { "ADDIN", "APPLICATION", "INFRASTRUCTURE", "DOMAIN" })
            {
                byte[] bytes = ReadResource(module, "TSEEXCEL." + assembly, "ASSEMBLY_LZMA");
                Assert.NotEmpty(bytes);
            }

            string xml = Encoding.UTF8.GetString(ReadResource(module, "__MAIN__", "DNA"));
            XDocument document = XDocument.Parse(xml);
            Assert.Equal("TseExcel.AddIn Add-In", (string?)document.Root!.Attribute("Name"));
            XElement library = Assert.Single(document.Descendants(), element => element.Name.LocalName == "ExternalLibrary");
            Assert.Equal("packed:TSEEXCEL.ADDIN", (string?)library.Attribute("Path"));
            Assert.Equal("true", (string?)library.Attribute("ExplicitExports"));
            Assert.NotEqual("true", (string?)library.Attribute("ExplicitRegistration"));
            Assert.Equal(new[] { "packed:TSEEXCEL.APPLICATION", "packed:TSEEXCEL.DOMAIN", "packed:TSEEXCEL.INFRASTRUCTURE" },
                document.Descendants().Where(element => element.Name.LocalName == "Reference")
                    .Select(element => (string)element.Attribute("Path")!).Order());
        }
        finally
        {
            FreeLibrary(module);
        }
    }

    private static byte[] ReadResource(nint module, string name, string type)
    {
        nint resource = FindResource(module, name, type);
        Assert.NotEqual(0, resource);
        uint size = SizeofResource(module, resource);
        Assert.True(size > 0);
        nint pointer = LockResource(LoadResource(module, resource));
        Assert.NotEqual(0, pointer);
        byte[] bytes = new byte[checked((int)size)];
        Marshal.Copy(pointer, bytes, 0, bytes.Length);
        return bytes;
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern nint LoadLibraryEx(string fileName, nint file, uint flags);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern nint FindResource(nint module, string name, string type);

    [DllImport("kernel32.dll")]
    private static extern uint SizeofResource(nint module, nint resource);

    [DllImport("kernel32.dll")]
    private static extern nint LoadResource(nint module, nint resource);

    [DllImport("kernel32.dll")]
    private static extern nint LockResource(nint resource);

    [DllImport("kernel32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool FreeLibrary(nint module);
}
