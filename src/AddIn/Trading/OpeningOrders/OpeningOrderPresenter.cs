using System.Windows.Forms;
using TseExcel.AddIn.Trading.OpeningOrders.Forms;
using TseExcel.Application.Trading.OpeningOrders;
using TseExcel.Domain.Trading.Orders;

namespace TseExcel.AddIn.Trading.OpeningOrders;

internal sealed class OpeningOrderPresenter(IOpeningOrderBroker broker)
{
    private bool active;

    internal void Show(bool loginOnly)
    {
        if (active) { Notify("یک عملیات مفید در حال اجراست."); return; }
        active = true;
        try
        {
            if (loginOnly)
            {
                if (Load("ورود به مفید", true, async token => { await broker.AuthenticateAsync(true, token).ConfigureAwait(false); return true; }, out bool loggedIn) && loggedIn)
                    Notify("ورود انجام شد. نشست برای استفادهٔ بعدی در حافظه نگهداری می‌شود.");
                return;
            }
            if (!Load("دریافت پیش‌نویس‌ها", true, broker.GetDraftsAsync, out IReadOnlyList<OpeningDraft>? drafts)) return;
            if (drafts!.Count == 0) { Notify("پیش‌نویسی برای انتخاب وجود ندارد."); return; }
            using var selection = new DraftSelectionForm(drafts);
            if (selection.ShowDialog() != DialogResult.OK || selection.SelectedDraft is not OpeningDraft draft) return;
            using var details = new OrderDetailsForm(draft);
            if (draft.Side == OrderSide.Sell)
            {
                details.SetCost(null, null, false);
                Notify("نمایش پیش‌نویس فروش مجاز است؛ محاسبات و ارسال زندهٔ فروش هنوز تأیید نشده‌اند.");
                details.ShowDialog();
                return;
            }
            if (draft.ValidityType != 0) { Notify("این آزمایش فقط سفارش خرید با اعتبار روز را پشتیبانی می‌کند."); return; }
            if (!Load("دریافت مشخصات ابزار", false, token => broker.GetFeesAsync(draft, token), out InstrumentFees? fees)) return;
            OrderTerms? order = null;
            void Recalculate()
            {
                try
                {
                    order = fees!.CreateOrder(draft, details.Quantity, details.Price);
                    details.SetCost(order.CommissionRate, order.TotalIrr, true);
                }
                catch (Exception exception) when (exception is ArgumentException or OverflowException or FormatException)
                {
                    order = null;
                    details.SetCost(fees!.CommissionRate, null, false);
                }
            }
            details.TermsChanged += (_, _) => Recalculate();
            Recalculate();
            if (details.ShowDialog() != DialogResult.OK || order is null) return;
            using var timing = new DispatchTimingForm();
            DispatchSettings? settings = null;
            void UpdateTiming()
            {
                try
                {
                    settings = new(DispatchSettings.TodayLocal(timing.StartTime, DateTimeOffset.Now), timing.DurationSeconds, timing.IntervalMicroseconds);
                    timing.Estimate.Text = OpeningForm.Number(settings.EstimatedAttempts) + " (تقریبی؛ بدون تضمین)";
                }
                catch (Exception exception) when (exception is ArgumentException or OverflowException or FormatException)
                {
                    settings = null;
                    timing.Estimate.Text = "زمان امروز باید در آینده و مقادیر مثبت باشند.";
                }
            }
            timing.TimingChanged += (_, _) => UpdateTiming();
            UpdateTiming();
            while (timing.ShowDialog() == DialogResult.OK)
            {
                UpdateTiming();
                if (settings is not null) break;
                Notify("زمان شروع امروز باید در آینده باشد؛ مدت و فاصله باید مثبت باشند.");
            }
            if (timing.DialogResult != DialogResult.OK || settings is null) return;
            using var confirmation = new FinalConfirmationForm(order, settings);
            if (confirmation.ShowDialog() != DialogResult.OK) return;
            Execute(draft, order, settings);
        }
        catch (Exception exception)
        {
            System.Diagnostics.Trace.WriteLine("Opening-order presentation failed: " + exception.GetType().Name);
            Notify("عملیات انجام نشد. اطلاعات، نشست یا زمان‌بندی را بررسی کنید. نتیجهٔ هیچ سفارشی از این پیام قابل استنتاج نیست.");
        }
        finally { active = false; }
    }

    private void Execute(OpeningDraft draft, OrderTerms order, DispatchSettings settings)
    {
        var progress = new DispatchProgress();
        using var cancellation = new CancellationTokenSource();
        using var form = new DispatchExecutionForm(progress);
        form.CancellationRequested += (_, _) => cancellation.Cancel();
        form.ExecutionRequested += async (_, _) =>
        {
            DispatchSummary? summary = null;
            bool failed = false;
            try
            {
                summary = await Task.Run(() => new OpeningOrderWorkflow(broker, new SystemDispatchClock())
                    .ExecuteConfirmedAsync(draft, order, settings, true, progress, cancellation.Token));
            }
            catch (OperationCanceledException) when (cancellation.IsCancellationRequested)
            { summary = new(progress.InitiatedAttempts, progress.InitiationFailures, progress.Elapsed, true); }
            catch (Exception exception)
            {
                System.Diagnostics.Trace.WriteLine("Opening-order execution stopped: " + exception.GetType().Name);
                failed = true;
            }
            form.Complete(summary, failed);
        };
        form.ShowDialog();
    }

    private static bool Load<T>(string title, bool login, Func<CancellationToken, Task<T>> work, out T? result)
    {
        using var form = new ConnectionForm(title, login);
        using var cancellation = new CancellationTokenSource();
        T? value = default;
        bool completed = false;
        form.CancellationRequested += (_, _) => cancellation.Cancel();
        form.ConnectionRequested += async (_, _) =>
        {
            try { value = await Task.Run(() => work(cancellation.Token)); completed = true; }
            catch (OperationCanceledException) when (cancellation.IsCancellationRequested) { }
            catch (Exception exception)
            {
                System.Diagnostics.Trace.WriteLine("Mofid operation failed: " + exception.GetType().Name);
                Notify("ارتباط یا اعتبارسنجی اطلاعات مفید انجام نشد. در صورت نیاز دوباره وارد شوید؛ اطلاعات تأییدنشده جایگزین نمی‌شود.");
            }
            finally { form.Close(); }
        };
        form.ShowDialog();
        result = value;
        return completed;
    }

    private static void Notify(string message) => MessageBox.Show(message, "مفید", MessageBoxButtons.OK, MessageBoxIcon.Information);
}
