# TSE Excel Portfolio

**TSE Excel Portfolio** (`tse-excel-portfo`) — پروژه ساخت افزونه مستقل Excel برای دریافت، اعتبارسنجی و نمایش داده‌های بازار سرمایه ایران، با تمرکز اولیه بر اطلاعات نمادها، وضعیت معاملاتی، صف خرید/فروش و رفتار معاملاتی حقیقی/حقوقی.

> **وضعیت فعلی:** مخزن در مرحله **تعریف محصول و مستندسازی معماری** است. هنوز Solution، افزونه C#، فایل XLL، نصب‌کننده، تست خودکار یا فایل Workbook به‌عنوان خروجی این ریپو ساخته و تأیید نشده‌اند.

## هدف

انتقال منطق نمونه Excel/VBA قبلی به یک معماری قابل تست و قابل توسعه **C#/.NET + Excel-DNA**؛ به شکلی که Excel رابط کاربری و محل نمایش جدول‌ها/فرمول‌ها باشد و کد مربوط به دریافت و پردازش TSETMC در کتابخانه‌های کامپایل‌شده اجرا شود. برنامه باید با نمادهای متوقف، داده ناقص و خطای API به‌صورت ایمن برخورد کند و داده‌ها و فرمول‌های کاربر را حفظ کند.

## دامنه MVP

- افزونه C# مبتنی بر Excel-DNA/XLL، با Build و نصب **محلی**؛
- اتصال به TSETMC برای دریافت داده نمادها؛
- Refresh جدول نمادهای Excel با تطبیق امن `InsCode` و بدون تخریب فرمول‌های دستی؛
- تشخیص و گزارش وضعیت نماد، تازگی/ناقص‌بودن داده و خطا؛
- رابط مناسب Excel برای اجرای Refresh و مشاهده نتیجه.

**خارج از MVP:** VBA/VB در محصول جدید، Auto-Updater، سرویس اشتراک/لایسنس، Backend اختصاصی، تجاری‌سازی و موتور Python. افزودن هرکدام در آینده مستلزم تصمیم جداگانه است.

نسخه‌های دقیق .NET، Excel-DNA، سازگاری Office/Windows، روش نصب و قرارداد نهایی Workbook هنوز تأیید نشده‌اند؛ مستندات فنی زیر تصمیم‌های باز را صریحاً مشخص می‌کنند.

## مستندات

مرجع مستندات کانتکس ChatGPT در [docs/gpt](docs/gpt/README.md) است:

| سند | کاربرد |
|---|---|
| [Project Instructions](docs/gpt/PROJECT-INSTRUCTIONS.md) | Bootstrap بسیار کوتاه برای ChatGPT Project Instructions |
| [Context Index](docs/gpt/README.md) | راهنمای Lazy Loading و انتخاب فایل فقط بر اساس کار |
| [Project Context](docs/gpt/PROJECT-CONTEXT.md) | هدف، محدوده و موارد خارج از MVP |
| [Architecture](docs/gpt/ARCHITECTURE.md) | مرز لایه‌ها و پیشنهاد معماری |
| [Workbook Contract](docs/gpt/WORKBOOK-CONTRACT.md) | ساختار مشاهده‌شده Excel نمونه، فیلدها و فرمول‌ها |
| [Data Reliability](docs/gpt/DATA-RELIABILITY.md) | TSETMC، وضعیت توقف، تازگی و سیاست برخورد با خطا |
| [Development Workflow](docs/gpt/DEVELOPMENT-WORKFLOW.md) | ساخت، تست، تحویل و تجربه توسعه |
| [Governance](docs/gpt/GOVERNANCE.md) | تأیید تغییرات، GitHub و همگام‌سازی کانتکس |
| [Decisions](docs/gpt/DECISIONS.md) | مصوبات و سؤال‌های باز |
| [Changelog](docs/gpt/CHANGELOG.md) | تاریخچه تغییرات کانتکس |

## راه‌اندازی ChatGPT Project

نام پیشنهادی: **Mohsen-Portfo-TSE-Excel**.

1. یک ChatGPT Project جدید بساز.
2. فقط **محتوای** [docs/gpt/PROJECT-INSTRUCTIONS.md](docs/gpt/PROJECT-INSTRUCTIONS.md) را در بخش **Project Instructions** کپی کن.
3. فایل‌های دیگر `docs/gpt/` را به **Project Sources** اضافه کن (به‌ویژه `README.md` همان پوشه به‌عنوان راهنمای بارگذاری تنبل).
4. در درخواست‌های جدید، از ChatGPT بخواه نسخه فعلی `main` را از GitHub بررسی کند و **فقط سند مرتبط با همان کار** را بخواند. Project Sources نسخه‌های کپی‌شده‌اند و به‌صورت خودکار با GitHub Sync نمی‌شوند.
5. پس از تأیید تو، هر تغییر کانتکس در GitHub ثبت می‌شود؛ فایل‌های تغییریافته را در Sources جایگزین کن. **تنها اگر Project Instructions عوض شد**، متن Bootstrap را هم در تنظیمات پروژه جایگزین کن.

## توسعه

برای اولین فاز توسعه، ابتدا نسخه واقعی Workbook و محیط هدف Excel/Windows/.NET تأیید می‌شوند؛ سپس Solution و افزونه به‌صورت عمودی (دریافت داده، پردازش، Refresh و تست) پیاده‌سازی خواهد شد. ساختار احتمالی سورس در سند [Architecture](docs/gpt/ARCHITECTURE.md) آمده و تا ایجاد واقعی، صرفاً **پیشنهاد** است.

## امنیت و حریم خصوصی

**این مخزن در زمان تهیه مستندات Public است.** هیچ داده شخصی پرتفوی/کارگزاری، رمز، توکن، فایل مشتری یا الگوریتم محرمانه نباید در آن commit شود. فایل‌های نمونه باید ساختگی یا پاک‌سازی‌شده باشند. اگر قرار است منطق تجاری اختصاصی نگهداری شود، ابتدا سیاست دسترسی و خصوصی‌بودن مخزن را تعیین کن.

---

**منبع حقیقت:** برنچ [`main`](https://github.com/shelterless/tse-excel-portfo/tree/main)؛ به‌روزرسانی اسناد GPT پس از تأیید کاربر، مطابق [Governance](docs/gpt/GOVERNANCE.md).
