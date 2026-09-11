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

    started = ProgressService.mark_running(
        task_id=task_id,
        update_type=update_type,
        total=total,
    )

    if started is None:
        return {
            "status": "ignored",
            "update_type": update_type,
            "reason": "stale_task",
        }

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

                if not ProgressService.heartbeat(task_id):
                    break

            except Exception as exc:

                print(
                    f"⚠️ Heartbeat thread error: {exc}"
                )
                break



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

            if ProgressService.is_cancel_requested(task_id):
                raise TaskCancelled()

            # ----------------------------------------------------
            # Heartbeat
            # ----------------------------------------------------

            if not ProgressService.heartbeat(task_id):
                raise RuntimeError(
                    f"Task {task_id} lost update ownership"
                )

            # ----------------------------------------------------
            # Progress
            # ----------------------------------------------------

            updated = ProgressService.update(
                task_id=task_id,
                current_command=command_name,
                completed=completed,
                total=total,
            )

            if updated is None:
                raise RuntimeError(
                    f"Task {task_id} failed to update progress"
                )

        # ========================================================
        # تشغيل الـImports
        # ========================================================

        run_result = UpdateAllDataService.run(
            stdout=output,
            progress_callback=progress_callback,
            commands=commands,
            task_id=task_id,
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
        # إيقاف Heartbeat قبل Final State
        # ========================================================

        heartbeat_stop.set()

        # ========================================================
        # Final State
        # ========================================================

        if has_errors:

            final_state = ProgressService.mark_error(
                task_id=task_id,
                message="اكتمل التحديث مع وجود أخطاء.",
                logs=logs,
                results=results,
            )

            if final_state is None:
                raise RuntimeError(
                    f"Task {task_id} failed to save error state"
                )

        else:

            final_state = ProgressService.mark_completed(
                task_id=task_id,
                results=results,
                logs=logs,
            )

            if final_state is None:
                raise RuntimeError(
                    f"Task {task_id} failed to save completed state"
                )

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

        cancelled_state = ProgressService.mark_cancelled(
            task_id=task_id,
            logs=logs,
        )

        if cancelled_state is None:
            raise RuntimeError(
                f"Task {task_id} failed to save cancelled state"
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

        try:

            error_state = ProgressService.mark_error(
                task_id=task_id,
                message=str(exc),
                logs=logs,
            )

            if error_state is None:
                print(
                    "❌ Failed to save error state: "
                    f"Task {task_id}"
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

        # ========================================================
        # Safety Lock Release
        # ========================================================

        try:
            ProgressService.release_lock(task_id)
        except Exception as exc:
            print(
                f"⚠️ Failed to release update lock "
                f"for task {task_id}: {exc}"
            )