"""URL configuration for the accounts app."""
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # Authentication
    path("login/", views.LoginView.as_view(), name="login"),
    path("token/refresh/", views.CustomTokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    # Profile
    path("profile/", views.UserProfileView.as_view(), name="profile"),
    # Password
    path("password/change/", views.ChangePasswordView.as_view(), name="password-change"),
]
