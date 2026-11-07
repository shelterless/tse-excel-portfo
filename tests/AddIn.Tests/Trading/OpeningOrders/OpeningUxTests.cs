using System.Drawing;
using System.Reflection;
using System.Runtime.ExceptionServices;
using System.Windows.Forms;
using TseExcel.AddIn.Trading.OpeningOrders;
using TseExcel.AddIn.Trading.OpeningOrders.Forms;
using TseExcel.Application.Trading.OpeningOrders;
using TseExcel.Domain.Trading.Orders;
using Xunit;

namespace TseExcel.AddIn.Tests.Trading.OpeningOrders;

public class OpeningUxTests
{
    private static OpeningDraft Draft => new("fixture", "IRO1TEST0001", "ابزار آزمایشی", OrderSide.Buy, 1000, 2000, 0);

    [Fact]
    public void FakeDraftToDetails_InitializesEditsAndRejectsInvalidInputsWithoutSending() => Sta(() =>
    {
        var broker = new Broker();
        OpeningDraft draft = Assert.Single(broker.GetDraftsAsync(CancellationToken.None).GetAwaiter().GetResult());
        using var selection = new DraftSelectionForm(new[] { draft });
        Show(selection);
        Assert.Null(selection.SelectedDraft); Assert.False(selection.SelectButton.Enabled);
        Assert.Same(selection.Grid, selection.ActiveControl);
        selection.Grid.Rows[0].Selected = true;
        Assert.True(selection.SelectButton.Enabled);
        Assert.Same(draft, selection.SelectedDraft);
        InstrumentFees fees = broker.GetFeesAsync(selection.SelectedDraft!, CancellationToken.None).GetAwaiter().GetResult();
        using var details = new OrderDetailsForm(selection.SelectedDraft!);
        void Update() => OpeningOrderPresenter.RecalculateDetails(draft, fees, details);
        details.TermsChanged += (_, _) => Update();
        Update(); Show(details);
        Assert.Same(details.QuantityInput, details.ActiveControl);
        Assert.Equal(2_000_738m, OpeningOrderPresenter.RecalculateDetails(draft, fees, details)!.TotalIrr);
        details.QuantityInput.Text = "22"; details.PriceInput.Text = "56593";
        Assert.True(((Button)details.AcceptButton!).Enabled);
        Assert.Equal(1_245_506m, OpeningOrderPresenter.RecalculateDetails(draft, fees, details)!.TotalIrr);
        foreach (string invalid in new[] { "", "0", "-1", "1.5", "9223372036854775808" })
        {
            details.QuantityInput.Text = invalid;
            Assert.Null(OpeningOrderPresenter.RecalculateDetails(draft, fees, details));
            Assert.False(((Button)details.AcceptButton!).Enabled);
            Assert.NotEmpty(details.Validation.Text);
        }
        details.QuantityInput.Text = "22"; details.PriceInput.Text = "0.00000000000000000000000000001";
        Assert.Null(OpeningOrderPresenter.RecalculateDetails(draft, fees, details));
        details.PriceInput.Text = "56593";
        Assert.True(((Button)details.AcceptButton!).Enabled);
        Assert.Equal(1000, draft.Quantity); Assert.Equal(2000m, draft.UnitPriceIrr);
        Assert.Equal(0, broker.DispatchCalls);
    });

    [Theory]
    [InlineData(1f)]
    [InlineData(1.5f)]
    [InlineData(2f)]
    public void Stages_KeepButtonsCompactAndContentWithinScrollableBody(float scale) => Sta(() =>
    {
        var fees = new InstrumentFees(.00036875m, 0, null);
        var order = fees.CreateOrder(Draft, Draft.Quantity, Draft.UnitPriceIrr);
        var settings = new DispatchSettings(new DateTimeOffset(2026, 11, 7, 8, 44, 58, TimeSpan.FromHours(3.5)), 5, 350);
        var progress = new DispatchProgress();
        OpeningForm[] forms = [new ConnectionForm(), new DraftSelectionForm(Enumerable.Range(1, 40).Select(i => Draft with { Id = i.ToString() }).ToArray()),
            new OrderDetailsForm(Draft), new DispatchTimingForm(), new FinalConfirmationForm(order, settings), new DispatchExecutionForm(progress)];
        try
        {
            foreach (OpeningForm form in forms)
            {
                if (form is OrderDetailsForm details) details.SetCost(order.CommissionRate, order.TotalIrr, true);
                Show(form);
                if (scale != 1) form.Scale(new SizeF(scale, scale));
                Layout(form);
                Assert.Equal(RightToLeft.Yes, form.RightToLeft);
                Assert.True(form.RightToLeftLayout);
                Assert.Equal(AutoScaleMode.Dpi, form.AutoScaleMode);
                Assert.All(Controls(form).OfType<Button>(), button =>
                {
                    Assert.InRange(button.Width, (int)(130 * scale), (int)(160 * scale));
                    Assert.InRange(button.Height, (int)(32 * scale), (int)(42 * scale));
                    Assert.True(button.Parent!.ClientRectangle.Contains(button.Bounds), form.GetType().Name + ": action clipped");
                });
                foreach (TableLayoutPanel table in Controls(form).OfType<TableLayoutPanel>())
                    Assert.True(table.Width <= table.Parent!.ClientSize.Width, form.GetType().Name + ": content too wide");
                foreach (Label label in Controls(form).OfType<Label>().Where(label => label.AutoSize && label.Text.Length > 0))
                    Assert.True(label.Height >= label.GetPreferredSize(new Size(label.Width, 0)).Height,
                        form.GetType().Name + ": label clipped");
                if (form is DraftSelectionForm selection) Assert.True(selection.Grid.Height > 200 * scale);
                if (form is DispatchExecutionForm execution)
                {
                    Assert.True(execution.Log.Height > 180 * scale);
                    execution.Complete(new(0, 0, TimeSpan.Zero, true), false);
                    Assert.All(Controls(execution).OfType<Button>().Where(b => b.Enabled), b => Assert.Same(execution.CloseButton, b));
                }
                string? preview = Environment.GetEnvironmentVariable("TSE_UX_PREVIEW_DIRECTORY");
                if (preview is not null && scale == 1)
                {
                    Directory.CreateDirectory(preview);
                    using var bitmap = new Bitmap(form.Width, form.Height);
                    form.DrawToBitmap(bitmap, new Rectangle(Point.Empty, bitmap.Size));
                    bitmap.Save(Path.Combine(preview, form.GetType().Name + ".png"));
                }
                form.Hide();
            }
        }
        finally { foreach (OpeningForm form in forms) form.Dispose(); }
    });

    [Fact]
    public void Confirmation_EnterCannotApproveEvenWhenPrimaryHasFocus() => Sta(() =>
    {
        var order = new InstrumentFees(.001m, 0, null).CreateOrder(Draft, 1000, 2000);
        using var form = new FinalConfirmationForm(order, new(DateTimeOffset.Now.AddHours(1), 5, 350));
        Show(form);
        Assert.Same(form.CancelButton, form.ActiveControl);
        Assert.Null(form.AcceptButton);
        var primary = Controls(form).OfType<Button>().Single(b => b.DialogResult == DialogResult.OK);
        primary.Focus();
        MethodInfo method = typeof(FinalConfirmationForm).GetMethod("ProcessDialogKey", BindingFlags.NonPublic | BindingFlags.Instance)!;
        Assert.Equal(true, method.Invoke(form, new object[] { Keys.Enter }));
        Assert.Equal(DialogResult.None, form.DialogResult);
        primary.PerformClick();
        Assert.Equal(DialogResult.OK, form.DialogResult);
    });

    [Fact]
    public void Connection_CancellationIsSingleShotAndWaitsForWorkerCleanup() => Sta(() =>
    {
        using var form = new ConnectionForm();
        int calls = 0; form.CancellationRequested += (_, _) => calls++;
        Show(form);
        form.Close(); form.Close();
        Assert.Equal(1, calls); Assert.True(form.Visible);
        Assert.False(((Button)form.CancelButton!).Enabled);
        form.Finish(); Assert.False(form.Visible);
    });

    [Fact]
    public void EmptyDraftsAndTimingValidity_ProvideGuidanceAndGateContinuation() => Sta(() =>
    {
        using var empty = new DraftSelectionForm(Array.Empty<OpeningDraft>());
        Assert.False(empty.SelectButton.Enabled); Assert.Null(empty.SelectedDraft);
        Assert.Contains(Controls(empty), c => c.Text.Contains("پیش‌نویسی موجود نیست"));
        using var timing = new DispatchTimingForm();
        Show(timing); Assert.Same(timing.Hour, timing.ActiveControl);
        timing.SetValidity(false); Assert.False(((Button)timing.AcceptButton!).Enabled);
        timing.SetValidity(true); Assert.True(((Button)timing.AcceptButton!).Enabled);
    });

    [Theory]
    [InlineData("en-US", "۱,۲۳۴.۱۲۵")]
    [InlineData("fa-IR", "۱٬۲۳۴٫۱۲۵")]
    public void NumericInput_PreservesPersianDigitsAndRejectsMalformedGrouping(string culture, string input) => Sta(() =>
    {
        var previous = System.Globalization.CultureInfo.CurrentCulture;
        try
        {
            System.Globalization.CultureInfo.CurrentCulture = new System.Globalization.CultureInfo(culture);
            using var form = new OrderDetailsForm(Draft);
            form.PriceInput.Text = input;
            Assert.Equal(1234.125m, form.Price);
            string separator = System.Globalization.CultureInfo.CurrentCulture.NumberFormat.NumberGroupSeparator;
            form.PriceInput.Text = "1" + separator + "2";
            Assert.Throws<FormatException>(() => form.Price);
            form.PriceInput.Text = "1234";
            Assert.Equal(1234m, form.Price);
        }
        finally { System.Globalization.CultureInfo.CurrentCulture = previous; }
    });

    [Fact]
    public void ErrorCategories_HaveDistinctSanitizedPersianGuidance()
    {
        var messages = Enum.GetValues<OpeningOrderError>().Select(category =>
            OpeningOrderPresenter.ErrorText(new OpeningOrderException("private fixture data", category))).ToArray();
        Assert.Equal(messages.Length, messages.Distinct().Count());
        Assert.All(messages, message => Assert.DoesNotContain("private fixture data", message));
        Assert.DoesNotContain("private fixture data", OpeningOrderPresenter.ErrorText(new Exception("private fixture data")));
    }

    private static void Show(Form form) { form.Show(); System.Windows.Forms.Application.DoEvents(); }
    private static void Layout(Control control)
    {
        control.PerformLayout();
        foreach (Control child in control.Controls) Layout(child);
        control.PerformLayout();
    }
    private static IEnumerable<Control> Controls(Control parent) => parent.Controls.Cast<Control>()
        .SelectMany(child => new[] { child }.Concat(Controls(child)));
    private static void Sta(Action action)
    {
        Exception? failure = null;
        var thread = new Thread(() => { try { action(); } catch (Exception exception) { failure = exception; } });
        thread.SetApartmentState(ApartmentState.STA); thread.Start(); thread.Join();
        if (failure is not null) ExceptionDispatchInfo.Capture(failure).Throw();
    }
    private sealed class Broker : IOpeningOrderBroker
    {
        internal int DispatchCalls { get; private set; }
        public Task AuthenticateAsync(bool refresh, CancellationToken cancellationToken) => Task.CompletedTask;
        public Task<IReadOnlyList<OpeningDraft>> GetDraftsAsync(CancellationToken cancellationToken) => Task.FromResult<IReadOnlyList<OpeningDraft>>(new[] { Draft });
        public Task<InstrumentFees> GetFeesAsync(OpeningDraft draft, CancellationToken cancellationToken) => Task.FromResult(new InstrumentFees(.00036875m, 0, null));
        public Task ValidateAsync(OpeningDraft draft, OrderTerms order, DispatchSettings settings, CancellationToken cancellationToken) => throw new InvalidOperationException("Unexpected preflight in details-only fixture.");
        public Task<IOrderDispatch> OpenDispatchAsync(OrderTerms order, DateTimeOffset cutoff, CancellationToken cancellationToken)
        { DispatchCalls++; throw new InvalidOperationException("Unexpected dispatch in details-only fixture."); }
        public ValueTask DisposeAsync() => ValueTask.CompletedTask;
    }
}
