"""WebSocket URL routing for Inspire Attendance System."""
from django.urls import re_path

from apps.attendance.consumers import AttendanceMapConsumer

websocket_urlpatterns = [
    re_path(
        r"ws/(?P<tenant_slug>[\w-]+)/attendance/map/$",
        AttendanceMapConsumer.as_asgi(),
    ),
]
