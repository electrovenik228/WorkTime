from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView
from rest_framework import generics, permissions

from users.models import User

from .forms import TaskForm, TaskUpdateForm
from .models import Task
from .permissions import IsManagerOrRelatedTaskUser
from .serializers import TaskSerializer


class TaskQuerysetMixin:
    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.select_related("created_by", "assigned_to")
        if user.role != User.Roles.MANAGER:
            queryset = queryset.filter(Q(created_by=user) | Q(assigned_to=user))

        search = self.request.GET.get("search")
        status_value = self.request.GET.get("status")
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        if status_value:
            queryset = queryset.filter(status=status_value)
        return queryset


class TaskListCreateApiView(TaskQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]


class TaskDetailApiView(TaskQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsManagerOrRelatedTaskUser]


class TaskListView(LoginRequiredMixin, TaskQuerysetMixin, ListView):
    template_name = "tasks/list.html"
    model = Task
    paginate_by = 6
    context_object_name = "tasks"

    def get_queryset(self):
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = TaskForm(user=self.request.user)
        context["statuses"] = Task.Status.choices
        return context

    def post(self, request, *args, **kwargs):
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            if request.user.role != User.Roles.MANAGER and task.assigned_to != request.user:
                messages.error(request, "Employees can assign tasks only to themselves.")
            else:
                task.save()
                messages.success(request, "Task created.")
                return redirect("task-detail", pk=task.pk)
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        context["form"] = form
        return self.render_to_response(context)


class TaskDetailView(LoginRequiredMixin, DetailView):
    template_name = "tasks/detail.html"
    context_object_name = "task"
    model = Task

    def get_queryset(self):
        queryset = Task.objects.select_related("created_by", "assigned_to").prefetch_related("time_entries__user")
        user = self.request.user
        if user.role != User.Roles.MANAGER:
            queryset = queryset.filter(Q(created_by=user) | Q(assigned_to=user))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entries"] = self.object.time_entries.select_related("user")
        context["statuses"] = Task.Status.choices
        context["form"] = TaskUpdateForm(instance=self.object, user=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = TaskUpdateForm(request.POST, instance=self.object, user=request.user)
        if form.is_valid():
            updated_task = form.save(commit=False)
            if request.user.role != User.Roles.MANAGER and updated_task.assigned_to != request.user:
                messages.error(request, "Employees cannot reassign tasks to other users.")
            else:
                updated_task.save()
                messages.success(request, "Task updated.")
                return redirect("task-detail", pk=self.object.pk)
        context = self.get_context_data()
        context["form"] = form
        return self.render_to_response(context)
