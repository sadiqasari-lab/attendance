"""HRIS integration models — webhook config, API tokens, delivery logs."""
import secrets

from django.db import models

from apps.core.models import ActiveManager, BaseModel, TenantBaseModel


class IntegrationToken(TenantBaseModel):
    """API token for external HRIS systems to authenticate against pull endpoints."""

    name = models.CharField(max_length=255, help_text="Descriptive name for this token.")
    token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Secret token value.",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    allowed_ips = models.JSONField(
        default=list,
        blank=True,
        help_text='List of allowed IP addresses (empty = allow all). E.g. ["10.0.0.1", "192.168.1.0/24"]',
    )
    rate_limit_per_minute = models.PositiveIntegerField(
        default=60,
        help_text="Max requests per minute for this token.",
    )
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta(TenantBaseModel.Meta):
        verbose_name = "Integration Token"
        verbose_name_plural = "Integration Tokens"

    def __str__(self):
        return f"{self.name} ({'active' if self.is_active else 'inactive'})"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(48)
        super().save(*args, **kwargs)


class WebhookConfig(TenantBaseModel):
    """Webhook configuration for pushing attendance events to external HRIS."""

    class Event(models.TextChoices):
        CLOCK_IN = "CLOCK_IN", "Clock In"
        CLOCK_OUT = "CLOCK_OUT", "Clock Out"
        CORRECTION_APPROVED = "CORRECTION_APPROVED", "Correction Approved"
        DAILY_SUMMARY = "DAILY_SUMMARY", "Daily Summary"

    name = models.CharField(max_length=255)
    url = models.URLField(help_text="Webhook delivery URL.")
    secret = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text="Secret for HMAC signature of webhook payloads.",
    )
    events = models.JSONField(
        default=list,
        help_text='List of event types to deliver. E.g. ["CLOCK_IN", "CLOCK_OUT"]',
    )
    is_active = models.BooleanField(default=True, db_index=True)
    headers = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom HTTP headers to include with webhook delivery.",
    )
    max_retries = models.PositiveIntegerField(default=3)
    timeout_seconds = models.PositiveIntegerField(default=30)

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta(TenantBaseModel.Meta):
        verbose_name = "Webhook Config"
        verbose_name_plural = "Webhook Configs"

    def __str__(self):
        return f"{self.name} -> {self.url}"


class IntegrationWebhookLog(BaseModel):
    """Log of webhook delivery attempts."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        DELIVERED = "DELIVERED", "Delivered"
        FAILED = "FAILED", "Failed"
        RETRYING = "RETRYING", "Retrying"

    webhook = models.ForeignKey(
        WebhookConfig,
        on_delete=models.CASCADE,
        related_name="delivery_logs",
    )
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="webhook_logs",
    )
    event_type = models.CharField(max_length=30)
    payload = models.JSONField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    response_status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    attempt_count = models.PositiveIntegerField(default=0)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = "Webhook Delivery Log"
        verbose_name_plural = "Webhook Delivery Logs"
        indexes = [
            models.Index(fields=["tenant", "event_type", "status"]),
        ]

    def __str__(self):
        return f"{self.event_type} -> {self.webhook.name} ({self.status})"
