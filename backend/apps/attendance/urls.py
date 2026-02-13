"""URL patterns for the attendance app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .report_views import AttendanceReportView, ExportExcelView, ExportPdfView

router = DefaultRouter()
router.register("shifts", views.ShiftViewSet, basename="shift")
router.register("policies", views.AttendancePolicyViewSet, basename="attendance-policy")
router.register("geofences", views.GeofenceViewSet, basename="geofence")
router.register("wifi-policies", views.WifiPolicyViewSet, basename="wifi-policy")
router.register("records", views.AttendanceRecordViewSet, basename="attendance-record")
router.register("corrections", views.AttendanceCorrectionRequestViewSet, basename="correction")

urlpatterns = [
    path("clock-in/", views.ClockInView.as_view(), name="clock-in"),
    path("clock-out/", views.ClockOutView.as_view(), name="clock-out"),
    path("offline-sync/", views.OfflineSyncView.as_view(), name="offline-sync"),
    path("summary/", views.AttendanceSummaryView.as_view(), name="attendance-summary"),
    # Reports & Export
    path("reports/", AttendanceReportView.as_view(), name="attendance-report"),
    path("reports/export/excel/", ExportExcelView.as_view(), name="report-export-excel"),
    path("reports/export/pdf/", ExportPdfView.as_view(), name="report-export-pdf"),
    path("", include(router.urls)),
]
