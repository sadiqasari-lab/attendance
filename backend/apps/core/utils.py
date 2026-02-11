"""Utility functions for the Inspire Attendance System."""
import hashlib
import json
import math

from django.utils import timezone


def get_client_ip(request):
    """Extract client IP from request, respecting X-Forwarded-For."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two GPS coordinates."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def generate_integrity_hash(data: dict) -> str:
    """Generate SHA-256 integrity hash for offline attendance data."""
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def verify_integrity_hash(data: dict, expected_hash: str) -> bool:
    """Verify integrity hash for offline attendance records."""
    return generate_integrity_hash(data) == expected_hash


def is_within_geofence(lat, lon, fence_lat, fence_lon, radius_meters):
    """Check if coordinates are within a geofence radius."""
    distance = haversine_distance(lat, lon, fence_lat, fence_lon)
    return distance <= radius_meters


def now():
    """Return timezone-aware current datetime."""
    return timezone.now()
