"""App configuration for the attendance app."""
from django.apps import AppConfig


class AttendanceConfig(AppConfig):
    """Configuration for the core attendance tracking application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.attendance"
    verbose_name = "Attendance"

    def ready(self):
        """Import signal handlers when the app is ready."""
        pass
