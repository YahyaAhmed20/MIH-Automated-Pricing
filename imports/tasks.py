from io import StringIO
from celery import shared_task
from django.core.cache import cache

from imports.services.progress_service import ProgressService
from imports.services.update_all_data_service import (
    UpdateAllDataService,
    IMPORT_COMMANDS,
    POST_IMPORT_COMMANDS,
)


@shared_task(bind=True)
def update_all_data_task(self):

    output = StringIO()

    total = len(IMPORT_COMMANDS) + len(POST_IMPORT_COMMANDS)

    ProgressService.reset()
    
    ProgressService.update(
        is_running=True,
        total=total,
        logs=None,
    )

    try:

        def progress_callback(command_name, completed):
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
            is_running=False,
            completed=total,
            total=total,
            logs=logs,
        )

        return {
            "status": "success",
            "logs": logs,
        }

    except Exception as e:

        # ✅ في حالة الخطأ، سجل الـ logs الموجودة
        error_logs = output.getvalue()
        ProgressService.update(
            is_running=False,
            logs=error_logs + f"\n\n❌ خطأ: {str(e)}",
        )

        raise e