from django.urls import path

from .views import DashboardView, LoginPageView, LogoutPageView, RegisterPageView


urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("login/", LoginPageView.as_view(), name="login"),
    path("register/", RegisterPageView.as_view(), name="register"),
    path("logout/", LogoutPageView.as_view(), name="logout"),
]
