"""Celery tasks for HRIS webhook delivery."""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def deliver_webhook_task(self, tenant_id, event_type, payload_data):
    """Asynchronous webhook delivery via Celery."""
    try:
        from apps.tenants.models import Tenant

        from .webhooks import deliver_webhook

        tenant = Tenant.objects.get(id=tenant_id)
        deliver_webhook(tenant, event_type, payload_data)
    except Exception as exc:
        logger.exception("Webhook delivery task failed for tenant %s", tenant_id)
        raise self.retry(exc=exc, countdown=30)


@shared_task
def deliver_daily_summary_webhooks():
    """Deliver daily attendance summary to all configured webhooks."""
    from django.utils import timezone

    from apps.attendance.models import AttendanceRecord
    from apps.tenants.models import Tenant

    from .webhooks import deliver_webhook

    today = timezone.localdate()
    tenants = Tenant.objects.filter(is_active=True, is_deleted=False)

    for tenant in tenants:
        records = AttendanceRecord.objects.filter(
            tenant=tenant, date=today, is_deleted=False
        )
        summary = {
            "date": str(today),
            "tenant": tenant.name,
            "total_records": records.count(),
            "present": records.filter(status="PRESENT").count(),
            "late": records.filter(status="LATE").count(),
            "absent": records.filter(status="ABSENT").count(),
        }
        deliver_webhook(tenant, "DAILY_SUMMARY", summary)
