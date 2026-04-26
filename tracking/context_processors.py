from .models import TimeEntry


def active_timer(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"global_active_entry": None}
    entry = TimeEntry.objects.filter(user=request.user, end_time__isnull=True).select_related("task").first()
    return {"global_active_entry": entry}
