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

        # ✅ مسح الـ Cache الخاص بالشركات والباكدجات فقط
        cache.delete_pattern('packages_company_*')
        cache.delete_pattern('specialties_company_*')
        cache.delete('active_companies_list')
        cache.delete_pattern('*pricing*')

        ProgressService.update(
            is_running=False,
            completed=total,
            total=total,
            logs=logs + "\n\n✅ تم تحديث الـ Cache بنجاح",
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