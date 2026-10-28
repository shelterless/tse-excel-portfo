using System.Reflection;
using System.Runtime.InteropServices;
using System.Xml.Linq;
using ExcelDna.Integration.CustomUI;
using Xunit;

namespace TseExcel.AddIn.Tests;

public class RibbonContractTests
{
    [Fact]
    public void FileOperations_AreNotPublicStaticMethodsThatExcelDnaCouldExportAsWorksheetFunctions()
    {
        // Excel-DNA discovers public static methods automatically, including file-writing methods.
        Assert.Empty(typeof(TseExcelRibbon).Assembly.GetTypes()
            .SelectMany(type => type.GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly)));
    }

    [Fact]
    public void Ribbon_IsComVisibleAndDeclaresTwoRegisteredButtonCallbacks()
    {
        Type ribbonType = typeof(TseExcelRibbon);
        Assert.True(ribbonType.GetCustomAttribute<ComVisibleAttribute>()?.Value);
        Assert.True(typeof(ExcelRibbon).IsAssignableFrom(ribbonType));
        Assert.NotNull(ribbonType.GetConstructor(Type.EmptyTypes));

        XDocument document = XDocument.Parse(new TseExcelRibbon().GetCustomUI("Microsoft.Excel.Workbook"));
        XNamespace ns = "http://schemas.microsoft.com/office/2006/01/customui";
        XElement tab = Assert.Single(document.Descendants(ns + "tab"));
        Assert.Equal("TSE Excel", (string?)tab.Attribute("label"));
        XElement[] buttons = tab.Descendants(ns + "button").ToArray();
        Assert.Equal(new[] { "Create JSON", "Show JSON" }, buttons.Select(button => (string?)button.Attribute("label")));

        foreach (XElement button in buttons)
        {
            string callback = (string)button.Attribute("onAction")!;
            MethodInfo? method = ribbonType.GetMethod(callback, [typeof(IRibbonControl)]);
            Assert.NotNull(method);
            Assert.Equal(typeof(void), method.ReturnType);
        }
    }
}
