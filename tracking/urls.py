from django.urls import path

from .views import StartTimerWebView, StopTimerWebView


urlpatterns = [
    path("time/start/<int:task_id>/", StartTimerWebView.as_view(), name="time-start"),
    path("time/stop/<int:task_id>/", StopTimerWebView.as_view(), name="time-stop"),
]

