from django.urls import path

from .views import DailyReportApiView, DailyReportCsvApiView, WeeklyReportApiView, WeeklyReportCsvApiView


urlpatterns = [
    path("reports/daily/", DailyReportApiView.as_view(), name="api-report-daily"),
    path("reports/weekly/", WeeklyReportApiView.as_view(), name="api-report-weekly"),
    path("reports/daily/export/", DailyReportCsvApiView.as_view(), name="api-report-daily-export"),
    path("reports/weekly/export/", WeeklyReportCsvApiView.as_view(), name="api-report-weekly-export"),
]
