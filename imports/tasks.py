from io import StringIO

from celery import shared_task

from imports.services.progress_service import ProgressService
from imports.services.update_all_data_service import UpdateAllDataService


@shared_task(bind=True)
def update_all_data_task(self):

    output = StringIO()

    ProgressService.reset()

    ProgressService.update(
        is_running=True,
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

        ProgressService.update(
            is_running=False,
            completed=ProgressService.get()["total"],
        )

        return {
            "status": "success",
            "logs": output.getvalue(),
        }

    except Exception as e:

        ProgressService.update(
            is_running=False,
        )

        raise e