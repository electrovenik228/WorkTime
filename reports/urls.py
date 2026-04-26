from django.urls import path

from .views import ReportsPageView


urlpatterns = [
    path("reports/", ReportsPageView.as_view(), name="reports"),
]

