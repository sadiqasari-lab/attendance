from django.contrib import admin

from .models import BiometricEnrollmentLog, BiometricTemplate


@admin.register(BiometricTemplate)
class BiometricTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "employee", "tenant", "embedding_version", "status",
        "num_images_used", "quality_score", "enrolled_at",
    )
    list_filter = ("tenant", "status")
    search_fields = ("employee__employee_id", "employee__user__email")
    raw_id_fields = ("employee",)
    readonly_fields = ("encrypted_embedding", "encryption_iv")


@admin.register(BiometricEnrollmentLog)
class BiometricEnrollmentLogAdmin(admin.ModelAdmin):
    list_display = ("employee", "tenant", "event", "created_at")
    list_filter = ("tenant", "event")
    search_fields = ("employee__employee_id",)
    raw_id_fields = ("employee", "template")
