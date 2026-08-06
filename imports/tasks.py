from io import StringIO
from celery import shared_task
from django.core.cache import cache

from imports.services.progress_service import ProgressService
from imports.services.update_all_data_service import (
    UpdateAllDataService,
    IMPORT_COMMANDS,
    POST_IMPORT_COMMANDS,
)
from imports.exceptions import TaskCancelled


@shared_task(bind=True)
def update_all_data_task(self):

    output = StringIO()

    total = len(IMPORT_COMMANDS) + len(POST_IMPORT_COMMANDS)

    ProgressService.reset()
    ProgressService.clear_cancel()

    ProgressService.update(
        status="running",
        is_running=True,
        total=total,
        logs=None,
    )

    try:

        def progress_callback(command_name, completed):
            if ProgressService.is_cancel_requested():
                raise TaskCancelled()

            ProgressService.update(
                current_command=command_name,
                completed=completed,
            )

        UpdateAllDataService.run(
            stdout=output,
            progress_callback=progress_callback,
        )

        logs = output.getvalue()

        # ✅ مسح الـ Cache بالكامل
        try:
            cache.clear()
            logs += "\n\n✅ تم مسح الـ Cache بنجاح"
        except Exception as e:
            logs += f"\n\n⚠️ فشل مسح الـ Cache: {str(e)}"

        ProgressService.update(
            status="completed",
            is_running=False,
            completed=total,
            total=total,
            logs=logs,
        )

        return {
            "status": "success",
            "logs": logs,
        }

    except TaskCancelled:

        logs = output.getvalue()

        ProgressService.update(
            status="cancelled",
            is_running=False,
            completed=ProgressService.get().get("completed", 0),
            logs=logs + "\n\n🛑 تم إلغاء العملية بواسطة المستخدم.",
        )

        return {
            "status": "cancelled",
        }

    except Exception as exc:

        error_logs = output.getvalue()

        ProgressService.update(
            status="error",
            is_running=False,
            logs=error_logs + f"\n\n❌ خطأ: {exc}",
        )

        raise