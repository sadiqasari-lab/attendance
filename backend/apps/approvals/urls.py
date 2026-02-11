"""URL configuration for the approvals app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ApprovalRequestViewSet

app_name = "approvals"

router = DefaultRouter()
router.register(r"approval-requests", ApprovalRequestViewSet, basename="approval-request")

urlpatterns = [
    path("", include(router.urls)),
]
