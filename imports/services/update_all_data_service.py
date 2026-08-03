# imports/services/update_all_data_service.py

from time import perf_counter

from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.cache import cache

from imports.services.excel_provider import ExcelProvider


# ✅ الأوامر اللي بتدعم --no-confirm
COMMANDS_WITH_NO_CONFIRM = [
    "import_report_statistics",
    "import_external_approvals",
    "import_report_statistics_sheet15",
]

IMPORT_COMMANDS = [
    ("Package Catalog", "import_package_catalog"),
    ("Contract Migration", "migrate_contract_entities"),
    ("Cash Packages", "import_cash_packages"),
    ("Company Contracts", "import_company_contracts"),
    ("Company Discounts", "import_company_discounts"),
    ("Special Offers", "import_special_offers"),
    ("Service Records", "import_service_records"),
    ("Pricing Details", "import_pricing_details"),
    ("Similar Invoices", "import_similar_invoices"),
    ("Procedures", "import_procedures"),
    ("Medical Procedures", "import_medical_procedures"),
    ("Procedure Fees", "import_procedure_fees"),
    ("Company Discount Rank", "import_company_discount_rank"),
    ("Company Exceptions", "import_company_exceptions"),
    ("Report Statistics", "import_report_statistics"),
    ("External Approvals", "import_external_approvals"),
    ("Report Statistics Sheet 15", "import_report_statistics_sheet15"),
    ("Effective Dates", "import_effective_dates"),  # ✅ إضافة
]

POST_IMPORT_COMMANDS = [
    ("Normalize Categories", "normalize_categories"),
]


class UpdateAllDataService:

    @classmethod
    def run(cls, stdout, progress_callback=None):

        stdout.write("")
        stdout.write("=" * 70)
        stdout.write("      MIH Automated Pricing System")
        stdout.write("        Update All Data")
        stdout.write("=" * 70)

        total_start = perf_counter()

        # ✅ مسح Cache الـ Excel
        ExcelProvider.clear_cache()

        results = []
        total_commands = len(IMPORT_COMMANDS) + len(POST_IMPORT_COMMANDS)

        try:

            # ============================================================
            # ✅ 1. تنفيذ أوامر الاستيراد
            # ============================================================
            for idx, (title, command_name) in enumerate(IMPORT_COMMANDS):

                if progress_callback:
                    progress_callback(title, idx)

                stdout.write("")
                stdout.write("-" * 70)
                stdout.write(f"▶ START : {title}")
                stdout.flush()

                start = perf_counter()

                try:

                    if command_name in COMMANDS_WITH_NO_CONFIRM:
                        call_command(
                            command_name,
                            stdout=stdout,
                            no_confirm=True,
                        )
                    else:
                        call_command(
                            command_name,
                            stdout=stdout,
                        )

                    elapsed = perf_counter() - start
                    results.append({"title": title, "status": "✅", "time": elapsed})
                    stdout.write(f"✅ END : {title} ({elapsed:.2f} sec)")

                except Exception as exc:

                    elapsed = perf_counter() - start
                    results.append({"title": title, "status": "❌", "time": elapsed})
                    stdout.write(f"❌ {title} Failed")
                    stdout.write(f"   Error: {str(exc)}")
                    stdout.write("   Continuing with remaining commands...")

                stdout.flush()

            # ============================================================
            # ✅ 2. تنفيذ أوامر ما بعد الاستيراد (توحيد البيانات)
            # ============================================================
            stdout.write("")
            stdout.write("=" * 70)
            stdout.write("📋 POST-IMPORT: توحيد البيانات...")
            stdout.write("=" * 70)

            for idx, (title, command_name) in enumerate(POST_IMPORT_COMMANDS):

                if progress_callback:
                    progress_callback(title, len(IMPORT_COMMANDS) + idx)

                stdout.write("")
                stdout.write("-" * 70)
                stdout.write(f"▶ START : {title}")
                stdout.flush()

                start = perf_counter()

                try:
                    call_command(
                        command_name,
                        stdout=stdout,
                    )

                    elapsed = perf_counter() - start
                    results.append({"title": title, "status": "✅", "time": elapsed})
                    stdout.write(f"✅ END : {title} ({elapsed:.2f} sec)")

                except Exception as exc:

                    elapsed = perf_counter() - start
                    results.append({"title": title, "status": "⚠️", "time": elapsed})
                    stdout.write(f"⚠️ {title} Failed (skipping)")
                    stdout.write(f"   Error: {str(exc)}")
                    stdout.write("   Continuing with remaining commands...")

                stdout.flush()

        finally:

            # ✅ مسح Cache الـ Excel
            ExcelProvider.clear_cache()

            # ✅ مسح Cache الـ Django بالكامل
            try:
                cache.clear()
                stdout.write("\n✅ Django cache cleared successfully")
            except Exception as e:
                stdout.write(f"\n⚠️ Failed to clear Django cache: {str(e)}")

            # ✅ مسح Cache المخصص للشركات والباكدجات (باستخدام delete فقط)
            try:
                cache.delete('active_companies_list')
                # ✅ مسح كل مفاتيح Cache اللي تبدأ بـ packages_company_
                from django.core.cache import caches
                for key in list(cache._cache.keys()):
                    if key.startswith('packages_company_') or key.startswith('specialties_company_'):
                        cache.delete(key)
                stdout.write("\n✅ Company packages cache cleared successfully")
            except Exception as e:
                stdout.write(f"\n⚠️ Failed to clear company cache: {str(e)}")

            if progress_callback:
                progress_callback("✅ تم الانتهاء", total_commands)

        total_elapsed = perf_counter() - total_start

        stdout.write("")
        stdout.write("=" * 70)
        stdout.write("✓ ALL IMPORTS COMPLETED SUCCESSFULLY")
        stdout.write(f"Total Time : {total_elapsed:.2f} sec")
        stdout.write("=" * 70)

        stdout.write("")
        stdout.write("📊 SUMMARY:")
        for r in results:
            stdout.write(f"   {r['status']} {r['title']} ({r['time']:.2f}s)")
        stdout.write("=" * 70)
        stdout.write("")