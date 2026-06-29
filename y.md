🥇 1. تنظيف الـ Import System (أعلى أولوية)

دلوقتى عندك أكتر من Service فيها نفس الدوال:

normalize_text
clean_decimal
clean_percentage
clean_date
normalize_package_codes

كلهم بقوا موجودين فى ImportHelpers.

المطلوب:

✅ حذف النسخ المكررة من الـ Services.
✅ استخدام ImportHelpers فقط.

النتيجة:

كود أقل.
صيانة أسهل.
أى تعديل يتم مرة واحدة.
🥈 2. عمل Import Summary احترافى

بدل:

processed : 14816
created : 0
updated : 14816

يبقى:

==============================
Packages Processed : 18301
Created Packages   : 42
Updated Packages   : 18259

Entities Created   : 0
Contracts Created  : 0

Missing Codes      : 2
Missing Prices     : 139

Done Successfully
==============================

وده هيسهل جدًا معرفة أى مشكلة بعد كل Import.

🥉 3. إضافة Logging

بدل ما تطبع:

print(...)

يبقى عندك:

logs/import_2026-06-29.txt

يتسجل فيه:

Missing Codes
Missing Prices
Package Not Found
Duplicate Packages

لو الدكتور قال "فى شركة ناقصة"، هتفتح اللوج بدل ما تعيد التجارب.

🏅 4. حذف البيانات القديمة تلقائيًا (Cleanup)

مثلاً:

is_active=False

اللى بقاله شهر.

أو

package_code = nan

القديمة.

نعمل Management Command:

python manage.py cleanup_contracts

ينضف قاعدة البيانات.

🏅 5. تحسين البحث فى الموقع

الـ Dropdown حاليًا بيبحث بالاسم.

ممكن يخلى البحث يدعم:

اسم الباكدج.
الكود.
جزء من الاسم.
عربى وإنجليزى.
🏅 6. Dashboard للإحصائيات

صفحة Admin فيها:

عدد الشركات

عدد العقود

عدد الباكدجات

عدد الباكدجات النشطة

آخر Import

آخر تحديث

ده هيبقى مفيد للدكتور.

🏅 7. Backup تلقائى

قبل كل Import:

db.sqlite3

يتنسخ إلى:

backup/

لو الدكتور بعت ملف غلط ترجع فى دقيقة.

🏅 8. جعل الحذف من الإكسيل ينعكس فى النظام

دلوقتى:

الإضافة ✔
التعديل ✔
الحذف ❌

المفروض لو الدكتور حذف صف من الإكسيل:

ContractPackage.is_active=False

أو يتحذف.

وده هيخلى قاعدة البيانات مطابقة للإكسيل 100%.

🏅 9. Cache

الشركات والباكدجات بتتقرأ كتير.

نضيف:

Redis

أو حتى

LocMemCache

الصفحة هتبقى أسرع.

🏅 10. اختبارات (Tests)

خصوصًا للـ Import.

يعنى ملف فيه:

نفس الكود.
أكثر من اسم.
شركة بدون كود.
سعر فارغ.

نتأكد إن كل حاجة شغالة بعد أى تعديل.