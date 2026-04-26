from rest_framework import serializers

from .models import TimeEntry
from .services import format_duration


class TimeEntrySerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()
    task_title = serializers.CharField(source="task.title", read_only=True)

    class Meta:
        model = TimeEntry
        fields = ("id", "task", "task_title", "start_time", "end_time", "duration")

    def get_duration(self, obj):
        return format_duration(obj.duration)

