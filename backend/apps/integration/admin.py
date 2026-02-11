from django.contrib import admin

from .models import IntegrationToken, IntegrationWebhookLog, WebhookConfig


@admin.register(IntegrationToken)
class IntegrationTokenAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "is_active", "last_used_at", "expires_at")
    list_filter = ("tenant", "is_active")
    search_fields = ("name",)
    readonly_fields = ("token",)


@admin.register(WebhookConfig)
class WebhookConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "url", "is_active", "events")
    list_filter = ("tenant", "is_active")
    search_fields = ("name", "url")


@admin.register(IntegrationWebhookLog)
class IntegrationWebhookLogAdmin(admin.ModelAdmin):
    list_display = (
        "webhook", "tenant", "event_type", "status",
        "response_status_code", "attempt_count", "created_at",
    )
    list_filter = ("tenant", "status", "event_type")
    readonly_fields = (
        "webhook", "tenant", "event_type", "payload", "status",
        "response_status_code", "response_body", "error_message",
        "attempt_count", "delivered_at",
    )
