from io import StringIO
import threading
import time

from celery import shared_task
from django.core.cache import cache

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

    ملاحظة:
    الـView هو المسؤول عن تسجيل QUEUED.
    الـCelery Worker هو المسؤول عن تحويلها إلى RUNNING.
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

        مهم:
        الـcommand الواحد ممكن يستغرق أكثر من 60 ثانية،
        لذلك لا نعتمد على progress_callback وحده.
        """

        while not heartbeat_stop.wait(HEARTBEAT_INTERVAL):

            try:

                # لو العملية انتهت، لا داعي لأي heartbeat إضافي
                progress = ProgressService.get()

                if progress.get("task_id") != task_id:
                    break

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
            """
            يتم استدعاؤها من UpdateAllDataService
            قبل كل Command.
            """

            # ----------------------------------------------------
            # Check Cancel
            # ----------------------------------------------------

            if ProgressService.is_cancel_requested():
                raise TaskCancelled()

            # ----------------------------------------------------
            # Heartbeat فوري
            # ----------------------------------------------------

            ProgressService.heartbeat()

            # ----------------------------------------------------
            # تحديث Progress
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

        logs = output.getvalue()

        results = run_result["results"]
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
        # إيقاف Heartbeat
        # ========================================================

        heartbeat_stop.set()

        # ========================================================
        # Final State
        # ========================================================

        if has_errors:

            ProgressService.mark_error(
                message="اكتمل التحديث مع وجود أخطاء.",
                logs=logs,
                results=results,
            )

            ProgressService.update(
                completed=total,
                total=total,
                current_command=(
                    "⚠️ اكتمل التحديث مع وجود أخطاء"
                ),
                update_type=update_type,
            )

        else:

            ProgressService.update(
                completed=total,
                total=total,
                update_type=update_type,
            )

            ProgressService.mark_completed(
                logs=logs,
                results=results,
            )

            # ----------------------------------------------------
            # حفظ آخر تحديث ناجح
            # ----------------------------------------------------

            ProgressService.set_last_successful_update(
                update_type=update_type
            )

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

        ProgressService.mark_cancelled(
            logs=logs,
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

        ProgressService.mark_error(
            message=str(exc),
            logs=logs,
        )

        raise

    finally:

        # ضمان إيقاف الـheartbeat مهما حصل
        heartbeat_stop.set()