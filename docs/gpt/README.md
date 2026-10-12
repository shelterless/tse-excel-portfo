# GPT Context Index — TSE Excel

این پوشه مرجع مستندات مربوط به توسعه پروژه در ChatGPT است. **این فایل نقشه راه بارگذاری تنبل است، نه دستور خواندن همه فایل‌ها.**

## مرجع و تقدم اطلاعات

1. گفته صریح و جدید کاربر در گفت‌وگوی جاری؛
2. وضعیت واقعی و فایل‌های مرتبط از `main` ریپوی `shelterless/tse-excel-portfo`؛
3. شواهد اجرا و تست‌های ارائه‌شده؛
4. نسخه‌های کپی‌شده در ChatGPT Project Sources؛
5. گفت‌وگوهای قدیمی و دانش عمومی.

قوانین قرارداد، تصمیم‌های مصوب و وضعیت اجرایی را از `main` بررسی کن؛ هر تناقض مؤثر میان این منابع را توضیح بده و **قبل از انتخاب یکی برای تغییرات حساس، سؤال بپرس**. فرض نکن متن Project Sources خودش با Git همگام می‌شود. اگر اتصال GitHub فراهم نبود، محدودیت را بگو و فایل/لینک یا دسترسی لازم را درخواست کن؛ ادعای خواندن `main` نکن.

## بارگذاری بر اساس کار

| نوع درخواست | فقط این فایل‌ها را بخوان |
|---|---|
| معرفی، هدف و مرزبندی محصول | [PROJECT-CONTEXT.md](PROJECT-CONTEXT.md) |
| طراحی ساختار یا انتخاب فناوری | [PROJECT-CONTEXT.md](PROJECT-CONTEXT.md) و [ARCHITECTURE.md](ARCHITECTURE.md) و در صورت تصمیم جدید [DECISIONS.md](DECISIONS.md) |
| Excel، ستون‌ها، فرمول‌ها و نگاشت فیلد | [WORKBOOK-CONTRACT.md](WORKBOOK-CONTRACT.md) |
| TSETMC، وضعیت نماد و خطا/تازگی داده | [DATA-RELIABILITY.md](DATA-RELIABILITY.md) و بخش مرتبط از [WORKBOOK-CONTRACT.md](WORKBOOK-CONTRACT.md) |
| پیاده‌سازی، تست، Build و تحویل | [DEVELOPMENT-WORKFLOW.md](DEVELOPMENT-WORKFLOW.md)؛ معماری را فقط در صورت لزوم |
| تغییر در کانتکس، ثبت تصمیم یا Git | [GOVERNANCE.md](GOVERNANCE.md) و فایل هدف؛ برای تصمیم معماری [DECISIONS.md](DECISIONS.md) |
| تاریخچه تصمیم‌های معماری | [DECISIONS.md](DECISIONS.md)؛ در صورت نیاز [CHANGELOG.md](CHANGELOG.md) |

`PROJECT-INSTRUCTIONS.md` فایل Bootstrap کپی‌شدنی در تنظیمات ChatGPT Project است؛ در هر درخواست نیازی به بازخوانی دوباره آن نیست اگر از قبل در Project Instructions موجود باشد.

## قواعد مستندسازی

- واقعیت تأییدشده، تصمیم ثبت‌شده، پیشنهاد، فرض کاری و موضوع باز را از هم جدا کن.
- کد یا فایل را فقط وقتی «پیاده‌سازی/تست/منتشر شده» بنام که شواهد واقعی وجود داشته باشد.
- به‌روزرسانی اسناد کانتکس فقط پس از تأیید کاربر؛ تغییرات را در کمترین فایل لازم انجام بده.
- وقتی فایل‌های کانتکس در Git عوض شدند، نام فایل‌های موردنیاز برای جایگزینی در Project Sources را گزارش کن.
- `PROJECT-INSTRUCTIONS.md` را حداقلی نگه دار. فقط با تغییر همان فایل، همگام‌سازی دستی ChatGPT Project Instructions لازم است.
