using System.Runtime.ExceptionServices;
using System.Windows.Forms;
using TseExcel.AddIn.Composition;
using TseExcel.AddIn.Ribbon;
using TseExcel.AddIn.Trading.OpeningOrders.Forms;
using TseExcel.Application.Trading.OpeningOrders;
using TseExcel.Application.WorkbookJson;
using TseExcel.Domain.Trading.Orders;
using Xunit;

namespace TseExcel.AddIn.Tests.Trading.OpeningOrders;

public class OpeningFormsTests
{
    [Fact]
    public void DraftGrid_SelectsExactlyOneActualRowAndPreservesInheritedSide() => Sta(() =>
    {
        OpeningDraft buy = Draft(); OpeningDraft sell = buy with { Id = "sell", Side = OrderSide.Sell };
        using var form = new DraftSelectionForm(new[] { buy, sell });
        Assert.True(form.Grid.ReadOnly); Assert.False(form.Grid.MultiSelect);
        Assert.Equal(ScrollBars.Vertical, form.Grid.ScrollBars);
        form.Grid.ClearSelection(); Assert.Null(form.SelectedDraft);
        form.Grid.Rows[1].Selected = true;
        Assert.Same(sell, form.SelectedDraft);
        Assert.Equal("فروش", form.Grid.Rows[1].Cells[2].Value);
        Assert.Equal(5, form.Grid.Columns.Count);
    });

    [Fact]
    public void OrderDetails_InitializeFromDraftAndRaiseImmediateEditEvents() => Sta(() =>
    {
        using var form = new OrderDetailsForm(Draft());
        Assert.Contains(Draft().SymbolName, form.Text);
        Assert.Equal(1000, form.Quantity); Assert.Equal(2000m, form.Price);
        int edits = 0; form.TermsChanged += (_, _) => edits++;
        form.QuantityInput.Value = 500; form.PriceInput.Value = 2500.125m;
        Assert.Equal(2, edits); Assert.Equal(500, form.Quantity); Assert.Equal(2500.125m, form.Price);
        form.PriceInput.Value = .0000000000000000000000000001m;
        Assert.Equal(.0000000000000000000000000001m, form.Price);
        int beforeTyping = edits;
        form.PriceInput.Text = "1234";
        Assert.Equal(1234m, form.Price); Assert.True(edits > beforeTyping);
        form.QuantityInput.Text = "1.5";
        Assert.Throws<FormatException>(() => form.Quantity);
        form.PriceInput.Text = "0.00000000000000000000000000001";
        Assert.Throws<FormatException>(() => form.Price);
        form.SetCost(.001m, 1251313m, true);
        Assert.True(((Button)form.AcceptButton!).Enabled);
        form.SetCost(null, null, false);
        Assert.False(((Button)form.AcceptButton!).Enabled);
    });

    [Fact]
    public void TimingAndConfirmation_UseApprovedDefaultsAndRequireDeliberateApproval() => Sta(() =>
    {
        using var timing = new DispatchTimingForm();
        Assert.Equal(DispatchSettings.DefaultStart, timing.StartTime);
        Assert.Equal(5m, timing.Duration.Value); Assert.Equal(350m, timing.Interval.Value);
        int changes = 0; timing.TimingChanged += (_, _) => changes++;
        timing.Interval.Value = 400; Assert.Equal(1, changes);
        timing.Hour.Text = "99";
        Assert.Throws<ArgumentOutOfRangeException>(() => timing.StartTime);
        timing.Duration.Text = "1.25";
        Assert.Equal(1.25m, timing.DurationSeconds);
        var order = new InstrumentFees(.001m, 0m, null).CreateOrder(Draft(), 1000, 2000);
        using var confirmation = new FinalConfirmationForm(order, new(DateTimeOffset.Now.AddHours(1), 5, 350));
        Assert.Null(confirmation.AcceptButton);
        string text = string.Join(" ", AllControls(confirmation).Select(c => c.Text));
        Assert.Contains("هر ارسال یک درخواست سفارش مستقل است", text);
        Assert.Contains("تأیید و شروع", text); Assert.Contains("انصراف", text);
        Assert.DoesNotContain("balance", text, StringComparison.OrdinalIgnoreCase);
    });

    [Fact]
    public async Task Log_BatchesAllRecordsIntoOneFixedScrollableControlAndFreezesOnCompletion()
    {
        var clock = new Clock(); var progress = new DispatchProgress();
        await new DispatchEngine(clock).RunAsync(new(clock.LocalNow, 1m, 350), new Transport(clock), progress, CancellationToken.None);
        Sta(() =>
        {
            using var form = new DispatchExecutionForm(progress);
            var size = form.Size; int controls = AllControls(form).Count();
            form.RenderBatch(); Assert.Equal(2000, form.Log.Items.Count);
            form.Complete(new(progress.InitiatedAttempts, 0, progress.Elapsed, false), false);
            Assert.Equal(2858, form.Log.Items.Count);
            Assert.Equal(size, form.Size); Assert.Equal(controls, AllControls(form).Count());
            Assert.Equal(FormBorderStyle.FixedDialog, form.FormBorderStyle); Assert.False(form.MaximizeBox);
            Assert.True(form.Log.ScrollAlwaysVisible); Assert.False(form.Log.IntegralHeight);
            Assert.True(form.Completed); Assert.False(form.CancelDispatch.Enabled); Assert.True(form.CloseButton.Enabled);
            Assert.All(form.Log.Items.Cast<string>(), line => Assert.DoesNotContain('\n', line));
            Assert.StartsWith("08:44:58.000000 | #000001", (string)form.Log.Items[0]);
        });
    }

    [Fact]
    public void RibbonTradingActions_DoNotAccessWorkbookAndLifecycleDoesNotAuthenticateAtStartup()
    {
        var calls = new List<bool>();
        var ribbon = new TseExcelRibbon(new WorkbookJsonCommands(new UnusedStore()),
            () => throw new InvalidOperationException("Trading must not access Excel COM."), (_, _) => { }, calls.Add);
        ribbon.OnMofidLogin(null!); ribbon.OnOpeningOrder(null!);
        Assert.Equal(new[] { true, false }, calls);
        var lifecycle = new MofidAddInLifecycle(); lifecycle.AutoOpen(); lifecycle.AutoClose();
    }

    [Fact]
    public void Presenter_MarshalsWorkOffUiThreadAndSanitizesUserDiagnostics()
    {
        string source = File.ReadAllText(Path.Combine(ArchitectureContractTests.FindRepositoryRoot(), "src", "AddIn", "Trading", "OpeningOrders", "OpeningOrderPresenter.cs"));
        Assert.Contains("Task.Run", source);
        Assert.Contains("ExecuteConfirmedAsync", source);
        Assert.Contains("TermsChanged", source);
        Assert.DoesNotContain("exception.Message", source);
        Assert.DoesNotContain("TseExcel.Infrastructure", source);
    }

    private static OpeningDraft Draft() => new("fixture", "IRO1TEST0001", "Fixture", OrderSide.Buy, 1000, 2000, 0);
    private static IEnumerable<Control> AllControls(Control parent)
    {
        foreach (Control child in parent.Controls)
        {
            yield return child;
            foreach (Control descendant in AllControls(child)) yield return descendant;
        }
    }
    private static void Sta(Action action)
    {
        Exception? failure = null;
        var thread = new Thread(() => { try { action(); } catch (Exception exception) { failure = exception; } });
        thread.SetApartmentState(ApartmentState.STA); thread.Start(); thread.Join();
        if (failure is not null) ExceptionDispatchInfo.Capture(failure).Throw();
    }
    private sealed class Clock : IDispatchClock
    {
        public DateTimeOffset LocalNow => new DateTimeOffset(2026, 11, 7, 8, 44, 58, TimeSpan.Zero) + Elapsed;
        public TimeSpan Elapsed { get; private set; }
        public Task WaitUntilAsync(TimeSpan deadline, CancellationToken cancellationToken) { Elapsed = deadline; return Task.CompletedTask; }
    }
    private sealed class Transport(Clock clock) : IOrderDispatch
    {
        public Task<LocalInitiation> InitiateAsync(DateTimeOffset timestamp, CancellationToken cancellationToken) => Task.FromResult(new LocalInitiation(true, clock.LocalNow, false));
        public ValueTask DisposeAsync() => ValueTask.CompletedTask;
    }
    private sealed class UnusedStore : IWorkbookJsonStore
    {
        public string ResolvePath(string? path) => throw new NotSupportedException();
        public bool CreateIfMissing(string path) => throw new NotSupportedException();
        public string Read(string path) => throw new NotSupportedException();
    }
}
