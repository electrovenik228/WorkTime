from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from tasks.models import Task

from .models import TimeEntry
from .serializers import TimeEntrySerializer
from .services import (
    ActiveTimerExistsError,
    ActiveTimerMissingError,
    can_track_task,
    format_duration,
    start_timer,
    stop_timer,
)


class StartTimerApiView(APIView):
    def post(self, request, task_id):
        task = get_object_or_404(Task, pk=task_id)
        if not can_track_task(request.user, task):
            return Response({"detail": "You cannot track this task."}, status=status.HTTP_403_FORBIDDEN)
        try:
            entry = start_timer(user=request.user, task=task)
        except ActiveTimerExistsError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TimeEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


class StopTimerApiView(APIView):
    def post(self, request, task_id):
        task = get_object_or_404(Task, pk=task_id)
        if not can_track_task(request.user, task):
            return Response({"detail": "You cannot track this task."}, status=status.HTTP_403_FORBIDDEN)
        try:
            entry = stop_timer(user=request.user, task=task)
        except ActiveTimerMissingError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TimeEntrySerializer(entry).data)


class MyTimeEntriesApiView(generics.ListAPIView):
    serializer_class = TimeEntrySerializer

    def get_queryset(self):
        return TimeEntry.objects.filter(user=self.request.user).select_related("task")


class TimerActionMixin(LoginRequiredMixin):
    def handle(self, request, task_id, action):
        task = get_object_or_404(Task, pk=task_id)
        if not can_track_task(request.user, task):
            return JsonResponse({"detail": "You cannot track this task."}, status=403)

        try:
            entry = action(user=request.user, task=task)
        except (ActiveTimerExistsError, ActiveTimerMissingError) as exc:
            return JsonResponse({"detail": str(exc)}, status=400)

        return JsonResponse(
            {
                "id": entry.id,
                "task": task.id,
                "task_title": task.title,
                "is_active": entry.is_active,
                "start_time": entry.start_time.isoformat(),
                "end_time": entry.end_time.isoformat() if entry.end_time else None,
                "duration": format_duration(entry.duration),
            }
        )


class StartTimerWebView(TimerActionMixin, View):
    def post(self, request, task_id):
        return self.handle(request, task_id, start_timer)


class StopTimerWebView(TimerActionMixin, View):
    def post(self, request, task_id):
        return self.handle(request, task_id, stop_timer)
