using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using System.Windows.Forms;
using ExcelDna.Integration.CustomUI;
using Microsoft.CSharp.RuntimeBinder;

namespace TseExcel.AddIn;

[ComVisible(true)]
public class TseExcelRibbon : ExcelRibbon
{
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

    public void OnCreateJson(IRibbonControl control) => Execute(jsonPath =>
    {
        bool created = WorkbookJsonFile.CreateIfMissing(jsonPath);
        ShowMessage(created
            ? $"JSON created:\n{jsonPath}"
            : $"JSON already exists and was left unchanged:\n{jsonPath}", MessageBoxIcon.Information);
    });

    public void OnShowJson(IRibbonControl control) => Execute(jsonPath =>
        ShowMessage(WorkbookJsonFile.Read(jsonPath), MessageBoxIcon.Information));

    private static void Execute(Action<string> action)
    {
        try
        {
            action(ExcelWorkbook.GetActiveJsonPath());
        }
        catch (JsonException exception)
        {
            ShowMessage($"The JSON file is malformed.\n{exception.Message}", MessageBoxIcon.Warning);
        }
        catch (DecoderFallbackException exception)
        {
            ShowMessage($"The JSON file contains invalid text encoding.\n{exception.Message}", MessageBoxIcon.Warning);
        }
        catch (FileNotFoundException exception)
        {
            ShowMessage($"File not found. Save the workbook and use Create JSON if needed.\n{exception.FileName}", MessageBoxIcon.Warning);
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or
            System.Security.SecurityException or ArgumentException or NotSupportedException or
            InvalidOperationException or COMException or RuntimeBinderException)
        {
            ShowMessage($"Unable to complete the workbook JSON command.\n{exception.Message}", MessageBoxIcon.Warning);
        }
    }

    private static void ShowMessage(string message, MessageBoxIcon icon) =>
        MessageBox.Show(message, "TSE Excel", MessageBoxButtons.OK, icon);
}
