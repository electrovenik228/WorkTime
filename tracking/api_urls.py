from django.urls import path

from .views import MyTimeEntriesApiView, StartTimerApiView, StopTimerApiView


urlpatterns = [
    path("time/start/<int:task_id>/", StartTimerApiView.as_view(), name="api-time-start"),
    path("time/stop/<int:task_id>/", StopTimerApiView.as_view(), name="api-time-stop"),
    path("time/my/", MyTimeEntriesApiView.as_view(), name="api-time-my"),
]

