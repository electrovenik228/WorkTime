from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("", include("users.api_urls")),
    path("", include("tasks.api_urls")),
    path("", include("tracking.api_urls")),
    path("", include("reports.api_urls")),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]
