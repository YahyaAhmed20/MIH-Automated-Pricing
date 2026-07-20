import threading

from imports.services.update_all_data_service import (
    UpdateAllDataService,
)


class SystemUpdateRunner:

    _thread = None

    @classmethod
    def is_running(cls):
        return (
            cls._thread is not None
            and cls._thread.is_alive()
        )

    @classmethod
    def start(cls, stdout):

        if cls.is_running():
            return False

        cls._thread = threading.Thread(
            target=UpdateAllDataService.run,
            kwargs={
                "stdout": stdout,
            },
            daemon=True,
        )

        cls._thread.start()

        return True