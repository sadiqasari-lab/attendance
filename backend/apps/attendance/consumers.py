"""WebSocket consumer for real-time attendance map."""
import json
import logging

from channels.generic.websocket import JsonWebsocketConsumer

logger = logging.getLogger(__name__)


class AttendanceMapConsumer(JsonWebsocketConsumer):
    """
    WebSocket consumer for live attendance map.
    Clients connect to ws/{tenant_slug}/attendance/map/
    and receive real-time clock-in/out events with location data.
    """

    def connect(self):
        # Authenticate: reject anonymous connections
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            self.close()
            return

        self.tenant_slug = self.scope["url_route"]["kwargs"]["tenant_slug"]

        # Verify the user belongs to this tenant
        if user.role != "SUPER_ADMIN":
            from apps.tenants.models import Tenant

            tenant_exists = Tenant.objects.filter(
                slug=self.tenant_slug, is_deleted=False
            ).exists()
            if not tenant_exists:
                self.close()
                return

            has_access = user.employee_profiles.filter(
                tenant__slug=self.tenant_slug, is_deleted=False
            ).exists()
            if not has_access:
                self.close()
                return

        self.group_name = f"attendance_map_{self.tenant_slug}"

        # Join the tenant attendance group
        self.channel_layer.group_add(self.group_name, self.channel_name)
        self.accept()
        logger.info("WebSocket connected: user=%s group=%s", user, self.group_name)

    def disconnect(self, close_code):
        self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info("WebSocket disconnected: %s", self.group_name)

    def receive_json(self, content, **kwargs):
        """Handle incoming messages from clients (e.g., map viewport updates)."""
        msg_type = content.get("type")
        if msg_type == "ping":
            self.send_json({"type": "pong"})

    def attendance_event(self, event):
        """Broadcast attendance event to connected clients."""
        self.send_json(event["data"])
