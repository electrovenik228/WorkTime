from django.urls import path

from .views import TaskDetailApiView, TaskListCreateApiView


urlpatterns = [
    path("tasks/", TaskListCreateApiView.as_view(), name="api-task-list"),
    path("tasks/<int:pk>/", TaskDetailApiView.as_view(), name="api-task-detail"),
]

