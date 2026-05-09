from datetime import timedelta

from django.utils import timezone

from tracking.models import TimeEntry
from users.models import User

from tracking.services import format_duration


def resolve_target_user(request_user, user_id=None):
    if request_user.role != User.Roles.MANAGER:
        return request_user
    if not user_id:
        return None
    return request_user.__class__.objects.filter(pk=user_id).first()


def _entries_for_user(user, target_user=None):
    queryset = TimeEntry.objects.select_related("task", "user")
    if user.role == User.Roles.MANAGER and target_user and target_user != user:
        return queryset.filter(user=target_user)
    if user.role == User.Roles.MANAGER:
        return queryset
    return queryset.filter(user=user)


def parse_report_date(raw_value, fallback=None):
    if not raw_value:
        return fallback or timezone.localdate()
    try:
        return timezone.datetime.strptime(raw_value, "%Y-%m-%d").date()
    except ValueError:
        return fallback or timezone.localdate()


def build_daily_report(user, target_date=None, target_user=None):
    target_date = target_date or timezone.localdate()
    entries = _entries_for_user(user, target_user=target_user).filter(start_time__date=target_date)
    grouped = {}
    for entry in entries:
        key = (entry.task_id, entry.task.title, entry.user.username)
        grouped.setdefault(key, timedelta())
        grouped[key] += entry.duration
    rows = [
        {
            "task_id": task_id,
            "task_title": task_title,
            "user_name": user_name,
            "seconds": int(duration.total_seconds()),
            "duration": format_duration(duration),
        }
        for (task_id, task_title, user_name), duration in grouped.items()
    ]
    rows.sort(key=lambda row: row["seconds"], reverse=True)
    return {"date": str(target_date), "rows": rows}


def build_weekly_report(user, anchor_date=None, target_user=None):
    anchor_date = anchor_date or timezone.localdate()
    week_start = anchor_date - timedelta(days=anchor_date.weekday())
    week_end = week_start + timedelta(days=6)
    entries = _entries_for_user(user, target_user=target_user).filter(
        start_time__date__gte=week_start,
        start_time__date__lte=week_end,
    )

    per_day = {}
    total = timedelta()
    for offset in range(7):
        date_value = week_start + timedelta(days=offset)
        per_day[str(date_value)] = timedelta()

    for entry in entries:
        day_key = str(timezone.localtime(entry.start_time).date())
        per_day[day_key] += entry.duration
        total += entry.duration

    total_seconds = int(total.total_seconds()) or 1
    return {
        "week_start": str(week_start),
        "week_end": str(week_end),
        "total_seconds": int(total.total_seconds()),
        "total_duration": format_duration(total),
        "days": [
            {
                "date": day,
                "seconds": int(duration.total_seconds()),
                "duration": format_duration(duration),
                "percent": round((duration.total_seconds() / total_seconds) * 100) if duration.total_seconds() else 0,
            }
            for day, duration in per_day.items()
        ],
    }
