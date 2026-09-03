from time import perf_counter

from django.core.management import call_command
from django.db import close_old_connections  # ✅ تم إضافة هذا الـ import
from django.core.cache import cache

from imports.services.excel_provider import ExcelProvider
from imports.services.progress_service import ProgressService
from imports.exceptions import TaskCancelled


COMMANDS_WITH_NO_CONFIRM = [
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
    ("Pricing Requests", "import_pricing_requests"),
    ("Similar Invoices", "import_similar_invoices"),
    ("Procedures", "import_procedures"),
    ("Medical Procedures", "import_medical_procedures"),
    ("Procedure Fees", "import_procedure_fees"),
    ("Company Discount Rank", "import_company_discount_rank"),
    ("Company Exceptions", "import_company_exceptions"),
    ("Report Statistics", "import_report_statistics"),
    ("External Approvals", "import_external_approvals"),
    ("Report Statistics Sheet 15", "import_report_statistics_sheet15"),
    ("Effective Dates", "import_effective_dates"),
]


POST_IMPORT_COMMANDS = [
    ("Normalize Categories", "normalize_categories"),
]


# ⚡ تحديث سريع: Sheet 7 + Sheet 12
QUICK_UPDATE_COMMANDS = [
    ("Pricing Details", "import_pricing_details"),
    ("Pricing Requests", "import_pricing_requests"),
    ("External Approvals", "import_external_approvals"),
]


PACKAGE_COUNT_COMMANDS = {
    "import_package_catalog",
    "migrate_contract_entities",
    "import_cash_packages",
}


class UpdateAllDataService:

    @classmethod
    def run(cls, stdout, progress_callback=None, commands=None):

        stdout.write("")
        stdout.write("=" * 70)
        stdout.write("      MIH Automated Pricing System")
        stdout.write("        Update All Data")
        stdout.write("=" * 70)

        total_start = perf_counter()

        ExcelProvider.clear_cache()

        results = []

        if commands is None:
            commands = IMPORT_COMMANDS + POST_IMPORT_COMMANDS

        commands = list(commands)
        total_commands = len(commands)

        try:

            # ============================================================
            # تنفيذ الأوامر
            # ============================================================

            for idx, (title, command_name) in enumerate(commands):

                # --------------------------------------------------------
                # فحص الإلغاء قبل بدء الأمر
                # --------------------------------------------------------

                if ProgressService.is_cancel_requested():
                    raise TaskCancelled()

                if progress_callback:
                    progress_callback(title, idx)

                stdout.write("")
                stdout.write("-" * 70)
                stdout.write(f"▶ START : {title}")
                stdout.flush()

                stdout.write(
                    f"RUNNING => {command_name}"
                )
                stdout.flush()

                start = perf_counter()

                try:

                    # ✅ إغلاق الاتصالات القديمة قبل كل أمر
                    close_old_connections()

                    # ----------------------------------------------------
                    # تشغيل Command
                    # ----------------------------------------------------

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

                    stdout.write(
                        f"FINISHED => {command_name}"
                    )
                    stdout.flush()

                    # ----------------------------------------------------
                    # Package Count
                    # ----------------------------------------------------

                    if command_name in PACKAGE_COUNT_COMMANDS:

                        from medical_catalog.models import Package

                        stdout.write(
                            f"Packages Count = "
                            f"{Package.objects.count()}"
                        )

                    # ----------------------------------------------------
                    # فحص الإلغاء بعد انتهاء الأمر
                    # ----------------------------------------------------

                    if ProgressService.is_cancel_requested():
                        raise TaskCancelled()

                    elapsed = perf_counter() - start

                    results.append({
                        "title": title,
                        "status": "✅",
                        "time": elapsed,
                    })

                    stdout.write(
                        f"✅ END : "
                        f"{title} "
                        f"({elapsed:.2f} sec)"
                    )

                except TaskCancelled:
                    raise

                except Exception as exc:

                    elapsed = perf_counter() - start

                    results.append({
                        "title": title,
                        "status": "❌",
                        "time": elapsed,
                        "error": str(exc),
                    })

                    stdout.write(
                        f"❌ {title} Failed"
                    )

                    stdout.write(
                        f"   Error: {str(exc)}"
                    )

                    stdout.write(
                        "   Continuing with remaining commands..."
                    )

                stdout.flush()

        finally:

            # ============================================================
            # تنظيف الـCache
            # ============================================================

            ExcelProvider.clear_cache()

            try:

                cache.clear()

                stdout.write(
                    "\n✅ Django cache cleared successfully"
                )

            except Exception as e:

                stdout.write(
                    "\n⚠️ Failed to clear Django cache: "
                    f"{str(e)}"
                )

            try:

                cache.delete(
                    "active_companies_list"
                )

                from django.core.cache import caches

                for key in list(cache._cache.keys()):

                    if (
                        key.startswith("packages_company_")
                        or
                        key.startswith("specialties_company_")
                    ):
                        cache.delete(key)

                stdout.write(
                    "\n✅ Company packages cache cleared successfully"
                )

            except Exception as e:

                stdout.write(
                    "\n⚠️ Failed to clear company cache: "
                    f"{str(e)}"
                )

            if progress_callback:
                progress_callback(
                    "✅ تم الانتهاء",
                    total_commands
                )

        # ================================================================
        # تحليل النتيجة النهائية
        # ================================================================

        total_elapsed = perf_counter() - total_start

        success_count = sum(
            1
            for result in results
            if result["status"] == "✅"
        )

        failed_count = sum(
            1
            for result in results
            if result["status"] == "❌"
        )

        has_errors = failed_count > 0

        # ================================================================
        # الرسالة النهائية
        # ================================================================

        stdout.write("")
        stdout.write("=" * 70)

        if has_errors:

            stdout.write(
                "⚠️ UPDATE COMPLETED WITH ERRORS"
            )

        else:

            stdout.write(
                "✓ ALL IMPORTS COMPLETED SUCCESSFULLY"
            )

        stdout.write(
            f"Total Time : "
            f"{total_elapsed:.2f} sec"
        )

        stdout.write("=" * 70)

        # ================================================================
        # SUMMARY
        # ================================================================

        stdout.write("")
        stdout.write("📊 SUMMARY:")

        for result in results:

            stdout.write(
                f"   {result['status']} "
                f"{result['title']} "
                f"({result['time']:.2f}s)"
            )

            if result.get("error"):

                stdout.write(
                    f"      Error: "
                    f"{result['error']}"
                )

        stdout.write("=" * 70)
        stdout.write("")

        # ================================================================
        # Return للـCelery Task
        # ================================================================

        return {
            "results": results,
            "total": total_commands,
            "success_count": success_count,
            "failed_count": failed_count,
            "success": not has_errors,
            "total_time": total_elapsed,
        }