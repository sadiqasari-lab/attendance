"""Tests for the devices app."""
import pytest

from apps.devices.models import DeviceChangeRequest, DeviceRegistry


class TestDeviceRegistryModel:
    @pytest.mark.django_db
    def test_device_creation(self, device):
        assert device.device_type == DeviceRegistry.DeviceType.COMPANY
        assert device.platform == DeviceRegistry.Platform.ANDROID
        assert device.status == DeviceRegistry.Status.ACTIVE

    @pytest.mark.django_db
    def test_device_str(self, device):
        assert "Samsung Galaxy S23" in str(device)


class TestDeviceRegistrationAPI:
    @pytest.mark.django_db
    def test_register_device(self, authenticated_client, tenant, employee):
        response = authenticated_client.post(
            f"/api/v1/{tenant.slug}/devices/register/",
            {
                "device_type": "BYOD",
                "platform": "ANDROID",
                "device_identifier": "new-device-id-67890",
                "device_model": "Pixel 8",
                "device_manufacturer": "Google",
                "os_version": "14",
                "is_rooted": False,
            },
        )
        assert response.status_code == 201
        assert response.json()["success"] is True

    @pytest.mark.django_db
    def test_reject_rooted_company_device(self, authenticated_client, tenant, employee):
        response = authenticated_client.post(
            f"/api/v1/{tenant.slug}/devices/register/",
            {
                "device_type": "COMPANY",
                "platform": "ANDROID",
                "device_identifier": "rooted-device-123",
                "is_rooted": True,
            },
        )
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_byod_one_device_per_user(self, authenticated_client, tenant, employee):
        # Register first device
        authenticated_client.post(
            f"/api/v1/{tenant.slug}/devices/register/",
            {
                "device_type": "BYOD",
                "platform": "ANDROID",
                "device_identifier": "byod-device-1",
            },
        )
        # Approve it
        dev = DeviceRegistry.objects.filter(
            employee=employee, device_identifier="byod-device-1"
        ).first()
        if dev:
            dev.status = DeviceRegistry.Status.ACTIVE
            dev.save()

        # Try registering second device
        response = authenticated_client.post(
            f"/api/v1/{tenant.slug}/devices/register/",
            {
                "device_type": "BYOD",
                "platform": "ANDROID",
                "device_identifier": "byod-device-2",
            },
        )
        assert response.status_code == 409


class TestDeviceApprovalAPI:
    @pytest.mark.django_db
    def test_approve_device(self, tenant_admin_client, tenant, device, tenant_admin_employee):
        device.status = DeviceRegistry.Status.PENDING
        device.save()

        response = tenant_admin_client.post(
            f"/api/v1/{tenant.slug}/devices/{device.id}/approve/",
            {"action": "approve"},
        )
        assert response.status_code == 200
        device.refresh_from_db()
        assert device.status == DeviceRegistry.Status.ACTIVE

    @pytest.mark.django_db
    def test_revoke_device(self, tenant_admin_client, tenant, device, tenant_admin_employee):
        response = tenant_admin_client.post(
            f"/api/v1/{tenant.slug}/devices/{device.id}/approve/",
            {"action": "revoke"},
        )
        assert response.status_code == 200
        device.refresh_from_db()
        assert device.status == DeviceRegistry.Status.REVOKED
