"""URL configuration for Inspire Attendance System."""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.core.backup_views import (
    BackupCreateView,
    BackupDeleteView,
    BackupDownloadView,
    BackupListView,
    BackupRestoreView,
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
    # Backup & Restore
    path("api/v1/backups/", BackupListView.as_view(), name="backup-list"),
    path("api/v1/backups/create/", BackupCreateView.as_view(), name="backup-create"),
    path("api/v1/backups/restore/", BackupRestoreView.as_view(), name="backup-restore"),
    path("api/v1/backups/<str:filename>/download/", BackupDownloadView.as_view(), name="backup-download"),
    path("api/v1/backups/<str:filename>/", BackupDeleteView.as_view(), name="backup-delete"),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
