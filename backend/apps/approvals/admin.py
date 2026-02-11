"""Admin configuration for the approvals app."""
from django.contrib import admin

from .models import ApprovalRequest


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "request_type",
        "requester",
        "status",
        "priority",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    )
    list_filter = ("request_type", "status", "priority", "tenant")
    search_fields = (
        "title",
        "description",
        "requester__user__email",
        "requester__employee_id",
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "created_by",
        "reviewed_at",
    )
    ordering = ("-created_at",)
    raw_id_fields = ("tenant", "requester", "reviewed_by", "created_by")
