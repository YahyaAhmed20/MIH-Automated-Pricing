from io import StringIO
import threading

from celery import shared_task
from django.core.cache import cache
from django.utils import timezone

from imports.services.progress_service import ProgressService
from imports.services.update_all_data_service import (
    UpdateAllDataService,
    IMPORT_COMMANDS,
    POST_IMPORT_COMMANDS,
    QUICK_UPDATE_COMMANDS,
)
from imports.exceptions import TaskCancelled


HEARTBEAT_INTERVAL = 10


@shared_task(bind=True)
def update_all_data_task(
    self,
    update_type="full",
):
    """
    تنفيذ تحديث بيانات النظام.

    Lifecycle:

        QUEUED
           ↓
        RUNNING
           ↓
        COMPLETED / ERROR / CANCELLED

    الـView مسؤول عن QUEUED.
    الـWorker مسؤول عن RUNNING والـFinal State.
    """

    output = StringIO()

    # ============================================================
    # تحديد الأوامر
    # ============================================================

    if update_type == "quick":
        commands = QUICK_UPDATE_COMMANDS
    else:
        commands = IMPORT_COMMANDS + POST_IMPORT_COMMANDS

    commands = list(commands)
    total = len(commands)

    task_id = self.request.id

    # ============================================================
    # Worker بدأ فعليًا
    # ============================================================

    ProgressService.mark_running(
        task_id=task_id,
        update_type=update_type,
        total=total,
    )

    # ============================================================
    # Heartbeat Thread
    # ============================================================

    heartbeat_stop = threading.Event()

    def heartbeat_loop():
        """
        تحديث heartbeat بشكل مستقل أثناء تنفيذ الـimports.
        """

        while not heartbeat_stop.wait(HEARTBEAT_INTERVAL):

            try:

                progress = ProgressService.get()

                # Task مختلفة → توقف
                if progress.get("task_id") != task_id:
                    break

                # لم تعد Running → توقف
                if progress.get("status") != "running":
                    break

                ProgressService.heartbeat()

            except Exception as exc:

                print(
                    f"⚠️ Heartbeat thread error: {exc}"
                )

    heartbeat_thread = threading.Thread(
        target=heartbeat_loop,
        name=f"update-heartbeat-{task_id}",
        daemon=True,
    )

    heartbeat_thread.start()

    # ============================================================
    # Main Task
    # ============================================================

    try:

        # ========================================================
        # Progress Callback
        # ========================================================

        def progress_callback(
            command_name,
            completed,
        ):

            # ----------------------------------------------------
            # Check Cancel
            # ----------------------------------------------------

            if ProgressService.is_cancel_requested():
                raise TaskCancelled()

            # ----------------------------------------------------
            # Heartbeat
            # ----------------------------------------------------

            ProgressService.heartbeat()

            # ----------------------------------------------------
            # Progress
            # ----------------------------------------------------

            ProgressService.update(
                current_command=command_name,
                completed=completed,
                total=total,
            )

        # ========================================================
        # تشغيل الـImports
        # ========================================================

        run_result = UpdateAllDataService.run(
            stdout=output,
            progress_callback=progress_callback,
            commands=commands,
        )

        # ✅ تم إضافة 3 prints هنا
        print("### TASK DEBUG: UpdateAllDataService.run RETURNED ###")

        logs = output.getvalue()

        print("### TASK DEBUG: LOGS EXTRACTED ###")

        results = run_result["results"]

        print("### TASK DEBUG: RESULTS EXTRACTED ###")

        has_errors = not run_result["success"]

        # ========================================================
        # Cache
        # ========================================================

        try:

            cache.clear()

            logs += (
                "\n\n"
                "✅ تم مسح الـ Cache بنجاح"
            )

        except Exception as e:

            logs += (
                "\n\n"
                f"⚠️ فشل مسح الـ Cache: {str(e)}"
            )

        # ========================================================
        # إيقاف Heartbeat قبل Final State
        # ========================================================

        heartbeat_stop.set()

        # ========================================================
        # Final State
        # ========================================================

        final_status = (
            "error"
            if has_errors
            else "completed"
        )

        final_command = (
            "⚠️ اكتمل التحديث مع وجود أخطاء"
            if has_errors
            else "✅ تم الانتهاء من التحديث بنجاح!"
        )

        final_error = (
            "اكتمل التحديث مع وجود أخطاء."
            if has_errors
            else None
        )

        # --------------------------------------------------------
        # حفظ الحالة النهائية مرة واحدة
        # --------------------------------------------------------

        ProgressService.update(
            status=final_status,
            is_running=False,
            completed=total,
            total=total,
            logs=logs,
            results=results,
            current_command=final_command,
            update_type=update_type,
            finished_at=timezone.now().isoformat(),
            error=final_error,
            heartbeat_at=timezone.now().isoformat(),
        )

        # ========================================================
        # آخر تحديث ناجح
        # ========================================================

        if not has_errors:

            ProgressService.set_last_successful_update(
                update_type=update_type
            )

        # ========================================================
        # Return
        # ========================================================

        return {
            "status": (
                "error"
                if has_errors
                else "success"
            ),
            "update_type": update_type,
            "logs": logs,
            "results": results,
        }

    # ============================================================
    # CANCELLED
    # ============================================================

    except TaskCancelled:

        heartbeat_stop.set()

        logs = output.getvalue()

        logs += (
            "\n\n"
            "🛑 تم إلغاء العملية بواسطة المستخدم."
        )

        # --------------------------------------------------------
        # حالة الإلغاء النهائية
        # --------------------------------------------------------

        ProgressService.update(
            status="cancelled",
            is_running=False,
            logs=logs,
            current_command="🛑 تم الإلغاء",
            update_type=update_type,
            finished_at=timezone.now().isoformat(),
            error=None,
        )

        return {
            "status": "cancelled",
            "update_type": update_type,
        }

    # ============================================================
    # UNEXPECTED ERROR
    # ============================================================

    except Exception as exc:

        heartbeat_stop.set()

        logs = output.getvalue()

        logs += (
            "\n\n"
            f"❌ خطأ: {exc}"
        )

        # --------------------------------------------------------
        # حفظ Error State
        # --------------------------------------------------------

        try:

            ProgressService.update(
                status="error",
                is_running=False,
                logs=logs,
                current_command=(
                    f"❌ خطأ: {str(exc)[:100]}"
                ),
                update_type=update_type,
                finished_at=timezone.now().isoformat(),
                error=str(exc),
            )

        except Exception as progress_exc:

            print(
                "❌ Failed to save error state: "
                f"{progress_exc}"
            )

        # مهم:
        # نخلي Celery تعتبر الـTask FAILURE
        raise

    finally:

        # ========================================================
        # ضمان إيقاف Heartbeat
        # ========================================================

        heartbeat_stop.set()