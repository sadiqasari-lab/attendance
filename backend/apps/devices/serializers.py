"""Serializers for the devices app."""
from rest_framework import serializers

from .models import DeviceChangeRequest, DeviceRegistry


class DeviceRegistrySerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source="employee.user.get_full_name", read_only=True
    )

    class Meta:
        model = DeviceRegistry
        fields = [
            "id", "employee", "employee_name", "device_type", "platform",
            "device_identifier", "device_model", "device_manufacturer",
            "os_version", "app_version", "is_rooted", "status",
            "registered_at", "last_active_at", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "status", "is_rooted", "registered_at",
            "last_active_at", "created_at", "updated_at",
        ]


class DeviceRegisterSerializer(serializers.Serializer):
    """Serializer for initial device registration."""
    device_type = serializers.ChoiceField(choices=DeviceRegistry.DeviceType.choices)
    platform = serializers.ChoiceField(choices=DeviceRegistry.Platform.choices)
    device_identifier = serializers.CharField(max_length=255)
    device_model = serializers.CharField(max_length=255, required=False, default="")
    device_manufacturer = serializers.CharField(max_length=255, required=False, default="")
    os_version = serializers.CharField(max_length=50, required=False, default="")
    app_version = serializers.CharField(max_length=50, required=False, default="")
    fcm_token = serializers.CharField(required=False, default="")
    is_rooted = serializers.BooleanField(default=False)


class DeviceChangeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceChangeRequest
        fields = [
            "id", "employee", "old_device", "new_device_identifier",
            "new_device_model", "new_platform", "reason",
            "status", "reviewed_by", "reviewed_at",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "old_device", "status", "reviewed_by",
            "reviewed_at", "created_at", "updated_at",
        ]


class RootDetectionSerializer(serializers.Serializer):
    device_identifier = serializers.CharField(max_length=255)
    is_rooted = serializers.BooleanField()
    root_indicators = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
