from django.db import models

# Create your models here.
from django.db import models


class SystemUpdateJob(models.Model):

    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RUNNING,
    )

    started_at = models.DateTimeField(auto_now_add=True)

    finished_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    current_step = models.CharField(
        max_length=200,
        blank=True,
    )

    logs = models.TextField(
        blank=True,
    )

    duration = models.FloatField(
        default=0,
    )

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.started_at} - {self.status}"