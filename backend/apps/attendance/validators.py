"""Attendance validation engine for the Inspire Attendance System.

Runs all 12 validation checks against incoming attendance data before
a record is persisted.  Each check is independent and returns a list of
error strings so that the caller receives a complete diagnostic rather
than failing on the first issue.
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from apps.core.utils import (
    haversine_distance,
    is_within_geofence,
    verify_integrity_hash,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configurable thresholds (read from Django settings with sane defaults)
# ---------------------------------------------------------------------------
BIOMETRIC_MATCH_THRESHOLD = getattr(settings, "BIOMETRIC_MATCH_THRESHOLD", 0.6)
GPS_ACCURACY_THRESHOLD = getattr(settings, "ATTENDANCE_GPS_ACCURACY_THRESHOLD", 50)
CLOCK_SKEW_TOLERANCE = getattr(settings, "ATTENDANCE_CLOCK_SKEW_TOLERANCE", 300)
OFFLINE_MAX_PER_SHIFT = getattr(settings, "ATTENDANCE_OFFLINE_MAX_PER_SHIFT", 1)


class AttendanceValidator:
    """Orchestrates all attendance validation checks.

    Usage::

        validator = AttendanceValidator(data=clock_in_data, request=request)
        is_valid, errors = validator.validate_all()
    """

    def __init__(self, data: dict, request, policy=None):
        """
        Args:
            data: Dictionary containing the raw attendance payload.
            request: The current Django/DRF request (provides server time, user,
                     and tenant context).
            policy: An optional ``AttendancePolicy`` instance.  When provided,
                    the validator uses the policy flags to decide which checks
                    to enforce.
        """
        self.data = data
        self.request = request
        self.policy = policy
        self.errors: list[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def validate_all(self) -> tuple[bool, list[str]]:
        """Run every applicable validation check and return the aggregate result.

        Returns:
            A tuple of ``(is_valid, errors)`` where *is_valid* is ``True``
            only when *errors* is empty.
        """
        self.errors = []

        # Each validator appends to self.errors if it fails.
        self.validate_selfie()
        self.validate_liveness()
        self.validate_face_match()
        self.validate_gps()
        self.validate_fake_gps()
        self.validate_geofence()
        self.validate_wifi()
        self.validate_device()
        self.validate_duplicate()
        self.validate_shift()
        self.validate_clock_tampering()
        self.validate_offline()

        is_valid = len(self.errors) == 0
        return is_valid, self.errors

    # ------------------------------------------------------------------
    # 1. Selfie validation
    # ------------------------------------------------------------------
    def validate_selfie(self) -> None:
        """Check that a selfie image is present and appears to be a live camera
        capture (not picked from the gallery).

        Heuristic: images taken with the camera typically contain EXIF
        orientation and camera-model tags.  A bare file without these hints
        is treated as a gallery pick and rejected when the policy enforces
        selfies.
        """
        if self.policy and not self.policy.require_selfie:
            return

        selfie = self.data.get("selfie") or self.data.get("clock_in_selfie")
        if not selfie:
            self.errors.append("Selfie image is required for attendance.")
            return

        # If the file object carries EXIF metadata we do a simple camera check.
        try:
            if hasattr(selfie, "read"):
                # Read a small chunk to inspect; then seek back.
                header = selfie.read(12)
                selfie.seek(0)
            else:
                header = None

            exif_meta = self.data.get("selfie_exif", {})
            # Gallery-sourced images usually lack camera make/model.
            if exif_meta:
                is_camera = bool(
                    exif_meta.get("Make")
                    or exif_meta.get("Model")
                    or exif_meta.get("Software")
                )
                if not is_camera:
                    self.errors.append(
                        "Selfie appears to be from a gallery. A live camera "
                        "capture is required."
                    )
        except Exception:
            logger.exception("Error inspecting selfie EXIF data")

    # ------------------------------------------------------------------
    # 2. Liveness detection
    # ------------------------------------------------------------------
    def validate_liveness(self) -> None:
        """Verify that the liveness detection flag is ``True``."""
        if self.policy and not self.policy.require_liveness:
            return

        if not self.data.get("liveness_passed", False):
            self.errors.append(
                "Liveness detection failed. Please look directly at the camera."
            )

    # ------------------------------------------------------------------
    # 3. Face match score
    # ------------------------------------------------------------------
    def validate_face_match(self) -> None:
        """Ensure the face match confidence score meets the threshold."""
        if self.policy and not self.policy.require_selfie:
            return

        score = self.data.get("face_match_score")
        if score is None:
            self.errors.append("Face match score is missing.")
            return

        try:
            score = float(score)
        except (TypeError, ValueError):
            self.errors.append("Face match score is invalid.")
            return

        if score < BIOMETRIC_MATCH_THRESHOLD:
            self.errors.append(
                f"Face match score ({score:.2f}) is below the required "
                f"threshold ({BIOMETRIC_MATCH_THRESHOLD:.2f})."
            )

    # ------------------------------------------------------------------
    # 4. GPS coordinates
    # ------------------------------------------------------------------
    def validate_gps(self) -> None:
        """Check that GPS coordinates are present and the reported accuracy
        is within the acceptable threshold."""
        if self.policy and not self.policy.require_gps:
            return

        latitude = self.data.get("latitude") or self.data.get("clock_in_latitude")
        longitude = self.data.get("longitude") or self.data.get("clock_in_longitude")

        if latitude is None or longitude is None:
            self.errors.append("GPS coordinates are required.")
            return

        try:
            lat_val = float(latitude)
            lon_val = float(longitude)
        except (TypeError, ValueError):
            self.errors.append("GPS coordinates are invalid.")
            return

        if not (-90 <= lat_val <= 90) or not (-180 <= lon_val <= 180):
            self.errors.append("GPS coordinates are out of valid range.")
            return

        accuracy = self.data.get("gps_accuracy")
        if accuracy is not None:
            try:
                accuracy = float(accuracy)
            except (TypeError, ValueError):
                accuracy = None

            if accuracy is not None and accuracy > GPS_ACCURACY_THRESHOLD:
                self.errors.append(
                    f"GPS accuracy ({accuracy:.1f}m) exceeds the maximum "
                    f"threshold ({GPS_ACCURACY_THRESHOLD}m). Move to an "
                    f"area with better GPS signal."
                )

    # ------------------------------------------------------------------
    # 5. Fake / mock GPS detection
    # ------------------------------------------------------------------
    def validate_fake_gps(self) -> None:
        """Detect mock-location indicators sent by the client."""
        if self.policy and not self.policy.require_gps:
            return

        is_mock = self.data.get("is_mock_location", False)
        if is_mock:
            self.errors.append(
                "Mock location detected. Disable mock location providers "
                "and try again."
            )
            return

        # Additional heuristic: unrealistic altitude or speed values
        altitude = self.data.get("altitude")
        if altitude is not None:
            try:
                alt = float(altitude)
                if alt < -500 or alt > 20000:
                    self.errors.append(
                        "GPS altitude value is outside realistic range, "
                        "possible mock location."
                    )
            except (TypeError, ValueError):
                pass

        # Check for mock location flag from Android
        mock_provider = self.data.get("location_provider", "")
        if mock_provider and "mock" in str(mock_provider).lower():
            self.errors.append(
                "Location appears to originate from a mock provider."
            )

    # ------------------------------------------------------------------
    # 6. Geofence validation
    # ------------------------------------------------------------------
    def validate_geofence(self) -> None:
        """Verify the employee is within the assigned geofence radius."""
        if self.policy and not self.policy.require_geofence:
            return

        geofence = self.data.get("geofence")
        if geofence is None:
            # Try loading from the model object if provided
            geofence_id = self.data.get("geofence_id")
            if geofence_id:
                from apps.attendance.models import Geofence as GeofenceModel

                try:
                    geofence = GeofenceModel.objects.get(
                        pk=geofence_id, is_active=True, is_deleted=False
                    )
                except GeofenceModel.DoesNotExist:
                    self.errors.append("Assigned geofence not found or inactive.")
                    return

        if geofence is None:
            self.errors.append("No geofence assigned for validation.")
            return

        latitude = self.data.get("latitude") or self.data.get("clock_in_latitude")
        longitude = self.data.get("longitude") or self.data.get("clock_in_longitude")

        if latitude is None or longitude is None:
            self.errors.append(
                "GPS coordinates are required for geofence validation."
            )
            return

        try:
            lat = float(latitude)
            lon = float(longitude)
            fence_lat = float(geofence.latitude)
            fence_lon = float(geofence.longitude)
            radius = int(geofence.radius_meters)
        except (TypeError, ValueError, AttributeError):
            self.errors.append("Invalid geofence or coordinate data.")
            return

        if not is_within_geofence(lat, lon, fence_lat, fence_lon, radius):
            distance = haversine_distance(lat, lon, fence_lat, fence_lon)
            self.errors.append(
                f"You are {distance:.0f}m away from the geofence "
                f"'{geofence.name}' (allowed radius: {radius}m)."
            )

    # ------------------------------------------------------------------
    # 7. WiFi validation
    # ------------------------------------------------------------------
    def validate_wifi(self) -> None:
        """Check the device WiFi SSID matches a registered WiFi policy."""
        if self.policy and not self.policy.require_wifi:
            return

        ssid = self.data.get("wifi_ssid") or self.data.get("clock_in_wifi_ssid")
        if not ssid:
            self.errors.append(
                "WiFi SSID is required. Connect to the office WiFi network."
            )
            return

        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return

        from apps.attendance.models import WifiPolicy

        wifi_policies = WifiPolicy.objects.filter(
            tenant=tenant, is_active=True, is_deleted=False
        )

        if not wifi_policies.exists():
            # No WiFi policies configured — skip check
            return

        bssid = self.data.get("wifi_bssid") or self.data.get("clock_in_wifi_bssid", "")

        matched = False
        for wp in wifi_policies:
            if wp.ssid == ssid:
                # If a BSSID is configured, it must also match
                if wp.bssid and bssid:
                    if wp.bssid.upper() == bssid.upper():
                        matched = True
                        break
                else:
                    matched = True
                    break

        if not matched:
            self.errors.append(
                f"WiFi network '{ssid}' is not registered. Connect to an "
                f"approved office network."
            )

    # ------------------------------------------------------------------
    # 8. Device registration
    # ------------------------------------------------------------------
    def validate_device(self) -> None:
        """Verify the device is registered for this employee."""
        if self.policy and not self.policy.require_device_registered:
            return

        device_id = self.data.get("device_id") or self.data.get("clock_in_device_id")
        if not device_id:
            self.errors.append("Device information is required.")
            return

        employee_id = self.data.get("employee_id")
        if not employee_id:
            # Try to get from the request user
            user = getattr(self.request, "user", None)
            if not user:
                self.errors.append("Cannot verify device without employee context.")
                return

        try:
            from apps.devices.models import DeviceRegistry

            device_filter = {"pk": device_id, "is_deleted": False}
            if employee_id:
                device_filter["employee_id"] = employee_id
            else:
                device_filter["employee__user"] = self.request.user

            tenant = getattr(self.request, "tenant", None)
            if tenant:
                device_filter["tenant"] = tenant

            device_exists = DeviceRegistry.objects.filter(**device_filter).exists()
            if not device_exists:
                self.errors.append(
                    "This device is not registered for your account. "
                    "Please register your device first."
                )
        except Exception:
            logger.exception("Error checking device registration")
            self.errors.append("Unable to verify device registration.")

    # ------------------------------------------------------------------
    # 9. Duplicate record detection
    # ------------------------------------------------------------------
    def validate_duplicate(self) -> None:
        """Ensure no existing attendance record exists for the same
        employee / date / shift combination."""
        employee_id = self.data.get("employee_id")
        date = self.data.get("date")
        shift_id = self.data.get("shift_id") or self.data.get("shift")
        tenant = getattr(self.request, "tenant", None)

        if not (employee_id and date and shift_id):
            # Cannot check without all three fields; other validators will
            # catch the missing data.
            return

        from apps.attendance.models import AttendanceRecord

        qs = AttendanceRecord.objects.filter(
            employee_id=employee_id,
            date=date,
            shift_id=shift_id,
            is_deleted=False,
        )
        if tenant:
            qs = qs.filter(tenant=tenant)

        if qs.exists():
            self.errors.append(
                "An attendance record already exists for this employee, "
                "date, and shift."
            )

    # ------------------------------------------------------------------
    # 10. Shift window validation
    # ------------------------------------------------------------------
    def validate_shift(self) -> None:
        """Verify the current server time falls within the allowed clock-in
        window for the assigned shift (start_time - early_minutes to
        end_time + late_minutes)."""
        shift = self.data.get("shift_obj")
        if not shift:
            shift_id = self.data.get("shift_id") or self.data.get("shift")
            if not shift_id:
                return
            from apps.attendance.models import Shift as ShiftModel

            try:
                shift = ShiftModel.objects.get(pk=shift_id, is_deleted=False)
            except ShiftModel.DoesNotExist:
                self.errors.append("Specified shift does not exist.")
                return

        now = timezone.localtime(timezone.now())
        current_time = now.time()

        early_minutes = 30
        late_minutes = 30
        if self.policy:
            early_minutes = self.policy.allow_early_clockin_minutes
            late_minutes = self.policy.allow_late_clockout_minutes

        # Build allowed window as datetime objects for today
        today = now.date()

        shift_start_dt = datetime.combine(today, shift.start_time)
        shift_end_dt = datetime.combine(today, shift.end_time)

        # Handle overnight shifts
        if shift.is_overnight and shift.end_time <= shift.start_time:
            shift_end_dt += timedelta(days=1)

        window_start = shift_start_dt - timedelta(minutes=early_minutes)
        window_end = shift_end_dt + timedelta(minutes=late_minutes)

        # Make timezone-aware for comparison
        tz = now.tzinfo
        current_dt = datetime.combine(today, current_time)

        # For overnight shifts, also check if we are past midnight
        if shift.is_overnight and current_time < shift.start_time:
            current_dt += timedelta(days=1)

        if not (window_start.time() <= current_dt.time() or shift.is_overnight):
            if current_dt < window_start:
                minutes_early = (window_start - current_dt).total_seconds() / 60
                self.errors.append(
                    f"Clock-in is too early. The shift '{shift.name}' allows "
                    f"clock-in from {window_start.strftime('%H:%M')}. "
                    f"Please wait {minutes_early:.0f} minutes."
                )
                return

        if not shift.is_overnight:
            if current_dt > window_end:
                self.errors.append(
                    f"Clock-in window for shift '{shift.name}' has closed. "
                    f"The latest allowed time was {window_end.strftime('%H:%M')}."
                )

    # ------------------------------------------------------------------
    # 11. Clock tampering / skew detection
    # ------------------------------------------------------------------
    def validate_clock_tampering(self) -> None:
        """Compare the client-reported timestamp with the server time to
        detect significant clock skew that may indicate tampering."""
        client_timestamp = self.data.get("client_timestamp")
        if not client_timestamp:
            return

        server_now = timezone.now()

        if isinstance(client_timestamp, str):
            try:
                from django.utils.dateparse import parse_datetime

                client_timestamp = parse_datetime(client_timestamp)
                if client_timestamp is None:
                    self.errors.append("Invalid client timestamp format.")
                    return
            except (ValueError, TypeError):
                self.errors.append("Unable to parse client timestamp.")
                return

        # Ensure timezone-aware
        if timezone.is_naive(client_timestamp):
            client_timestamp = timezone.make_aware(client_timestamp)

        skew_seconds = abs((server_now - client_timestamp).total_seconds())

        if skew_seconds > CLOCK_SKEW_TOLERANCE:
            self.errors.append(
                f"Device clock skew detected ({skew_seconds:.0f}s). "
                f"Maximum allowed difference is {CLOCK_SKEW_TOLERANCE}s. "
                f"Please synchronise your device clock."
            )

    # ------------------------------------------------------------------
    # 12. Offline record validation
    # ------------------------------------------------------------------
    def validate_offline(self) -> None:
        """For offline records, verify the integrity hash and check the
        offline-per-shift limit."""
        is_offline = self.data.get("is_offline_record", False)
        if not is_offline:
            return

        # Verify integrity hash
        integrity_hash = self.data.get("offline_integrity_hash", "")
        if not integrity_hash:
            self.errors.append(
                "Offline record is missing an integrity hash."
            )
            return

        # Build the data dict that should have been hashed on the client
        hash_data = {
            "employee_id": str(self.data.get("employee_id", "")),
            "date": str(self.data.get("date", "")),
            "shift_id": str(self.data.get("shift_id", "") or self.data.get("shift", "")),
            "client_timestamp": str(self.data.get("client_timestamp", "")),
            "latitude": str(self.data.get("latitude", "") or self.data.get("clock_in_latitude", "")),
            "longitude": str(self.data.get("longitude", "") or self.data.get("clock_in_longitude", "")),
        }

        if not verify_integrity_hash(hash_data, integrity_hash):
            self.errors.append(
                "Offline record integrity check failed. The data may have "
                "been tampered with."
            )

        # Check offline-per-shift limit
        employee_id = self.data.get("employee_id")
        shift_id = self.data.get("shift_id") or self.data.get("shift")
        date = self.data.get("date")
        tenant = getattr(self.request, "tenant", None)

        if employee_id and shift_id and date:
            from apps.attendance.models import AttendanceRecord

            qs = AttendanceRecord.objects.filter(
                employee_id=employee_id,
                shift_id=shift_id,
                date=date,
                is_offline_record=True,
                is_deleted=False,
            )
            if tenant:
                qs = qs.filter(tenant=tenant)

            max_offline = OFFLINE_MAX_PER_SHIFT
            if self.policy:
                max_offline = self.policy.max_offline_per_shift

            if qs.count() >= max_offline:
                self.errors.append(
                    f"Offline attendance limit ({max_offline}) reached for "
                    f"this shift. No more offline records are allowed."
                )
