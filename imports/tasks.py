import time

from celery import shared_task


@shared_task
def test_task():
    print("Task Started")

    time.sleep(10)

    print("Task Finished")

    return "OK"