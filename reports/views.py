import csv

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import TemplateView
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User

from .services import build_daily_report, build_weekly_report, parse_report_date, _resolve_target_user


class ReportFilterMixin:
    def get_filter_payload(self):
        date_value = parse_report_date(self.request.GET.get("date"))
        target_user = _resolve_target_user(self.request.user, self.request.GET.get("user_id"))
        return {"date_value": date_value, "target_user": target_user}


class DailyReportApiView(ReportFilterMixin, APIView):
    def get(self, request):
        filters = self.get_filter_payload()
        return Response(build_daily_report(request.user, filters["date_value"], filters["target_user"]))


class WeeklyReportApiView(ReportFilterMixin, APIView):
    def get(self, request):
        filters = self.get_filter_payload()
        return Response(build_weekly_report(request.user, filters["date_value"], filters["target_user"]))


class DailyReportCsvApiView(ReportFilterMixin, APIView):
    def get(self, request):
        filters = self.get_filter_payload()
        report = build_daily_report(request.user, filters["date_value"], filters["target_user"])
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="daily-report-{report["date"]}.csv"'
        writer = csv.writer(response)
        writer.writerow(["date", "task", "user", "duration"])
        for row in report["rows"]:
            writer.writerow([report["date"], row["task_title"], row["user_name"], row["duration"]])
        return response


class WeeklyReportCsvApiView(ReportFilterMixin, APIView):
    def get(self, request):
        filters = self.get_filter_payload()
        report = build_weekly_report(request.user, filters["date_value"], filters["target_user"])
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="weekly-report-{report["week_start"]}.csv"'
        writer = csv.writer(response)
        writer.writerow(["week_start", "week_end", "date", "duration"])
        for day in report["days"]:
            writer.writerow([report["week_start"], report["week_end"], day["date"], day["duration"]])
        writer.writerow(["total", "", "", report["total_duration"]])
        return response


class ReportsPageView(LoginRequiredMixin, ReportFilterMixin, TemplateView):
    template_name = "reports/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filters = self.get_filter_payload()
        context["daily_report"] = build_daily_report(self.request.user, filters["date_value"], filters["target_user"])
        context["weekly_report"] = build_weekly_report(self.request.user, filters["date_value"], filters["target_user"])
        context["report_date"] = filters["date_value"]
        context["selected_user"] = filters["target_user"]
        context["team_members"] = User.objects.all() if self.request.user.role == User.Roles.MANAGER else []
        return context
