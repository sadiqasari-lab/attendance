"""Django admin configuration for the tenants app."""
from django.contrib import admin

from apps.tenants.models import Department, Group, Tenant


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "name_ar", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "name_ar", "description")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("name",)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "group",
        "city",
        "country",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "country", "group", "created_at")
    search_fields = ("name", "name_ar", "slug", "email", "phone", "city")
    readonly_fields = ("id", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    raw_id_fields = ("group", "created_by")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "name_ar",
        "tenant",
        "parent",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "tenant", "created_at")
    search_fields = ("name", "name_ar", "description")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("tenant", "name")
    raw_id_fields = ("tenant", "parent", "created_by")
