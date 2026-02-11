from django.contrib import admin

from .models import DeviceChangeRequest, DeviceRegistry


@admin.register(DeviceRegistry)
class DeviceRegistryAdmin(admin.ModelAdmin):
    list_display = (
        "employee", "tenant", "device_type", "platform", "device_model",
        "status", "is_rooted", "registered_at",
    )
    list_filter = ("tenant", "device_type", "platform", "status", "is_rooted")
    search_fields = ("employee__employee_id", "device_identifier", "device_model")
    raw_id_fields = ("employee",)


@admin.register(DeviceChangeRequest)
class DeviceChangeRequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "tenant", "status", "new_platform", "created_at")
    list_filter = ("tenant", "status")
    raw_id_fields = ("employee", "old_device", "reviewed_by")
