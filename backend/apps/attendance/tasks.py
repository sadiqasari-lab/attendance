"""Celery tasks for the attendance app."""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_attendance_notification(self, record_id, event_type):
    """Send WebSocket broadcast for attendance event."""
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        from .models import AttendanceRecord

        record = AttendanceRecord.objects.select_related(
            "employee", "tenant", "shift"
        ).get(id=record_id)

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
                    "latitude": str(record.clock_in_latitude) if record.clock_in_latitude else None,
                    "longitude": str(record.clock_in_longitude) if record.clock_in_longitude else None,
                    "timestamp": record.clock_in_time.isoformat() if record.clock_in_time else None,
                    "status": record.status,
                },
            },
        )
    except Exception as exc:
        logger.exception("Failed to send attendance notification")
        raise self.retry(exc=exc, countdown=5)


@shared_task
def generate_daily_attendance_report():
    """Generate daily attendance summary for all tenants."""
    from apps.tenants.models import Tenant
    from .models import AttendanceRecord

    today = timezone.localdate()
    tenants = Tenant.objects.filter(is_active=True, is_deleted=False)

    for tenant in tenants:
        records = AttendanceRecord.objects.filter(
            tenant=tenant, date=today, is_deleted=False
        )
        total = records.count()
        present = records.filter(status="PRESENT").count()
        late = records.filter(status="LATE").count()
        absent = records.filter(status="ABSENT").count()

        logger.info(
            "Daily report for %s on %s: total=%d present=%d late=%d absent=%d",
            tenant.name, today, total, present, late, absent,
        )


@shared_task
def cleanup_old_selfie_images(retention_days=90):
    """Remove selfie images older than retention period."""
    from .models import AttendanceRecord

    cutoff = timezone.now() - timedelta(days=retention_days)
    old_records = AttendanceRecord.objects.filter(
        created_at__lt=cutoff,
        is_deleted=False,
    ).exclude(clock_in_selfie="").exclude(clock_in_selfie__isnull=True)

    count = 0
    for record in old_records.iterator():
        if record.clock_in_selfie:
            record.clock_in_selfie.delete(save=False)
        if record.clock_out_selfie:
            record.clock_out_selfie.delete(save=False)
        record.clock_in_selfie = None
        record.clock_out_selfie = None
        record.save(update_fields=["clock_in_selfie", "clock_out_selfie", "updated_at"])
        count += 1

    logger.info("Cleaned up selfie images for %d records older than %d days", count, retention_days)
