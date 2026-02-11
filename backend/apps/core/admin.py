from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "resource_type", "user", "tenant", "created_at", "ip_address")
    list_filter = ("action", "resource_type", "tenant", "created_at")
    search_fields = ("resource_type", "details", "ip_address")
    readonly_fields = (
        "id", "tenant", "user", "action", "resource_type", "resource_id",
        "details", "ip_address", "user_agent", "created_at",
    )
    ordering = ("-created_at",)
