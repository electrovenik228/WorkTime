from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from tasks.models import Task
from tracking.models import TimeEntry

from .forms import LoginForm, RegisterForm
from .models import User
from .serializers import (
    LoginSerializer,
    LogoutSerializer,
    RegisterSerializer,
    TokenResponseSerializer,
)


class RegisterApiView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(TokenResponseSerializer.build_for_user(user), status=status.HTTP_201_CREATED)


class LoginApiView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(TokenResponseSerializer.build_for_user(serializer.validated_data["user"]))


class LogoutApiView(APIView):
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except TokenError as exc:
            raise ValidationError({"refresh": [str(exc)]}) from exc
        return Response(status=status.HTTP_205_RESET_CONTENT)


class LoginPageView(LoginView):
    template_name = "users/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class RegisterPageView(FormView):
    template_name = "users/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Account created successfully.")
        return super().form_valid(form)


class LogoutPageView(LoginRequiredMixin, View):
    http_method_names = ["get", "post"]

    def get(self, request, *args, **kwargs):
        return self._logout_and_redirect(request)

    def post(self, request, *args, **kwargs):
        return self._logout_and_redirect(request)

    def _logout_and_redirect(self, request):
        logout(request)
        messages.success(request, "You have been logged out.")
        return HttpResponseRedirect(reverse_lazy("login"))


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse_lazy("login"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        task_filter = Q()
        if user.role != User.Roles.MANAGER:
            task_filter = Q(created_by=user) | Q(assigned_to=user)
        tasks = Task.objects.filter(task_filter).select_related("assigned_to", "created_by")
        context["stats"] = {
            "tasks_total": tasks.count(),
            "tasks_in_progress": tasks.filter(status=Task.Status.IN_PROGRESS).count(),
            "tasks_done": tasks.filter(status=Task.Status.DONE).count(),
            "hours_logged": round(
                sum(entry.duration.total_seconds() for entry in TimeEntry.objects.filter(user=user)) / 3600,
                1,
            ),
        }
        context["recent_tasks"] = tasks[:5]
        context["active_entry"] = TimeEntry.objects.filter(user=user, end_time__isnull=True).select_related("task").first()
        context["team_overview"] = (
            User.objects.annotate(task_count=Count("assigned_tasks"))
            if user.role == User.Roles.MANAGER
            else []
        )
        return context
