"""Device registry models for company and BYOD device management."""
from django.conf import settings
from django.db import models

from apps.core.models import ActiveManager, TenantBaseModel


class DeviceRegistry(TenantBaseModel):
    """Registered device for attendance tracking — supports company and BYOD."""

    class DeviceType(models.TextChoices):
        COMPANY = "COMPANY", "Company Device"
        BYOD = "BYOD", "Bring Your Own Device"

    class Platform(models.TextChoices):
        ANDROID = "ANDROID", "Android"
        IOS = "IOS", "iOS"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        PENDING = "PENDING", "Pending Approval"
        REVOKED = "REVOKED", "Revoked"
        REPLACED = "REPLACED", "Replaced"

    employee = models.ForeignKey(
        "accounts.Employee",
        on_delete=models.CASCADE,
        related_name="devices",
    )
    device_type = models.CharField(
        max_length=10,
        choices=DeviceType.choices,
        default=DeviceType.BYOD,
    )
    platform = models.CharField(
        max_length=10,
        choices=Platform.choices,
    )
    device_identifier = models.CharField(
        max_length=255,
        help_text="Unique device identifier (Android ID or iOS Vendor ID).",
    )
    device_model = models.CharField(max_length=255, blank=True, default="")
    device_manufacturer = models.CharField(max_length=255, blank=True, default="")
    os_version = models.CharField(max_length=50, blank=True, default="")
    app_version = models.CharField(max_length=50, blank=True, default="")
    fcm_token = models.TextField(
        blank=True, default="",
        help_text="Firebase Cloud Messaging token for push notifications.",
    )
    is_rooted = models.BooleanField(
        default=False,
        help_text="Whether the device has been detected as rooted/jailbroken.",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    registered_at = models.DateTimeField(auto_now_add=True)
    last_active_at = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta(TenantBaseModel.Meta):
        verbose_name = "Device Registry"
        verbose_name_plural = "Device Registries"
        indexes = [
            models.Index(fields=["tenant", "employee", "status"]),
            models.Index(fields=["device_identifier"]),
        ]

    def __str__(self):
        return f"{self.employee} - {self.device_model} ({self.platform})"


class DeviceChangeRequest(TenantBaseModel):
    """Request to change registered device (BYOD one-device-per-user enforcement)."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    employee = models.ForeignKey(
        "accounts.Employee",
        on_delete=models.CASCADE,
        related_name="device_change_requests",
    )
    old_device = models.ForeignKey(
        DeviceRegistry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replaced_by_requests",
    )
    new_device_identifier = models.CharField(max_length=255)
    new_device_model = models.CharField(max_length=255, blank=True, default="")
    new_platform = models.CharField(
        max_length=10,
        choices=DeviceRegistry.Platform.choices,
    )
    reason = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="device_reviews",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta(TenantBaseModel.Meta):
        verbose_name = "Device Change Request"
        verbose_name_plural = "Device Change Requests"

    def __str__(self):
        return f"Device change for {self.employee} - {self.status}"
