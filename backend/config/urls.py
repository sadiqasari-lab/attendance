"""URL configuration for Inspire Attendance System."""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API v1
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/tenants/", include("apps.tenants.urls")),
    path("api/v1/<slug:tenant_slug>/attendance/", include("apps.attendance.urls")),
    path("api/v1/<slug:tenant_slug>/projects/", include("apps.projects.urls")),
    path("api/v1/<slug:tenant_slug>/approvals/", include("apps.approvals.urls")),
    path("api/v1/<slug:tenant_slug>/devices/", include("apps.devices.urls")),
    path("api/v1/<slug:tenant_slug>/biometric/", include("apps.biometric.urls")),
    path("api/v1/integration/", include("apps.integration.urls")),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
