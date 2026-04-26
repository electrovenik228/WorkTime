from django.contrib import admin

from .models import TimeEntry


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "task", "start_time", "end_time")
    list_filter = ("start_time", "end_time")
    search_fields = ("user__username", "task__title")
