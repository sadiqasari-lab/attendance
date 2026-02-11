"""URL patterns for the integration (HRIS) app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("tokens", views.IntegrationTokenViewSet, basename="integration-token")
router.register("webhooks", views.WebhookConfigViewSet, basename="webhook-config")
router.register("webhook-logs", views.WebhookLogViewSet, basename="webhook-log")

urlpatterns = [
    # Admin management endpoints
    path("", include(router.urls)),
    # External HRIS pull endpoints (token-authenticated)
    path("pull/attendance-logs/", views.AttendanceLogsPullView.as_view(), name="pull-attendance-logs"),
    path("pull/shifts/", views.ShiftsPullView.as_view(), name="pull-shifts"),
    path("pull/summary/", views.AttendanceSummaryPullView.as_view(), name="pull-summary"),
]
