from datetime import timedelta

from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.utils import timezone

from tasks.models import Task

from .models import TimeEntry


class ActiveTimerExistsError(Exception):
    pass


class ActiveTimerMissingError(Exception):
    pass


def _active_timer_cache_key(user_id):
    return f"active-timer:{user_id}"


def get_active_timer(user):
    cached_entry_id = cache.get(_active_timer_cache_key(user.id))
    if cached_entry_id:
        entry = TimeEntry.objects.filter(pk=cached_entry_id, user=user, end_time__isnull=True).select_related("task").first()
        if entry:
            return entry
    entry = TimeEntry.objects.filter(user=user, end_time__isnull=True).select_related("task").first()
    if entry:
        cache.set(_active_timer_cache_key(user.id), entry.id, 300)
    return entry


def start_timer(*, user, task):
    with transaction.atomic():
        locked_user = user.__class__.objects.select_for_update().get(pk=user.pk)
        active_entry = (
            TimeEntry.objects.select_for_update()
            .filter(user=locked_user, end_time__isnull=True)
            .select_related("task")
            .first()
        )
        if active_entry:
            if active_entry.task_id == task.id:
                return active_entry
            raise ActiveTimerExistsError("Stop the current timer before starting another one.")
        try:
            entry = TimeEntry.objects.create(user=locked_user, task=task, start_time=timezone.now())
        except IntegrityError as exc:
            raise ActiveTimerExistsError("Another timer was started at the same time. Retry after stopping it.") from exc
        if task.status == Task.Status.TODO:
            task.status = Task.Status.IN_PROGRESS
            task.save(update_fields=["status"])
    cache.set(_active_timer_cache_key(user.id), entry.id, 300)
    return entry


def stop_timer(*, user, task):
    with transaction.atomic():
        user.__class__.objects.select_for_update().get(pk=user.pk)
        entry = (
            TimeEntry.objects.select_for_update()
            .filter(user=user, task=task, end_time__isnull=True)
            .order_by("-start_time")
            .first()
        )
        if not entry:
            raise ActiveTimerMissingError("No active timer found for this task.")
        entry.end_time = timezone.now()
        entry.save(update_fields=["end_time"])
    cache.delete(_active_timer_cache_key(user.id))
    return entry


def format_duration(delta):
    total_seconds = int(max(delta, timedelta()).total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def can_track_task(user, task):
    return user.role == user.__class__.Roles.MANAGER or task.created_by_id == user.id or task.assigned_to_id == user.id
