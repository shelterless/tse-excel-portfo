using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using System.Windows.Forms;
using ExcelDna.Integration;
using ExcelDna.Integration.CustomUI;
using Microsoft.CSharp.RuntimeBinder;
using TseExcel.AddIn.Composition;
using TseExcel.AddIn.ExcelInterop;
using TseExcel.Application.WorkbookJson;

namespace TseExcel.AddIn.Ribbon;

[ComVisible(true)]
public class TseExcelRibbon : ExcelRibbon
{
    private readonly WorkbookJsonCommands commands;
    private readonly Func<string?> getActiveWorkbookFullName;
    private readonly Action<string, MessageBoxIcon> showMessage;

    public TseExcelRibbon() : this(
        AddInComposition.CreateWorkbookJsonCommands(),
        new ExcelWorkbook(() => ExcelDnaUtil.Application).GetActiveFullName,
        ShowMessage)
    {
    }

    internal TseExcelRibbon(WorkbookJsonCommands commands, Func<string?> getActiveWorkbookFullName,
        Action<string, MessageBoxIcon> showMessage)
    {
        this.commands = commands;
        this.getActiveWorkbookFullName = getActiveWorkbookFullName;
        this.showMessage = showMessage;
    }

    public override string GetCustomUI(string ribbonId) => """
        <customUI xmlns="http://schemas.microsoft.com/office/2006/01/customui">
          <ribbon>
            <tabs>
              <tab id="tseExcelTab" label="TSE Excel">
                <group id="tseExcelJsonGroup" label="Workbook JSON">
                  <button id="tseExcelCreateJson" label="Create JSON" onAction="OnCreateJson" />
                  <button id="tseExcelShowJson" label="Show JSON" onAction="OnShowJson" />
                </group>
              </tab>
            </tabs>
          </ribbon>
        </customUI>
        """;

    public void OnCreateJson(IRibbonControl control) => Execute(workbookFullName =>
    {
        WorkbookJsonCreation result = commands.Create(workbookFullName);
        showMessage(result.Created
            ? $"JSON created:\n{result.JsonPath}"
            : $"JSON already exists and was left unchanged:\n{result.JsonPath}", MessageBoxIcon.Information);
    });

    public void OnShowJson(IRibbonControl control) => Execute(workbookFullName =>
        showMessage(commands.Read(workbookFullName), MessageBoxIcon.Information));

    private void Execute(Action<string?> action)
    {
        try
        {
            action(getActiveWorkbookFullName());
        }
        catch (JsonException exception)
        {
            showMessage($"The JSON file is malformed.\n{exception.Message}", MessageBoxIcon.Warning);
        }
        catch (DecoderFallbackException exception)
        {
            showMessage($"The JSON file contains invalid text encoding.\n{exception.Message}", MessageBoxIcon.Warning);
        }
        catch (FileNotFoundException exception)
        {
            showMessage($"File not found. Save the workbook and use Create JSON if needed.\n{exception.FileName}", MessageBoxIcon.Warning);
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or
            System.Security.SecurityException or ArgumentException or NotSupportedException or
            InvalidOperationException or COMException or RuntimeBinderException)
        {
            showMessage($"Unable to complete the workbook JSON command.\n{exception.Message}", MessageBoxIcon.Warning);
        }
    }

    private static void ShowMessage(string message, MessageBoxIcon icon) =>
        MessageBox.Show(message, "TSE Excel", MessageBoxButtons.OK, icon);
}
