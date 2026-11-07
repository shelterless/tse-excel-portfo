using System.Drawing;
using System.Windows.Forms;
using TseExcel.Application.Trading.OpeningOrders;
using TseExcel.Domain.Trading.Orders;

namespace TseExcel.AddIn.Trading.OpeningOrders.Forms;

internal abstract class OpeningForm : Form
{
    protected readonly TableLayoutPanel ContentLayout;
    private readonly FlowLayoutPanel actions;
    private readonly Label heading;
    protected static readonly Color Accent = Color.FromArgb(23, 91, 112);
    protected static readonly Color Muted = Color.FromArgb(82, 96, 112);
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
        AutoScaleMode = AutoScaleMode.Dpi;
        AutoScaleDimensions = new SizeF(96, 96);
        Font = new Font("Tahoma", 10);
        BackColor = Color.FromArgb(246, 248, 250);
        ForeColor = Color.FromArgb(29, 43, 57);
        ShowInTaskbar = false;
        var frame = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(20, 16, 20, 16), ColumnCount = 1, RowCount = 3 };
        frame.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        frame.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        frame.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        frame.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        heading = new Label { AutoSize = true, Dock = DockStyle.Fill, ForeColor = Accent,
            Font = new Font(Font, FontStyle.Bold), Margin = new Padding(0, 0, 0, 14) };
        frame.Controls.Add(heading, 0, 0);
        var body = new Panel { Dock = DockStyle.Fill, AutoScroll = true, Margin = Padding.Empty };
        ContentLayout = new TableLayoutPanel { Dock = DockStyle.Top, ColumnCount = 2, AutoSize = true, Margin = Padding.Empty };
        ContentLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 43));
        ContentLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 57));
        body.Controls.Add(ContentLayout);
        frame.Controls.Add(body, 0, 1);
        actions = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill, WrapContents = false,
            FlowDirection = FlowDirection.LeftToRight, Padding = new Padding(0, 12, 0, 0), Margin = Padding.Empty };
        frame.Controls.Add(actions, 0, 2);
        Controls.Add(frame);
    }
    protected void Stage(string text) => heading.Text = text;
    protected void FillBody() { ContentLayout.AutoSize = false; ContentLayout.Dock = DockStyle.Fill; }
    protected void Guidance(string text, bool warning = false)
    {
        var label = new Label { Text = text, AutoSize = true, Dock = DockStyle.Fill,
            Padding = new Padding(12), Margin = new Padding(0, 0, 0, 12),
            BackColor = warning ? Color.FromArgb(255, 241, 215) : Color.FromArgb(231, 240, 244),
            ForeColor = warning ? Color.FromArgb(116, 65, 10) : Muted };
        AddWide(label);
    }
    protected void AddWide(Control value, bool fill = false)
    {
        int row = ContentLayout.RowCount++;
        ContentLayout.RowStyles.Add(new RowStyle(fill ? SizeType.Percent : SizeType.AutoSize, fill ? 100 : 0));
        value.Dock = DockStyle.Fill;
        ContentLayout.Controls.Add(value, 0, row);
        ContentLayout.SetColumnSpan(value, 2);
    }
    protected void AddRow(string title, Control value)
    {
        int row = ContentLayout.RowCount++;
        ContentLayout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        ContentLayout.Controls.Add(new Label { Text = title, AutoSize = true, Dock = DockStyle.Fill,
            ForeColor = Muted, Margin = new Padding(0, 7, 8, 7), TextAlign = ContentAlignment.MiddleLeft }, 0, row);
        value.Dock = DockStyle.Fill;
        value.Margin = new Padding(0, 5, 0, 5);
        value.AccessibleName = title;
        ContentLayout.Controls.Add(value, 1, row);
    }
    protected Button AddButton(string text, DialogResult result)
    {
        bool primary = result == DialogResult.OK;
        var button = new Button { Text = text, DialogResult = result, AutoSize = false, Size = new Size(144, 36),
            Margin = new Padding(0, 0, 8, 0), FlatStyle = FlatStyle.Flat,
            BackColor = primary ? Accent : Color.White, ForeColor = primary ? Color.White : ForeColor,
            AccessibleName = text, UseVisualStyleBackColor = false };
        button.FlatAppearance.BorderColor = primary ? Accent : Color.FromArgb(194, 205, 214);
        actions.Controls.Add(button);
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

    internal Button SelectButton { get; }
    internal DraftSelectionForm(IReadOnlyList<OpeningDraft> drafts) : base("انتخاب یک پیش‌نویس مفید", 860, 500)
    {
        this.drafts = drafts;
        Stage("۱ از ۶  •  انتخاب پیش‌نویس");
        FillBody();
        Guidance("یک ردیف را انتخاب کنید. تعداد و قیمت در مرحلهٔ بعد قابل ویرایش است؛ انتخاب، سفارشی ارسال نمی‌کند و پیش‌نویس اصلی تغییر نمی‌کند.");
        Grid = new DataGridView { ReadOnly = true, AllowUserToAddRows = false, AllowUserToDeleteRows = false,
            AutoGenerateColumns = false, MultiSelect = false, SelectionMode = DataGridViewSelectionMode.FullRowSelect,
            ScrollBars = ScrollBars.Vertical, Dock = DockStyle.Fill, RowHeadersVisible = false,
            AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill, Height = 310,
            BackgroundColor = Color.White, BorderStyle = BorderStyle.None, AllowUserToResizeRows = false,
            EnableHeadersVisualStyles = false, ColumnHeadersHeight = 38, ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.DisableResizing,
            AccessibleName = "پیش‌نویس‌های مفید" };
        Grid.DefaultCellStyle.SelectionBackColor = Accent;
        Grid.DefaultCellStyle.SelectionForeColor = Color.White;
        Grid.DefaultCellStyle.Padding = new Padding(6, 2, 6, 2);
        Grid.AlternatingRowsDefaultCellStyle.BackColor = Color.FromArgb(242, 246, 248);
        Grid.ColumnHeadersDefaultCellStyle.BackColor = Color.FromArgb(224, 233, 239);
        Grid.ColumnHeadersDefaultCellStyle.ForeColor = ForeColor;
        Grid.RowTemplate.Height = 34;
        foreach (string title in new[] { "نماد", "جهت", "تعداد", "قیمت واحد (ریال)" }) Grid.Columns.Add(title, title);
        foreach (OpeningDraft draft in drafts)
            Grid.Rows.Add(draft.SymbolName, SideText(draft.Side), Number(draft.Quantity), Number(draft.UnitPriceIrr));
        Grid.Columns[0].FillWeight = 170;
        AddWide(Grid, true);
        AddWide(new Label { Text = drafts.Count == 0 ? "پیش‌نویسی موجود نیست؛ ابتدا در مفید یک پیش‌نویس ذخیره کنید." :
            Number(drafts.Count) + " پیش‌نویس  •  انتخاب با کلیک، کلیدهای جهت یا دوبار کلیک", AutoSize = true, ForeColor = Muted, Padding = new Padding(0, 10, 0, 0) });
        SelectButton = AddButton("انتخاب و ادامه", DialogResult.OK);
        SelectButton.Enabled = false;
        AcceptButton = SelectButton;
        CancelButton = AddButton("انصراف", DialogResult.Cancel);
        Grid.SelectionChanged += (_, _) => SelectButton.Enabled = SelectedDraft is not null;
        Shown += (_, _) => { Grid.Focus(); Grid.ClearSelection(); };
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
    internal Label Validation { get; } = new() { AutoSize = true, ForeColor = Color.FromArgb(160, 63, 28) };
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

    internal OrderDetailsForm(OpeningDraft draft) : base("جزئیات سفارش — " + draft.SymbolName, 560, 470)
    {
        Stage("۲ از ۶  •  جزئیات یک سفارش");
        Guidance("تعداد و قیمت را بررسی کنید. مبلغ با هر تغییر محاسبه می‌شود و فقط مربوط به یک سفارش است.");
        AddRow("نماد", new Label { Text = draft.SymbolName, AutoSize = true });
        AddRow("جهت", new Label { Text = SideText(draft.Side), AutoSize = true });
        QuantityInput = Numeric(draft.Quantity, 0, long.MaxValue);
        PriceInput = Numeric(draft.UnitPriceIrr, 28, decimal.MaxValue);
        AddRow("تعداد", QuantityInput);
        AddRow("قیمت واحد (ریال)", PriceInput);
        AddRow("نرخ کارمزد", fee);
        AddRow("مبلغ یک سفارش (ریال)", total);
        total.Font = new Font(Font.FontFamily, 13, FontStyle.Bold);
        total.ForeColor = Accent;
        AddWide(Validation);
        next = AddButton("ادامه", DialogResult.OK);
        AcceptButton = next;
        CancelButton = AddButton("انصراف", DialogResult.Cancel);
        QuantityInput.TextChanged += (_, _) => TermsChanged?.Invoke(this, EventArgs.Empty);
        PriceInput.TextChanged += (_, _) => TermsChanged?.Invoke(this, EventArgs.Empty);
        Shown += (_, _) => { QuantityInput.Focus(); QuantityInput.Select(0, QuantityInput.Text.Length); };
    }
    internal void SetCost(decimal? rate, decimal? amount, bool allowed)
    {
        fee.Text = rate.HasValue ? Number(rate.Value * 100) + " درصد" : "تأیید نشده";
        total.Text = amount.HasValue ? Number(amount.Value) : "نامشخص";
        next.Enabled = allowed;
        Validation.Text = allowed ? "" : rate.HasValue
            ? "تعداد باید عدد صحیح مثبت و قیمت باید عدد مثبت و دقیق باشد؛ مقدار بزرگ‌تر از ظرفیت محاسبه مجاز نیست."
            : "محاسبات تأیید نشده است؛ ادامه و ارسال مجاز نیست.";
    }
    internal static NumericUpDown Numeric(decimal value, int decimals, decimal maximum) => new CompactNumericInput()
    {
        Minimum = 0, Maximum = maximum, DecimalPlaces = decimals, Value = value,
        ThousandsSeparator = true, TextAlign = HorizontalAlignment.Right, Height = 28, RightToLeft = RightToLeft.No
    };
}

internal sealed class CompactNumericInput : NumericUpDown
{
    internal decimal EnteredValue
    {
        get
        {
            var culture = System.Globalization.CultureInfo.CurrentCulture;
            string entered = new(Text.Select(c => c is >= '\u06f0' and <= '\u06f9' ? (char)('0' + c - '\u06f0') :
                c is >= '\u0660' and <= '\u0669' ? (char)('0' + c - '\u0660') : c).ToArray());
            decimal value = decimal.Parse(entered, System.Globalization.NumberStyles.Number, culture);
            string Normalize(string text)
            {
                var format = culture.NumberFormat;
                string input = text.Trim();
                if (input.StartsWith(format.PositiveSign, StringComparison.Ordinal)) input = input[format.PositiveSign.Length..];
                string sign = input.StartsWith(format.NegativeSign, StringComparison.Ordinal) ? format.NegativeSign : "";
                if (sign.Length > 0) input = input[sign.Length..];
                string[] parts = input.Split(format.NumberDecimalSeparator, StringSplitOptions.None);
                if (parts.Length > 2) throw new FormatException("Invalid decimal input.");
                if (format.NumberGroupSeparator.Length > 0 &&
                    ((parts.Length == 2 && parts[1].Contains(format.NumberGroupSeparator, StringComparison.Ordinal)) ||
                    (parts[0].Contains(format.NumberGroupSeparator, StringComparison.Ordinal) &&
                        parts[0] != decimal.Abs(decimal.Truncate(value)).ToString("#,0", culture))))
                    throw new FormatException("Invalid numeric grouping.");
                string whole = parts[0].Replace(format.NumberGroupSeparator, "", StringComparison.Ordinal).TrimStart('0');
                string fraction = parts.Length == 2 ? parts[1].TrimEnd('0') : "";
                return sign + (whole.Length == 0 ? "0" : whole) + (fraction.Length > 0 ? "." + fraction : "");
            }
            if (Normalize(entered) != Normalize(value.ToString("0.############################", culture)))
                throw new FormatException("The entered value exceeds exact decimal precision.");
            if (value < Minimum || value > Maximum) throw new ArgumentOutOfRangeException(nameof(value), "Input is outside the control's representable range.");
            return value;
        }
    }
    protected override void ValidateEditText()
    {
        try
        {
            decimal entered = EnteredValue;
            UserEdit = false;
            Value = entered;
            UpdateEditText();
        }
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
    internal NumericUpDown Interval { get; } = OrderDetailsForm.Numeric(DispatchSettings.DefaultIntervalMilliseconds, 0, int.MaxValue);
    internal Label Estimate { get; } = new() { AutoSize = true };
    private readonly Button next;
    internal event EventHandler? TimingChanged;
    internal TimeOnly StartTime => new(Whole(Hour), Whole(Minute), Whole(Second));
    internal decimal DurationSeconds => ((CompactNumericInput)Duration).EnteredValue;
    internal int IntervalMilliseconds => Whole(Interval);
    private static int Whole(NumericUpDown input)
    {
        decimal value = ((CompactNumericInput)input).EnteredValue;
        if (value != decimal.Truncate(value)) throw new FormatException("A whole timing component is required.");
        return decimal.ToInt32(value);
    }
    internal DispatchTimingForm() : base("زمان‌بندی ارسال با ساعت ویندوز", 580, 500)
    {
        Stage("۳ از ۶  •  زمان‌بندی با ساعت ویندوز");
        Guidance("شروع: ساعت امروز ویندوز. مدت: طول بازهٔ تلاش‌ها. فاصله: حداقل فاصلهٔ آغاز دو درخواست، به میلی‌ثانیه؛ هر ثانیه هزار میلی‌ثانیه است.");
        AddRow("ساعت شروع", Hour); AddRow("دقیقه", Minute); AddRow("ثانیه", Second);
        AddRow("مدت ارسال (ثانیه)", Duration); AddRow("حداقل فاصله (میلی‌ثانیه)", Interval);
        AddRow("تخمین تعداد تلاش محلی", Estimate);
        Guidance("تخمین، سقف تقریبی تلاش محلی است؛ سرعت شبکه، زمان‌بندی ویندوز، پذیرش سفارش و اولویت صف تضمین نمی‌شود.");
        foreach (NumericUpDown input in new[] { Hour, Minute, Second, Duration, Interval })
            input.TextChanged += (_, _) => TimingChanged?.Invoke(this, EventArgs.Empty);
        next = AddButton("بررسی نهایی", DialogResult.OK);
        AcceptButton = next;
        CancelButton = AddButton("انصراف", DialogResult.Cancel);
        Shown += (_, _) => { Hour.Focus(); Hour.Select(0, Hour.Text.Length); };
    }
    internal void SetValidity(bool valid) { next.Enabled = valid; Estimate.ForeColor = valid ? Accent : Color.FromArgb(160, 63, 28); }
}

internal sealed class FinalConfirmationForm : OpeningForm
{
    internal FinalConfirmationForm(OrderTerms order, DispatchSettings settings) : base("تأیید نهایی ارسال مستقل", 620, 560)
    {
        Stage("۴ از ۶  •  بازبینی و تأیید نهایی");
        Guidance("هر ارسال یک درخواست سفارش مستقل است. ممکن است چند سفارش پذیرفته یا اجرا شوند. تعداد تلاش‌ها نشان‌دهندهٔ پذیرش یا اجرای سفارش نیست. انصراف، سفارش‌های ارسال‌شده را بازنمی‌گرداند.", true);
        AddRow("نماد", new Label { Text = order.SymbolName, AutoSize = true });
        AddRow("جهت", new Label { Text = SideText(order.Side), AutoSize = true });
        AddRow("تعداد", new Label { Text = Number(order.Quantity), AutoSize = true });
        AddRow("قیمت واحد (ریال)", new Label { Text = Number(order.UnitPriceIrr), AutoSize = true });
        AddRow("نرخ کارمزد", new Label { Text = Number(order.CommissionRate * 100) + " درصد", AutoSize = true });
        AddRow("مبلغ یک سفارش (ریال)", new Label { Text = Number(order.TotalIrr), AutoSize = true });
        AddRow("شروع محلی ویندوز", new Label { Text = settings.Start.ToLocalTime().ToString("yyyy/MM/dd HH:mm:ss"), AutoSize = true,
            RightToLeft = RightToLeft.No, TextAlign = ContentAlignment.MiddleRight });
        AddRow("مدت (ثانیه)", new Label { Text = Number((decimal)settings.Duration.TotalSeconds), AutoSize = true });
        AddRow("حداقل فاصله (میلی‌ثانیه)", new Label { Text = Number(settings.Interval.Ticks / (decimal)TimeSpan.TicksPerMillisecond), AutoSize = true });
        AddRow("تخمین تلاش محلی", new Label { Text = Number(settings.EstimatedAttempts), AutoSize = true });
        AddButton("تأیید و شروع", DialogResult.OK);
        CancelButton = AddButton("انصراف", DialogResult.Cancel);
        Shown += (_, _) => ((Button)CancelButton).Focus();
    }
    // Enter is suppressed even when the primary button has focus. Click or focused Space is deliberate approval.
    protected override bool ProcessDialogKey(Keys keyData) => (keyData & Keys.KeyCode) == Keys.Enter || base.ProcessDialogKey(keyData);
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

    internal DispatchExecutionForm(DispatchProgress progress) : base("ارسال سرخطی — آمار محلی", 820, 600)
    {
        this.progress = progress;
        Stage("۵ از ۶  •  شمارش معکوس و ارسال");
        FillBody();
        Guidance("این پنجره فقط تلاش‌های محلی را نشان می‌دهد. توقف، درخواست‌های آغازشده یا سفارش‌های کارگزاری را بازنمی‌گرداند.");
        AddRow("زمان سپری‌شده", elapsed); AddRow("زمان باقی‌مانده", remaining); AddRow("تلاش‌های آغازشدهٔ محلی", count);
        count.ForeColor = Accent; count.Font = new Font(Font, FontStyle.Bold);
        Log.BorderStyle = BorderStyle.FixedSingle;
        Log.BackColor = Color.White;
        Log.AccessibleName = "گزارش زمان و شمارهٔ تلاش‌های محلی";
        AddWide(Log, true);
        AddRow("وضعیت", state);
        state.Text = "در انتظار شروع؛ نتایج کارگزاری بررسی نمی‌شوند.";
        CancelDispatch = AddButton("توقف ارسال‌های بعدی", DialogResult.None);
        CloseButton = AddButton("بستن", DialogResult.OK); CloseButton.Enabled = false;
        ControlBox = false;
        CancelDispatch.Click += (_, _) => { CancelDispatch.Enabled = false; state.Text = "در حال توقف تلاش‌های بعدی…"; CancellationRequested?.Invoke(this, EventArgs.Empty); };
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
        elapsed.Text = progress.Elapsed.ToString(@"hh\:mm\:ss\.fff");
        remaining.Text = progress.Remaining.ToString(@"hh\:mm\:ss\.fff");
        count.Text = OpeningForm.Number(progress.InitiatedAttempts);
        if (!Completed && CancelDispatch.Enabled)
            state.Text = progress.Stage switch
            {
                OpeningOrderStage.Preflight => "در حال بررسی پیش از ارسال؛ هنوز تلاشی ثبت نشده است…",
                OpeningOrderStage.PreparingDispatch => "در حال آماده‌سازی ارسال؛ هنوز تلاشی ثبت نشده است…",
                OpeningOrderStage.WaitingForStart => "بررسی کامل شد؛ در انتظار زمان شروع ویندوز…",
                OpeningOrderStage.Dispatching => "بازهٔ ارسال فعال است؛ نتیجهٔ کارگزاری نامشخص است.",
                _ => "در انتظار شروع و بررسی پیش از ارسال…"
            };
        // Retain every record and preserve the user's scroll position while reading older entries.
    }

    internal void Complete(DispatchSummary? summary, bool failed, string? failureMessage = null, bool authenticationFailed = false)
    {
        timer.Stop();
        progress.Freeze();
        while (true)
        {
            long before = Log.Items.Count;
            RenderBatch();
            if (Log.Items.Count == before) break;
        }
        Completed = true;
        bool noAttempts = progress.InitiatedAttempts == 0;
        bool dispatchStarted = !noAttempts || progress.Stage is OpeningOrderStage.Dispatching or OpeningOrderStage.Completed;
        Stage(failed ? authenticationFailed ? "ورود یا اعتبار نشست تأیید نشد" :
            !dispatchStarted ? "توقف پیش از آغاز ارسال" : "توقف در بازهٔ ارسال" :
            summary?.Cancelled == true ? "عملیات لغو شد" : "۶ از ۶  •  پایان بازهٔ ارسال محلی");
        CancelDispatch.Enabled = false; CloseButton.Enabled = true;
        CloseButton.Focus();
        state.Text = (failed ? (failureMessage ?? "عملیات متوقف شد.") :
            summary?.Cancelled == true ? "آغاز تلاش‌های بعدی لغو شد." : "بازهٔ ارسال پایان یافت.") +
            (noAttempts ? " هیچ تلاش ارسال محلی ثبت نشد." : " نتیجهٔ درخواست‌های آغازشده در کارگزاری نامشخص است؛ خودکار تکرار نکنید.") +
            (failed && dispatchStarted && noAttempts ? " نتیجهٔ درخواست احتمالی نامشخص است؛ خودکار تکرار نکنید." : "") +
            " خطاهای آغاز محلی: " + OpeningForm.Number(progress.InitiationFailures) +
            "؛ این آمار وضعیت سفارش‌های دیگر کارگزاری را مشخص نمی‌کند.";
    }

    protected override void Dispose(bool disposing) { if (disposing) timer.Dispose(); base.Dispose(disposing); }
}

internal sealed class ConnectionForm : OpeningForm
{
    internal event EventHandler? ConnectionRequested;
    internal event EventHandler? CancellationRequested;
    internal ConnectionForm(string title = "ورود به مفید", bool login = true) : base(title, 460, 200)
    {
        Stage(title);
        Guidance(login ? "در صورت نیاز ورود و پیامک یا کپچا را در Chrome تکمیل کنید. نشست فقط تا پایان اجرای فعلی اکسل و افزونه در حافظه می‌ماند." : "در حال دریافت و بررسی اطلاعات مفید؛ لطفاً صبر کنید…");
        AddWide(new ProgressBar { Style = ProgressBarStyle.Marquee, MarqueeAnimationSpeed = 35, Height = 5, Margin = Padding.Empty });
        var cancel = AddButton("انصراف", DialogResult.None);
        void Cancel() { if (!cancel.Enabled) return; cancel.Enabled = false; cancel.Text = "در حال لغو…"; CancellationRequested?.Invoke(this, EventArgs.Empty); }
        cancel.Click += (_, _) => Cancel();
        CancelButton = cancel;
        FormClosing += (_, e) => { if (e.CloseReason == CloseReason.UserClosing && !finished) { e.Cancel = true; Cancel(); } };
        Shown += (_, _) => ConnectionRequested?.Invoke(this, EventArgs.Empty);
    }
    private bool finished;
    internal void Finish() { finished = true; Close(); }
}
