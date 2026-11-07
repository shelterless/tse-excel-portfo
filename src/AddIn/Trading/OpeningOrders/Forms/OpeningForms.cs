using System.Drawing;
using System.Windows.Forms;
using TseExcel.Application.Trading.OpeningOrders;
using TseExcel.Domain.Trading.Orders;

namespace TseExcel.AddIn.Trading.OpeningOrders.Forms;

internal abstract class OpeningForm : Form
{
    protected readonly TableLayoutPanel ContentLayout;
    protected OpeningForm(string title, int width, int height)
    {
        Text = title;
        ClientSize = new Size(width, height);
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = false;
        StartPosition = FormStartPosition.CenterScreen;
        RightToLeft = RightToLeft.Yes;
        RightToLeftLayout = true;
        Font = new Font("Tahoma", 10);
        ContentLayout = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(12), ColumnCount = 2, AutoScroll = true };
        ContentLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 40));
        ContentLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 60));
        Controls.Add(ContentLayout);
    }
    protected void AddRow(string title, Control value)
    {
        int row = ContentLayout.RowCount++;
        ContentLayout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        ContentLayout.Controls.Add(new Label { Text = title, AutoSize = true, Margin = new Padding(4, 9, 4, 9) }, 0, row);
        value.Dock = DockStyle.Fill;
        ContentLayout.Controls.Add(value, 1, row);
    }
    protected Button AddButton(string text, DialogResult result)
    {
        var button = new Button { Text = text, DialogResult = result, AutoSize = true, MinimumSize = new Size(100, 32) };
        AddRow("", button);
        return button;
    }
    internal static string SideText(OrderSide side) => side == OrderSide.Buy ? "خرید" : "فروش";
    internal static string Number(decimal number) => number.ToString("#,0.############################", System.Globalization.CultureInfo.CurrentCulture);
}

internal sealed class DraftSelectionForm : OpeningForm
{
    internal DataGridView Grid { get; }
    private readonly IReadOnlyList<OpeningDraft> drafts;
    internal OpeningDraft? SelectedDraft => Grid.SelectedRows.Count == 1 ? drafts[Grid.SelectedRows[0].Index] : null;

    internal DraftSelectionForm(IReadOnlyList<OpeningDraft> drafts) : base("انتخاب یک پیش‌نویس مفید", 780, 430)
    {
        this.drafts = drafts;
        Grid = new DataGridView { ReadOnly = true, AllowUserToAddRows = false, AllowUserToDeleteRows = false,
            AutoGenerateColumns = false, MultiSelect = false, SelectionMode = DataGridViewSelectionMode.FullRowSelect,
            ScrollBars = ScrollBars.Vertical, Dock = DockStyle.Fill, RowHeadersVisible = false,
            AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill, Height = 310 };
        foreach (string title in new[] { "نماد", "نام ابزار", "جهت", "تعداد", "قیمت واحد (ریال)" }) Grid.Columns.Add(title, title);
        foreach (OpeningDraft draft in drafts)
            Grid.Rows.Add(draft.SymbolName, draft.SymbolName, SideText(draft.Side), Number(draft.Quantity), Number(draft.UnitPriceIrr));
        AddRow("پیش‌نویس‌ها", Grid);
        ContentLayout.RowStyles[0] = new RowStyle(SizeType.Percent, 100);
        AcceptButton = AddButton("انتخاب", DialogResult.OK);
        CancelButton = AddButton("انصراف", DialogResult.Cancel);
        Shown += (_, _) => Grid.ClearSelection();
        FormClosing += (_, e) => { if (DialogResult == DialogResult.OK && SelectedDraft is null) e.Cancel = true; };
        Grid.CellDoubleClick += (_, e) => { if (e.RowIndex >= 0 && SelectedDraft is not null) { DialogResult = DialogResult.OK; Close(); } };
    }
}

internal sealed class OrderDetailsForm : OpeningForm
{
    internal NumericUpDown QuantityInput { get; }
    internal NumericUpDown PriceInput { get; }
    private readonly Label total = new() { AutoSize = true };
    private readonly Label fee = new() { AutoSize = true };
    private readonly Button next;
    internal event EventHandler? TermsChanged;
    internal long Quantity
    {
        get
        {
            decimal quantity = ((CompactNumericInput)QuantityInput).EnteredValue;
            if (quantity != decimal.Truncate(quantity)) throw new FormatException("Quantity must be a whole number.");
            return decimal.ToInt64(quantity);
        }
    }
    internal decimal Price => ((CompactNumericInput)PriceInput).EnteredValue;

    internal OrderDetailsForm(OpeningDraft draft) : base("جزئیات سفارش — " + draft.SymbolName, 480, 390)
    {
        AddRow("نماد و نام ابزار", new Label { Text = draft.SymbolName, AutoSize = true });
        AddRow("جهت", new Label { Text = SideText(draft.Side), AutoSize = true });
        QuantityInput = Numeric(draft.Quantity, 0, long.MaxValue);
        PriceInput = Numeric(draft.UnitPriceIrr, 28, decimal.MaxValue);
        AddRow("تعداد", QuantityInput);
        AddRow("قیمت واحد (ریال)", PriceInput);
        AddRow("نرخ کارمزد", fee);
        AddRow("مبلغ یک سفارش (ریال)", total);
        next = AddButton("ادامه", DialogResult.OK);
        AcceptButton = next;
        CancelButton = AddButton("انصراف", DialogResult.Cancel);
        QuantityInput.TextChanged += (_, _) => TermsChanged?.Invoke(this, EventArgs.Empty);
        PriceInput.TextChanged += (_, _) => TermsChanged?.Invoke(this, EventArgs.Empty);
    }
    internal void SetCost(decimal? rate, decimal? amount, bool allowed)
    {
        fee.Text = rate.HasValue ? Number(rate.Value * 100) + " درصد" : "تأیید نشده";
        total.Text = amount.HasValue ? Number(amount.Value) : "نامشخص";
        next.Enabled = allowed;
    }
    internal static NumericUpDown Numeric(decimal value, int decimals, decimal maximum) => new CompactNumericInput()
    {
        Minimum = 0, Maximum = maximum, DecimalPlaces = decimals, Value = value,
        ThousandsSeparator = true, TextAlign = HorizontalAlignment.Right, Height = 28
    };
}

internal sealed class CompactNumericInput : NumericUpDown
{
    internal decimal EnteredValue
    {
        get
        {
            var culture = System.Globalization.CultureInfo.CurrentCulture;
            decimal value = decimal.Parse(Text, System.Globalization.NumberStyles.Number, culture);
            string Normalize(string text)
            {
                var format = culture.NumberFormat;
                string input = text.Trim().Replace(format.NumberGroupSeparator, "", StringComparison.Ordinal);
                if (input.StartsWith(format.PositiveSign, StringComparison.Ordinal)) input = input[format.PositiveSign.Length..];
                string sign = input.StartsWith(format.NegativeSign, StringComparison.Ordinal) ? format.NegativeSign : "";
                if (sign.Length > 0) input = input[sign.Length..];
                string[] parts = input.Split(format.NumberDecimalSeparator, StringSplitOptions.None);
                if (parts.Length > 2) throw new FormatException("Invalid decimal input.");
                string whole = parts[0].TrimStart('0');
                string fraction = parts.Length == 2 ? parts[1].TrimEnd('0') : "";
                return sign + (whole.Length == 0 ? "0" : whole) + (fraction.Length > 0 ? "." + fraction : "");
            }
            if (Normalize(Text) != Normalize(value.ToString("0.############################", culture)))
                throw new FormatException("The entered value exceeds exact decimal precision.");
            if (value < Minimum || value > Maximum) throw new ArgumentOutOfRangeException(nameof(value), "Input is outside the control's representable range.");
            return value;
        }
    }
    protected override void ValidateEditText()
    {
        try { _ = EnteredValue; base.ValidateEditText(); }
        catch (Exception exception) when (exception is FormatException or OverflowException or ArgumentOutOfRangeException)
        {
            // Preserve invalid text for correction instead of silently rounding or clamping it.
        }
    }
    protected override void UpdateEditText()
    {
        ChangingText = true;
        Text = OpeningForm.Number(Value);
        UserEdit = false;
    }
}

internal sealed class DispatchTimingForm : OpeningForm
{
    internal NumericUpDown Hour { get; } = OrderDetailsForm.Numeric(8, 0, 23);
    internal NumericUpDown Minute { get; } = OrderDetailsForm.Numeric(44, 0, 59);
    internal NumericUpDown Second { get; } = OrderDetailsForm.Numeric(58, 0, 59);
    internal NumericUpDown Duration { get; } = OrderDetailsForm.Numeric(DispatchSettings.DefaultDurationSeconds, 6, 86400);
    internal NumericUpDown Interval { get; } = OrderDetailsForm.Numeric(DispatchSettings.DefaultIntervalMicroseconds, 0, int.MaxValue);
    internal Label Estimate { get; } = new() { AutoSize = true };
    internal event EventHandler? TimingChanged;
    internal TimeOnly StartTime => new(Whole(Hour), Whole(Minute), Whole(Second));
    internal decimal DurationSeconds => ((CompactNumericInput)Duration).EnteredValue;
    internal int IntervalMicroseconds => Whole(Interval);
    private static int Whole(NumericUpDown input)
    {
        decimal value = ((CompactNumericInput)input).EnteredValue;
        if (value != decimal.Truncate(value)) throw new FormatException("A whole timing component is required.");
        return decimal.ToInt32(value);
    }
    internal DispatchTimingForm() : base("زمان‌بندی ارسال با ساعت ویندوز", 500, 400)
    {
        AddRow("ساعت شروع", Hour); AddRow("دقیقه", Minute); AddRow("ثانیه", Second);
        AddRow("مدت ارسال (ثانیه)", Duration); AddRow("حداقل فاصله (میکروثانیه)", Interval);
        AddRow("تخمین تعداد تلاش محلی", Estimate);
        foreach (NumericUpDown input in new[] { Hour, Minute, Second, Duration, Interval })
            input.TextChanged += (_, _) => TimingChanged?.Invoke(this, EventArgs.Empty);
        AcceptButton = AddButton("ادامه", DialogResult.OK);
        CancelButton = AddButton("انصراف", DialogResult.Cancel);
    }
}

internal sealed class FinalConfirmationForm : OpeningForm
{
    internal FinalConfirmationForm(OrderTerms order, DispatchSettings settings) : base("تأیید نهایی ارسال مستقل", 560, 590)
    {
        AddRow("نماد و ابزار", new Label { Text = order.SymbolName, AutoSize = true });
        AddRow("جهت", new Label { Text = SideText(order.Side), AutoSize = true });
        AddRow("تعداد", new Label { Text = Number(order.Quantity), AutoSize = true });
        AddRow("قیمت واحد (ریال)", new Label { Text = Number(order.UnitPriceIrr), AutoSize = true });
        AddRow("نرخ کارمزد", new Label { Text = Number(order.CommissionRate * 100) + " درصد", AutoSize = true });
        AddRow("مبلغ یک سفارش (ریال)", new Label { Text = Number(order.TotalIrr), AutoSize = true });
        AddRow("شروع محلی ویندوز", new Label { Text = settings.Start.ToLocalTime().ToString("yyyy/MM/dd HH:mm:ss"), AutoSize = true });
        AddRow("مدت (ثانیه)", new Label { Text = Number((decimal)settings.Duration.TotalSeconds), AutoSize = true });
        AddRow("حداقل فاصله (میکروثانیه)", new Label { Text = Number(settings.Interval.Ticks / 10m), AutoSize = true });
        AddRow("تخمین تلاش محلی", new Label { Text = Number(settings.EstimatedAttempts), AutoSize = true });
        AddRow("هشدار", new Label { Text = "هر ارسال یک درخواست سفارش مستقل است. ممکن است چند سفارش پذیرفته یا اجرا شوند. تعداد تلاش‌ها نشان‌دهندهٔ پذیرش یا اجرای سفارش نیست. انصراف، سفارش‌های ارسال‌شده را بازنمی‌گرداند.", AutoSize = true, MaximumSize = new Size(310, 0) });
        AddButton("تأیید و شروع", DialogResult.OK);
        CancelButton = AddButton("انصراف", DialogResult.Cancel);
        // No default Enter-key approval: the user must deliberately select the primary action.
    }
}

internal sealed class DispatchExecutionForm : OpeningForm
{
    internal ListBox Log { get; } = new() { Dock = DockStyle.Fill, IntegralHeight = false, HorizontalScrollbar = true,
        ScrollAlwaysVisible = true, RightToLeft = RightToLeft.No, Font = new Font("Consolas", 10), Height = 280 };
    private readonly Label elapsed = new() { AutoSize = true };
    private readonly Label remaining = new() { AutoSize = true };
    private readonly Label count = new() { AutoSize = true };
    private readonly Label state = new() { AutoSize = true, MaximumSize = new Size(430, 0) };
    internal Button CancelDispatch { get; }
    internal Button CloseButton { get; }
    private readonly System.Windows.Forms.Timer timer = new() { Interval = 100 };
    private readonly DispatchProgress progress;
    internal bool Completed { get; private set; }
    internal event EventHandler? CancellationRequested;
    internal event EventHandler? ExecutionRequested;

    internal DispatchExecutionForm(DispatchProgress progress) : base("ارسال سرخطی — آمار محلی", 780, 620)
    {
        this.progress = progress;
        AddRow("زمان سپری‌شده", elapsed); AddRow("زمان باقی‌مانده", remaining); AddRow("تلاش‌های آغازشدهٔ محلی", count);
        AddRow("گزارش محلی", Log);
        ContentLayout.RowStyles[3] = new RowStyle(SizeType.Percent, 100);
        AddRow("وضعیت", state);
        state.Text = "در انتظار شروع؛ نتایج کارگزاری بررسی نمی‌شوند.";
        CancelDispatch = AddButton("توقف ارسال‌های بعدی", DialogResult.None);
        CloseButton = AddButton("بستن", DialogResult.OK); CloseButton.Enabled = false;
        ControlBox = false;
        CancelDispatch.Click += (_, _) => { CancelDispatch.Enabled = false; CancellationRequested?.Invoke(this, EventArgs.Empty); };
        timer.Tick += (_, _) => RenderBatch();
        Shown += (_, _) => { timer.Start(); ExecutionRequested?.Invoke(this, EventArgs.Empty); };
        FormClosing += (_, e) => { if (!Completed) e.Cancel = true; };
    }

    internal void RenderBatch()
    {
        IReadOnlyList<DispatchRecord> records = progress.Drain(2000);
        Log.BeginUpdate();
        try { foreach (DispatchRecord record in records) Log.Items.Add(record.Format()); }
        finally { Log.EndUpdate(); }
        elapsed.Text = progress.Elapsed.ToString(@"hh\:mm\:ss\.ffffff");
        remaining.Text = progress.Remaining.ToString(@"hh\:mm\:ss\.ffffff");
        count.Text = OpeningForm.Number(progress.InitiatedAttempts);
        // Retain every record and preserve the user's scroll position while reading older entries.
    }

    internal void Complete(DispatchSummary? summary, bool failed)
    {
        timer.Stop();
        while (true)
        {
            long before = Log.Items.Count;
            RenderBatch();
            if (Log.Items.Count == before) break;
        }
        Completed = true;
        CancelDispatch.Enabled = false; CloseButton.Enabled = true;
        state.Text = (failed ? "عملیات متوقف شد؛ نتیجهٔ کارگزاری نامشخص است. خودکار تکرار نکنید." :
            summary?.Cancelled == true ? "ارسال‌های بعدی متوقف شدند." : "بازهٔ ارسال پایان یافت.") +
            " خطاهای آغاز محلی: " + OpeningForm.Number(progress.InitiationFailures) +
            "؛ پذیرش و اجرا بررسی نشده‌اند. سفارش‌های کارگزاری را در پنل مفید بررسی کنید.";
    }

    protected override void Dispose(bool disposing) { if (disposing) timer.Dispose(); base.Dispose(disposing); }
}

internal sealed class ConnectionForm : OpeningForm
{
    internal event EventHandler? ConnectionRequested;
    internal event EventHandler? CancellationRequested;
    internal ConnectionForm(string title = "ورود به مفید", bool login = true) : base(title, 520, 200)
    {
        AddRow("وضعیت", new Label { Text = login ? "در صورت نیاز، در پنجرهٔ Chrome وارد شوید و مراحل پیامک یا کپچا را خودتان تکمیل کنید. پس از ورود، پنجرهٔ ورود بسته می‌شود." : "در حال دریافت اطلاعات از مفید…", AutoSize = true, MaximumSize = new Size(300, 0) });
        var cancel = AddButton("انصراف", DialogResult.None);
        cancel.Click += (_, _) => { cancel.Enabled = false; CancellationRequested?.Invoke(this, EventArgs.Empty); };
        ControlBox = false;
        Shown += (_, _) => ConnectionRequested?.Invoke(this, EventArgs.Empty);
    }
}
