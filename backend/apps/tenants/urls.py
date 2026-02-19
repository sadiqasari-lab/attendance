"""URL configuration for the tenants app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import EmployeeViewSet
from apps.tenants.views import DepartmentViewSet, GroupViewSet, TenantViewSet

router = DefaultRouter()
router.register(r"groups", GroupViewSet, basename="group")
router.register(r"departments", DepartmentViewSet, basename="department")
router.register(r"employees", EmployeeViewSet, basename="employee")

app_name = "tenants"

# TenantViewSet is mounted at the root (/api/v1/tenants/) via explicit paths
# so the URL doesn't double up as /api/v1/tenants/tenants/.
tenant_list = TenantViewSet.as_view({"get": "list", "post": "create"})
tenant_detail = TenantViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
tenant_stats = TenantViewSet.as_view({"get": "stats"})

urlpatterns = [
    path("", tenant_list, name="tenant-list"),
    path("<uuid:pk>/", tenant_detail, name="tenant-detail"),
    path("<uuid:pk>/stats/", tenant_stats, name="tenant-stats"),
    path("", include(router.urls)),
]
