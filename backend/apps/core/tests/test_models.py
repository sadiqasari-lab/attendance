"""Tests for core models and utilities."""
import pytest
from django.utils import timezone

from apps.core.models import AuditLog
from apps.core.utils import (
    generate_integrity_hash,
    haversine_distance,
    is_within_geofence,
    verify_integrity_hash,
)


class TestBaseModel:
    """Test BaseModel abstract functionality via AuditLog (concrete model)."""

    @pytest.mark.django_db
    def test_audit_log_creation(self, tenant, super_admin):
        log = AuditLog.objects.create(
            tenant=tenant,
            user=super_admin,
            action="CREATE",
            resource_type="TestResource",
            resource_id=super_admin.pk,
            details={"test": True},
            ip_address="127.0.0.1",
        )
        assert log.pk is not None
        assert log.action == "CREATE"
        assert log.tenant == tenant
        assert log.details == {"test": True}

    @pytest.mark.django_db
    def test_soft_delete(self, tenant, super_admin):
        log = AuditLog.objects.create(
            tenant=tenant,
            user=super_admin,
            action="CREATE",
            resource_type="TestResource",
        )
        assert log.is_deleted is False
        log.soft_delete()
        log.refresh_from_db()
        assert log.is_deleted is True
        assert log.deleted_at is not None

    @pytest.mark.django_db
    def test_uuid_primary_key(self, tenant, super_admin):
        log = AuditLog.objects.create(
            tenant=tenant,
            user=super_admin,
            action="LOGIN",
            resource_type="User",
        )
        assert len(str(log.pk)) == 36  # UUID format


class TestUtils:
    def test_haversine_distance_same_point(self):
        d = haversine_distance(24.7136, 46.6753, 24.7136, 46.6753)
        assert d == 0.0

    def test_haversine_distance_known_distance(self):
        # Riyadh to Jeddah ~roughly 850km
        d = haversine_distance(24.7136, 46.6753, 21.4858, 39.1925)
        assert 800000 < d < 900000

    def test_is_within_geofence_inside(self):
        assert is_within_geofence(24.7136, 46.6753, 24.7136, 46.6753, 100)

    def test_is_within_geofence_outside(self):
        assert not is_within_geofence(24.7136, 46.6753, 24.72, 46.68, 100)

    def test_integrity_hash_generation(self):
        data = {"employee_id": "EMP001", "date": "2026-01-01", "shift": "Morning"}
        h = generate_integrity_hash(data)
        assert len(h) == 64  # SHA-256 hex

    def test_integrity_hash_verification(self):
        data = {"employee_id": "EMP001", "date": "2026-01-01"}
        h = generate_integrity_hash(data)
        assert verify_integrity_hash(data, h) is True
        assert verify_integrity_hash(data, "wrong-hash") is False

    def test_integrity_hash_deterministic(self):
        data = {"b": 2, "a": 1}
        h1 = generate_integrity_hash(data)
        h2 = generate_integrity_hash(data)
        assert h1 == h2
