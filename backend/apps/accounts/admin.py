"""Admin configuration for the accounts app."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Employee, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for the custom User model."""

    list_display = (
        "email",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_filter = ("role", "is_active", "is_staff", "date_joined")
    search_fields = ("email", "first_name", "last_name", "phone")
    ordering = ("-date_joined",)
    readonly_fields = ("id", "date_joined", "last_login")

    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        (
            "Personal Info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "first_name_ar",
                    "last_name_ar",
                    "phone",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Biometric",
            {"fields": ("requires_biometric_enrollment",)},
        ),
        (
            "Important Dates",
            {"fields": ("date_joined", "last_login")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "role",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Admin interface for the Employee model."""

    list_display = (
        "employee_id",
        "user",
        "tenant",
        "department",
        "designation",
        "is_active",
        "date_of_joining",
    )
    list_filter = ("is_active", "tenant", "department", "date_of_joining")
    search_fields = (
        "employee_id",
        "user__email",
        "user__first_name",
        "user__last_name",
        "designation",
    )
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("user", "tenant", "department", "created_by")
    ordering = ("-created_at",)
