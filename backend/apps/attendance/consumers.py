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
        self.tenant_slug = self.scope["url_route"]["kwargs"]["tenant_slug"]
        self.group_name = f"attendance_map_{self.tenant_slug}"

        # Join the tenant attendance group
        self.channel_layer.group_add(self.group_name, self.channel_name)
        self.accept()
        logger.info("WebSocket connected: %s", self.group_name)

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
