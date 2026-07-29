from io import StringIO

from celery import shared_task

from imports.services.update_all_data_service import UpdateAllDataService


@shared_task(bind=True)
def update_all_data_task(self):
    """
    Run the complete data update in the background.
    """

    output = StringIO()

    try:
        UpdateAllDataService.run(
            stdout=output,
        )

        return {
            "status": "success",
            "logs": output.getvalue(),
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "logs": output.getvalue(),
        }