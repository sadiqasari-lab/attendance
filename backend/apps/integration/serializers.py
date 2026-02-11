"""Serializers for the integration (HRIS) app."""
from rest_framework import serializers

from .models import IntegrationToken, IntegrationWebhookLog, WebhookConfig


class IntegrationTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationToken
        fields = [
            "id", "name", "token", "is_active", "allowed_ips",
            "rate_limit_per_minute", "last_used_at", "expires_at",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "token", "last_used_at", "created_at", "updated_at"]


class IntegrationTokenCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationToken
        fields = [
            "name", "allowed_ips", "rate_limit_per_minute", "expires_at",
        ]


class WebhookConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookConfig
        fields = [
            "id", "name", "url", "secret", "events", "is_active",
            "headers", "max_retries", "timeout_seconds",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "secret": {"write_only": True},
        }


class IntegrationWebhookLogSerializer(serializers.ModelSerializer):
    webhook_name = serializers.CharField(source="webhook.name", read_only=True)

    class Meta:
        model = IntegrationWebhookLog
        fields = [
            "id", "webhook", "webhook_name", "tenant", "event_type",
            "payload", "status", "response_status_code", "response_body",
            "error_message", "attempt_count", "delivered_at", "created_at",
        ]
        read_only_fields = fields


class AttendanceLogPullSerializer(serializers.Serializer):
    """Serializer for HRIS pull endpoint — attendance logs."""
    employee_id = serializers.CharField()
    employee_email = serializers.EmailField()
    date = serializers.DateField()
    shift_name = serializers.CharField()
    clock_in_time = serializers.DateTimeField(allow_null=True)
    clock_out_time = serializers.DateTimeField(allow_null=True)
    status = serializers.CharField()
    duration_hours = serializers.FloatField(allow_null=True)
    is_validated = serializers.BooleanField()


class ShiftPullSerializer(serializers.Serializer):
    """Serializer for HRIS pull endpoint — shifts."""
    shift_id = serializers.UUIDField()
    name = serializers.CharField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    grace_period_minutes = serializers.IntegerField()
    is_overnight = serializers.BooleanField()
