"""Tests for the attendance validation engine."""
import io
from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from django.test import RequestFactory
from django.utils import timezone
from PIL import Image

from apps.attendance.validators import AttendanceValidator


def _make_test_image():
    """Create a minimal in-memory image for testing."""
    img = Image.new("RGB", (100, 100), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    buf.name = "test.jpg"
    return buf


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def valid_data(tenant, employee, shift, geofence, device, attendance_policy):
    return {
        "tenant": tenant,
        "employee": employee,
        "employee_id": employee.id,
        "shift": shift,
        "shift_id": shift.id,
        "date": timezone.localdate(),
        "selfie": _make_test_image(),
        "latitude": Decimal("24.7136000"),
        "longitude": Decimal("46.6753000"),
        "gps_accuracy": 10.0,
        "device_id": device.id,
        "wifi_ssid": "",
        "wifi_bssid": "",
        "client_timestamp": timezone.now(),
        "liveness_passed": True,
        "face_match_score": 0.85,
        "is_mock_location": False,
        "geofence_id": geofence.id,
        "is_offline": False,
    }


class TestAttendanceValidator:
    @pytest.mark.django_db
    def test_validate_selfie_present(self, valid_data, request_factory, tenant):
        req = request_factory.post("/")
        req.tenant = tenant
        validator = AttendanceValidator(valid_data, req)
        validator.validate_selfie()
        assert len(validator.errors) == 0

    @pytest.mark.django_db
    def test_validate_selfie_missing(self, valid_data, request_factory, tenant):
        valid_data["selfie"] = None
        req = request_factory.post("/")
        req.tenant = tenant
        validator = AttendanceValidator(valid_data, req)
        validator.validate_selfie()
        assert len(validator.errors) > 0

    @pytest.mark.django_db
    def test_validate_liveness_passed(self, valid_data, request_factory, tenant):
        req = request_factory.post("/")
        req.tenant = tenant
        validator = AttendanceValidator(valid_data, req)
        validator.validate_liveness()
        assert len(validator.errors) == 0

    @pytest.mark.django_db
    def test_validate_liveness_failed(self, valid_data, request_factory, tenant):
        valid_data["liveness_passed"] = False
        req = request_factory.post("/")
        req.tenant = tenant
        validator = AttendanceValidator(valid_data, req)
        validator.validate_liveness()
        assert len(validator.errors) > 0

    @pytest.mark.django_db
    def test_validate_fake_gps_detected(self, valid_data, request_factory, tenant):
        valid_data["is_mock_location"] = True
        req = request_factory.post("/")
        req.tenant = tenant
        validator = AttendanceValidator(valid_data, req)
        validator.validate_fake_gps()
        assert len(validator.errors) > 0

    @pytest.mark.django_db
    def test_validate_geofence_within(self, valid_data, request_factory, tenant, geofence):
        req = request_factory.post("/")
        req.tenant = tenant
        validator = AttendanceValidator(valid_data, req)
        validator.validate_geofence()
        assert validator.geofence_valid is True

    @pytest.mark.django_db
    def test_validate_geofence_outside(self, valid_data, request_factory, tenant, geofence):
        valid_data["latitude"] = Decimal("25.0000000")
        valid_data["longitude"] = Decimal("47.0000000")
        req = request_factory.post("/")
        req.tenant = tenant
        validator = AttendanceValidator(valid_data, req)
        validator.validate_geofence()
        assert validator.geofence_valid is False

    @pytest.mark.django_db
    def test_validate_device_registered(self, valid_data, request_factory, tenant):
        req = request_factory.post("/")
        req.tenant = tenant
        validator = AttendanceValidator(valid_data, req)
        validator.validate_device()
        assert validator.device_valid is True

    @pytest.mark.django_db
    def test_validate_clock_tampering_no_skew(self, valid_data, request_factory, tenant):
        req = request_factory.post("/")
        req.tenant = tenant
        validator = AttendanceValidator(valid_data, req)
        validator.validate_clock_tampering()
        assert validator.clock_skew_detected is False

    @pytest.mark.django_db
    def test_validate_clock_tampering_with_skew(self, valid_data, request_factory, tenant):
        valid_data["client_timestamp"] = timezone.now() - timedelta(hours=2)
        req = request_factory.post("/")
        req.tenant = tenant
        validator = AttendanceValidator(valid_data, req)
        validator.validate_clock_tampering()
        assert validator.clock_skew_detected is True

    @pytest.mark.django_db
    def test_validate_duplicate_prevention(self, valid_data, request_factory, tenant, attendance_record):
        req = request_factory.post("/")
        req.tenant = tenant
        validator = AttendanceValidator(valid_data, req)
        validator.validate_duplicate()
        assert len(validator.errors) > 0  # duplicate exists

    @pytest.mark.django_db
    def test_validate_gps_missing(self, valid_data, request_factory, tenant):
        valid_data["latitude"] = None
        valid_data["longitude"] = None
        req = request_factory.post("/")
        req.tenant = tenant
        validator = AttendanceValidator(valid_data, req)
        validator.validate_gps()
        assert len(validator.errors) > 0
