"""Tests for attendance models."""
import pytest
from datetime import time
from decimal import Decimal
from django.utils import timezone

from apps.attendance.models import (
    AttendanceCorrectionRequest,
    AttendancePolicy,
    AttendanceRecord,
    Geofence,
    Shift,
    WifiPolicy,
)


class TestShiftModel:
    @pytest.mark.django_db
    def test_shift_creation(self, shift):
        assert shift.name == "Morning Shift"
        assert shift.start_time == time(8, 0)
        assert shift.end_time == time(16, 0)
        assert shift.grace_period_minutes == 15

    @pytest.mark.django_db
    def test_shift_str(self, shift):
        assert "Morning Shift" in str(shift)

    @pytest.mark.django_db
    def test_shift_unique_per_tenant(self, tenant, shift):
        with pytest.raises(Exception):
            Shift.objects.create(
                tenant=tenant,
                name="Morning Shift",
                start_time=time(9, 0),
                end_time=time(17, 0),
            )


class TestAttendancePolicyModel:
    @pytest.mark.django_db
    def test_policy_defaults(self, attendance_policy):
        assert attendance_policy.require_selfie is True
        assert attendance_policy.require_liveness is True
        assert attendance_policy.require_gps is True
        assert attendance_policy.require_wifi is False
        assert attendance_policy.max_offline_per_shift == 1


class TestGeofenceModel:
    @pytest.mark.django_db
    def test_geofence_creation(self, geofence):
        assert geofence.latitude == Decimal("24.7136000")
        assert geofence.radius_meters == 200

    @pytest.mark.django_db
    def test_geofence_str(self, geofence):
        assert "HQ Office" in str(geofence)


class TestWifiPolicyModel:
    @pytest.mark.django_db
    def test_wifi_policy_creation(self, wifi_policy):
        assert wifi_policy.ssid == "ArabInspire-Corp"
        assert wifi_policy.geofence is not None


class TestAttendanceRecordModel:
    @pytest.mark.django_db
    def test_record_creation(self, attendance_record):
        assert attendance_record.status == AttendanceRecord.Status.PRESENT
        assert attendance_record.is_validated is True

    @pytest.mark.django_db
    def test_record_unique_constraint(self, tenant, employee, shift, attendance_record):
        """Cannot create duplicate record for same employee/date/shift."""
        with pytest.raises(Exception):
            AttendanceRecord.objects.create(
                tenant=tenant,
                employee=employee,
                shift=shift,
                date=timezone.localdate(),
                status=AttendanceRecord.Status.PRESENT,
            )

    @pytest.mark.django_db
    def test_duration_with_clockout(self, attendance_record):
        from datetime import timedelta
        attendance_record.clock_out_time = attendance_record.clock_in_time + timedelta(hours=8)
        attendance_record.save()
        assert attendance_record.duration is not None
        assert abs(attendance_record.duration_hours - 8.0) < 0.01

    @pytest.mark.django_db
    def test_duration_without_clockout(self, attendance_record):
        assert attendance_record.duration is None
        assert attendance_record.duration_hours is None


class TestAttendanceCorrectionRequest:
    @pytest.mark.django_db
    def test_correction_request(self, tenant, employee, attendance_record):
        correction = AttendanceCorrectionRequest.objects.create(
            tenant=tenant,
            employee=employee,
            attendance_record=attendance_record,
            reason="Forgot to clock out",
            status=AttendanceCorrectionRequest.Status.PENDING,
        )
        assert correction.status == "PENDING"
        assert correction.reviewed_by is None
