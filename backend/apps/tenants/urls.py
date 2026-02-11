"""URL configuration for the tenants app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.tenants.views import DepartmentViewSet, GroupViewSet, TenantViewSet

router = DefaultRouter()
router.register(r"groups", GroupViewSet, basename="group")
router.register(r"tenants", TenantViewSet, basename="tenant")
router.register(r"departments", DepartmentViewSet, basename="department")

app_name = "tenants"

urlpatterns = [
    path("", include(router.urls)),
]
