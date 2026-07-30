from io import StringIO

from celery import shared_task

from imports.services.progress_service import ProgressService
from imports.services.update_all_data_service import (
    UpdateAllDataService,
    IMPORT_COMMANDS,
    POST_IMPORT_COMMANDS,
)


@shared_task(bind=True)
def update_all_data_task(self):

    output = StringIO()

    # ✅ حساب العدد الإجمالي للأوامر
    total = len(IMPORT_COMMANDS) + len(POST_IMPORT_COMMANDS)

    # ✅ بداية التحديث - مسح الـ logs القديمة
    ProgressService.reset()
    
    ProgressService.update(
        is_running=True,
        total=total,
        logs=None,  # ✅ مسح الـ logs القديمة
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

        # ✅ نهاية التحديث - حفظ الـ logs الجديدة
        ProgressService.update(
            is_running=False,
            completed=total,
            total=total,
            logs=logs,  # ✅ الـ logs الجديدة
        )

        return {
            "status": "success",
            "logs": logs,
        }

    except Exception as e:

        ProgressService.update(
            is_running=False,
        )

        raise e