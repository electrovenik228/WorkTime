from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "created_by", "assigned_to", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "description", "created_by__username", "assigned_to__username")
