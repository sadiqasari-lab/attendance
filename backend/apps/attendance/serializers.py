"""Serializers for the attendance app."""
from rest_framework import serializers

from apps.accounts.serializers import EmployeeSerializer

from .models import (
    AttendanceCorrectionRequest,
    AttendancePolicy,
    AttendanceRecord,
    Geofence,
    Shift,
    WifiPolicy,
)


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = [
            "id", "name", "name_ar", "start_time", "end_time",
            "grace_period_minutes", "is_overnight", "is_active",
            "description", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AttendancePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendancePolicy
        fields = [
            "id", "name", "name_ar",
            "require_selfie", "require_liveness", "require_gps",
            "require_geofence", "require_wifi", "require_device_registered",
            "max_offline_per_shift", "allow_early_clockin_minutes",
            "allow_late_clockout_minutes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GeofenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geofence
        fields = [
            "id", "name", "name_ar", "latitude", "longitude",
            "radius_meters", "is_active", "description",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class WifiPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = WifiPolicy
        fields = [
            "id", "name", "ssid", "bssid", "geofence",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee_detail = EmployeeSerializer(source="employee", read_only=True)
    shift_name = serializers.CharField(source="shift.name", read_only=True)
    duration_hours = serializers.FloatField(read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = [
            "id", "employee", "employee_detail", "shift", "shift_name",
            "policy", "date", "clock_in_time", "clock_out_time", "status",
            "clock_in_latitude", "clock_in_longitude",
            "clock_out_latitude", "clock_out_longitude",
            "is_offline_record", "is_validated", "validation_errors",
            "is_synced", "liveness_passed", "face_match_score",
            "gps_accuracy", "geofence", "geofence_valid",
            "wifi_valid", "device_valid", "clock_skew_detected",
            "duration_hours", "notes", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "is_validated", "validation_errors", "is_synced",
            "liveness_passed", "face_match_score", "geofence_valid",
            "wifi_valid", "device_valid", "clock_skew_detected",
            "duration_hours", "created_at", "updated_at",
        ]


class ClockInSerializer(serializers.Serializer):
    shift_id = serializers.UUIDField()
    selfie = serializers.ImageField()
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    gps_accuracy = serializers.FloatField(required=False)
    device_id = serializers.UUIDField(required=False)
    wifi_ssid = serializers.CharField(max_length=100, required=False, default="")
    wifi_bssid = serializers.CharField(max_length=17, required=False, default="")
    client_timestamp = serializers.DateTimeField()
    liveness_passed = serializers.BooleanField(default=False)
    face_match_score = serializers.FloatField(required=False)
    is_mock_location = serializers.BooleanField(default=False)
    geofence_id = serializers.UUIDField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, default="")


class ClockOutSerializer(serializers.Serializer):
    record_id = serializers.UUIDField()
    selfie = serializers.ImageField(required=False)
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    gps_accuracy = serializers.FloatField(required=False)
    client_timestamp = serializers.DateTimeField()
    notes = serializers.CharField(required=False, default="")


class OfflineSyncSerializer(serializers.Serializer):
    shift_id = serializers.UUIDField()
    selfie = serializers.ImageField()
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    gps_accuracy = serializers.FloatField(required=False)
    device_id = serializers.UUIDField(required=False)
    wifi_ssid = serializers.CharField(max_length=100, required=False, default="")
    wifi_bssid = serializers.CharField(max_length=17, required=False, default="")
    client_timestamp = serializers.DateTimeField()
    liveness_passed = serializers.BooleanField(default=False)
    face_match_score = serializers.FloatField(required=False)
    integrity_hash = serializers.CharField(max_length=64)
    is_mock_location = serializers.BooleanField(default=False)
    geofence_id = serializers.UUIDField(required=False, allow_null=True)
    date = serializers.DateField()
    clock_in_time = serializers.DateTimeField()
    notes = serializers.CharField(required=False, default="")


class AttendanceCorrectionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceCorrectionRequest
        fields = [
            "id", "attendance_record", "employee", "reason",
            "requested_clock_in", "requested_clock_out",
            "status", "reviewed_by", "reviewed_at", "review_notes",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "status", "reviewed_by", "reviewed_at",
            "review_notes", "created_at", "updated_at",
        ]


class AttendanceSummarySerializer(serializers.Serializer):
    employee_id = serializers.UUIDField()
    employee_name = serializers.CharField()
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    total_days = serializers.IntegerField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    late_count = serializers.IntegerField()
    early_departure_count = serializers.IntegerField()
    half_day_count = serializers.IntegerField()
    leave_count = serializers.IntegerField()
    total_hours = serializers.FloatField()
    avg_hours_per_day = serializers.FloatField()
