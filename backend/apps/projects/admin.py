"""Admin configuration for the projects app."""
from django.contrib import admin

from .models import EmployeeProjectAssignment, Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "tenant",
        "status",
        "is_active",
        "start_date",
        "end_date",
        "created_at",
    )
    list_filter = ("status", "is_active", "tenant")
    search_fields = ("name", "name_ar", "location_name")
    readonly_fields = ("id", "created_at", "updated_at", "created_by")
    ordering = ("-created_at",)
    raw_id_fields = ("tenant", "geofence", "created_by")


@admin.register(EmployeeProjectAssignment)
class EmployeeProjectAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "project",
        "role",
        "is_active",
        "start_date",
        "end_date",
        "created_at",
    )
    list_filter = ("role", "is_active", "project")
    search_fields = (
        "employee__user__email",
        "employee__employee_id",
        "project__name",
    )
    readonly_fields = ("id", "created_at", "updated_at", "created_by")
    ordering = ("-created_at",)
    raw_id_fields = ("tenant", "employee", "project", "created_by")
