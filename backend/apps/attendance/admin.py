from django.contrib import admin

from .models import (
    AttendanceCorrectionRequest,
    AttendancePolicy,
    AttendanceRecord,
    Geofence,
    Shift,
    WifiPolicy,
)


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "start_time", "end_time", "grace_period_minutes", "is_active")
    list_filter = ("tenant", "is_active", "is_overnight")
    search_fields = ("name", "name_ar")


@admin.register(AttendancePolicy)
class AttendancePolicyAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "require_selfie", "require_gps", "require_geofence")
    list_filter = ("tenant",)
    search_fields = ("name",)


@admin.register(Geofence)
class GeofenceAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "latitude", "longitude", "radius_meters", "is_active")
    list_filter = ("tenant", "is_active")
    search_fields = ("name",)


@admin.register(WifiPolicy)
class WifiPolicyAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "ssid", "bssid", "is_active")
    list_filter = ("tenant", "is_active")
    search_fields = ("name", "ssid")


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = (
        "employee", "tenant", "date", "shift", "status",
        "clock_in_time", "clock_out_time", "is_validated", "is_offline_record",
    )
    list_filter = ("tenant", "status", "is_validated", "is_offline_record", "date")
    search_fields = ("employee__employee_id", "employee__user__email")
    date_hierarchy = "date"
    raw_id_fields = ("employee", "shift", "policy", "geofence", "clock_in_device")


@admin.register(AttendanceCorrectionRequest)
class AttendanceCorrectionRequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "tenant", "attendance_record", "status", "created_at")
    list_filter = ("tenant", "status")
    raw_id_fields = ("attendance_record", "employee", "reviewed_by")
