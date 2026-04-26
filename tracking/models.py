from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from tasks.models import Task


class TimeEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="time_entries")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="time_entries")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(end_time__isnull=True),
                name="unique_active_timer_per_user",
            )
        ]
        indexes = [
            models.Index(fields=["user", "start_time"]),
            models.Index(fields=["task", "start_time"]),
        ]

    @property
    def is_active(self):
        return self.end_time is None

    @property
    def duration(self):
        end_time = self.end_time or timezone.now()
        return max(end_time - self.start_time, timedelta())

    def __str__(self):
        return f"{self.user} - {self.task}"
