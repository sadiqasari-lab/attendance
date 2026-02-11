"""Attendance service layer — clock-in, clock-out, offline sync, status calculation."""
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone

from apps.core.exceptions import AttendanceValidationError, OfflineLimitExceeded
from apps.core.models import AuditLog
from apps.core.utils import get_client_ip

from .models import AttendanceRecord, Shift
from .validators import AttendanceValidator

logger = logging.getLogger(__name__)


class AttendanceService:
    """Service for handling attendance clock-in/out operations."""

    @staticmethod
    def clock_in(employee, data, request):
        """
        Process a clock-in request.
        Runs the full validation engine, creates the record, and broadcasts.
        """
        tenant = request.tenant
        shift = Shift.objects.get(id=data["shift_id"], tenant=tenant, is_deleted=False)
        today = timezone.localdate()

        # Build validation context
        validation_data = {
            "tenant": tenant,
            "employee": employee,
            "shift": shift,
            "date": today,
            "selfie": data.get("selfie"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "gps_accuracy": data.get("gps_accuracy"),
            "device_id": data.get("device_id"),
            "wifi_ssid": data.get("wifi_ssid", ""),
            "wifi_bssid": data.get("wifi_bssid", ""),
            "client_timestamp": data.get("client_timestamp"),
            "liveness_passed": data.get("liveness_passed", False),
            "face_match_score": data.get("face_match_score"),
            "is_mock_location": data.get("is_mock_location", False),
            "geofence_id": data.get("geofence_id"),
            "is_offline": False,
        }

        validator = AttendanceValidator(validation_data, request)
        is_valid, errors = validator.validate_all()

        # Calculate status
        status = AttendanceService._calculate_clock_in_status(shift, timezone.now())

        record = AttendanceRecord.objects.create(
            tenant=tenant,
            employee=employee,
            shift=shift,
            policy=validator.policy,
            date=today,
            clock_in_time=timezone.now(),
            status=status,
            clock_in_latitude=data.get("latitude"),
            clock_in_longitude=data.get("longitude"),
            clock_in_selfie=data.get("selfie"),
            clock_in_device_id=data.get("device_id"),
            clock_in_wifi_ssid=data.get("wifi_ssid", ""),
            clock_in_wifi_bssid=data.get("wifi_bssid", ""),
            is_offline_record=False,
            is_validated=is_valid,
            validation_errors=errors,
            is_synced=True,
            liveness_passed=data.get("liveness_passed", False),
            face_match_score=data.get("face_match_score"),
            gps_accuracy=data.get("gps_accuracy"),
            geofence_id=data.get("geofence_id"),
            geofence_valid=validator.geofence_valid,
            wifi_valid=validator.wifi_valid,
            device_valid=validator.device_valid,
            clock_skew_detected=validator.clock_skew_detected,
            client_timestamp=data.get("client_timestamp"),
            notes=data.get("notes", ""),
            created_by=request.user,
        )

        if not is_valid:
            raise AttendanceValidationError(
                detail={"message": "Attendance validation failed.", "errors": errors}
            )

        # Audit log
        AuditLog.objects.create(
            tenant=tenant,
            user=request.user,
            action="CLOCK_IN",
            resource_type="AttendanceRecord",
            resource_id=record.pk,
            details={"shift": str(shift.name), "date": str(today)},
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        # Broadcast (non-blocking)
        AttendanceService._broadcast_attendance_event(record, "clock_in")

        return record

    @staticmethod
    def clock_out(employee, record_id, data, request):
        """Process a clock-out for an existing attendance record."""
        tenant = request.tenant

        try:
            record = AttendanceRecord.objects.get(
                id=record_id,
                tenant=tenant,
                employee=employee,
                is_deleted=False,
                clock_out_time__isnull=True,
            )
        except AttendanceRecord.DoesNotExist:
            raise AttendanceValidationError(
                detail="No open attendance record found for clock-out."
            )

        now = timezone.now()
        record.clock_out_time = now
        record.clock_out_latitude = data.get("latitude")
        record.clock_out_longitude = data.get("longitude")
        record.clock_out_selfie = data.get("selfie")
        record.client_timestamp = data.get("client_timestamp")
        record.notes = data.get("notes", record.notes)

        # Recalculate status with clock-out time
        record.status = AttendanceService._calculate_final_status(
            record.shift, record.clock_in_time, now
        )
        record.save()

        AuditLog.objects.create(
            tenant=tenant,
            user=request.user,
            action="CLOCK_OUT",
            resource_type="AttendanceRecord",
            resource_id=record.pk,
            details={
                "shift": str(record.shift.name),
                "date": str(record.date),
                "duration_hours": record.duration_hours,
            },
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        AttendanceService._broadcast_attendance_event(record, "clock_out")
        return record

    @staticmethod
    def sync_offline_record(employee, data, request):
        """Validate and sync an offline attendance record."""
        tenant = request.tenant
        shift = Shift.objects.get(id=data["shift_id"], tenant=tenant, is_deleted=False)

        # Check offline limit
        offline_count = AttendanceRecord.objects.filter(
            tenant=tenant,
            employee=employee,
            shift=shift,
            date=data["date"],
            is_offline_record=True,
            is_deleted=False,
        ).count()

        max_offline = getattr(settings, "ATTENDANCE_OFFLINE_MAX_PER_SHIFT", 1)
        if offline_count >= max_offline:
            raise OfflineLimitExceeded()

        # Build validation context
        validation_data = {
            "tenant": tenant,
            "employee": employee,
            "shift": shift,
            "date": data["date"],
            "selfie": data.get("selfie"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "gps_accuracy": data.get("gps_accuracy"),
            "device_id": data.get("device_id"),
            "wifi_ssid": data.get("wifi_ssid", ""),
            "wifi_bssid": data.get("wifi_bssid", ""),
            "client_timestamp": data.get("client_timestamp"),
            "liveness_passed": data.get("liveness_passed", False),
            "face_match_score": data.get("face_match_score"),
            "is_mock_location": data.get("is_mock_location", False),
            "geofence_id": data.get("geofence_id"),
            "is_offline": True,
            "integrity_hash": data.get("integrity_hash"),
        }

        validator = AttendanceValidator(validation_data, request)
        is_valid, errors = validator.validate_all()

        status = AttendanceService._calculate_clock_in_status(
            shift, data["clock_in_time"]
        )

        record = AttendanceRecord.objects.create(
            tenant=tenant,
            employee=employee,
            shift=shift,
            policy=validator.policy,
            date=data["date"],
            clock_in_time=data["clock_in_time"],
            status=status,
            clock_in_latitude=data.get("latitude"),
            clock_in_longitude=data.get("longitude"),
            clock_in_selfie=data.get("selfie"),
            clock_in_device_id=data.get("device_id"),
            clock_in_wifi_ssid=data.get("wifi_ssid", ""),
            clock_in_wifi_bssid=data.get("wifi_bssid", ""),
            is_offline_record=True,
            offline_integrity_hash=data.get("integrity_hash", ""),
            is_validated=is_valid,
            validation_errors=errors,
            is_synced=True,
            liveness_passed=data.get("liveness_passed", False),
            face_match_score=data.get("face_match_score"),
            gps_accuracy=data.get("gps_accuracy"),
            geofence_id=data.get("geofence_id"),
            geofence_valid=validator.geofence_valid,
            wifi_valid=validator.wifi_valid,
            device_valid=validator.device_valid,
            clock_skew_detected=validator.clock_skew_detected,
            client_timestamp=data.get("client_timestamp"),
            notes=data.get("notes", ""),
            created_by=request.user,
        )

        if not is_valid:
            raise AttendanceValidationError(
                detail={
                    "message": "Offline record failed server revalidation.",
                    "errors": errors,
                }
            )

        AuditLog.objects.create(
            tenant=tenant,
            user=request.user,
            action="CLOCK_IN",
            resource_type="AttendanceRecord",
            resource_id=record.pk,
            details={
                "shift": str(shift.name),
                "date": str(data["date"]),
                "offline_sync": True,
            },
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return record

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _calculate_clock_in_status(shift, clock_in_time):
        """Determine status based on clock-in time relative to shift start."""
        if isinstance(clock_in_time, datetime):
            clock_in = clock_in_time.time()
        else:
            clock_in = clock_in_time

        shift_start = shift.start_time
        grace_end = (
            datetime.combine(datetime.today(), shift_start)
            + timedelta(minutes=shift.grace_period_minutes)
        ).time()

        if clock_in <= grace_end:
            return AttendanceRecord.Status.PRESENT
        return AttendanceRecord.Status.LATE

    @staticmethod
    def _calculate_final_status(shift, clock_in_time, clock_out_time):
        """Determine final status considering both clock-in and clock-out."""
        clock_in = clock_in_time.time() if isinstance(clock_in_time, datetime) else clock_in_time
        clock_out = clock_out_time.time() if isinstance(clock_out_time, datetime) else clock_out_time

        shift_start = shift.start_time
        shift_end = shift.end_time
        grace_end = (
            datetime.combine(datetime.today(), shift_start)
            + timedelta(minutes=shift.grace_period_minutes)
        ).time()

        is_late = clock_in > grace_end
        is_early_departure = clock_out < shift_end and not shift.is_overnight

        if is_late and is_early_departure:
            return AttendanceRecord.Status.HALF_DAY
        if is_late:
            return AttendanceRecord.Status.LATE
        if is_early_departure:
            return AttendanceRecord.Status.EARLY_DEPARTURE
        return AttendanceRecord.Status.PRESENT

    @staticmethod
    def _broadcast_attendance_event(record, event_type):
        """Send attendance event to WebSocket group."""
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            group_name = f"attendance_map_{record.tenant.slug}"
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "attendance_event",
                    "data": {
                        "event": event_type,
                        "employee_id": str(record.employee.id),
                        "employee_name": str(record.employee),
                        "latitude": str(record.clock_in_latitude),
                        "longitude": str(record.clock_in_longitude),
                        "timestamp": record.clock_in_time.isoformat()
                        if record.clock_in_time
                        else None,
                        "status": record.status,
                    },
                },
            )
        except Exception:
            logger.exception("Failed to broadcast attendance event")
