"""Webhook delivery service for pushing attendance events to external HRIS."""
import hashlib
import hmac
import json
import logging

import requests
from django.utils import timezone

from .models import IntegrationWebhookLog, WebhookConfig

logger = logging.getLogger(__name__)


def deliver_webhook(tenant, event_type, payload_data):
    """
    Deliver a webhook event to all active configs for the tenant matching the event type.

    Args:
        tenant: Tenant instance
        event_type: string matching WebhookConfig.Event choices
        payload_data: dict of event data
    """
    webhooks = WebhookConfig.objects.filter(
        tenant=tenant,
        is_active=True,
        is_deleted=False,
    )

    for webhook in webhooks:
        if event_type not in webhook.events:
            continue

        log = IntegrationWebhookLog.objects.create(
            webhook=webhook,
            tenant=tenant,
            event_type=event_type,
            payload=payload_data,
            status=IntegrationWebhookLog.Status.PENDING,
        )

        _attempt_delivery(webhook, log, payload_data)


def _attempt_delivery(webhook, log, payload_data):
    """Attempt to deliver a webhook with retry logic."""
    payload_json = json.dumps(payload_data, default=str)
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Event": log.event_type,
        "X-Webhook-Delivery-Id": str(log.id),
    }

    # Add custom headers
    if webhook.headers:
        headers.update(webhook.headers)

    # Add HMAC signature if secret is configured
    if webhook.secret:
        signature = hmac.new(
            webhook.secret.encode(),
            payload_json.encode(),
            hashlib.sha256,
        ).hexdigest()
        headers["X-Webhook-Signature"] = f"sha256={signature}"

    for attempt in range(webhook.max_retries + 1):
        log.attempt_count = attempt + 1
        try:
            response = requests.post(
                webhook.url,
                data=payload_json,
                headers=headers,
                timeout=webhook.timeout_seconds,
            )
            log.response_status_code = response.status_code
            log.response_body = response.text[:2000]

            if 200 <= response.status_code < 300:
                log.status = IntegrationWebhookLog.Status.DELIVERED
                log.delivered_at = timezone.now()
                log.save()
                return

            log.error_message = f"HTTP {response.status_code}"
            log.status = IntegrationWebhookLog.Status.RETRYING
            log.save()

        except requests.exceptions.Timeout:
            log.error_message = "Request timed out"
            log.status = IntegrationWebhookLog.Status.RETRYING
            log.save()
        except requests.exceptions.RequestException as exc:
            log.error_message = str(exc)[:500]
            log.status = IntegrationWebhookLog.Status.RETRYING
            log.save()

    # All retries exhausted
    log.status = IntegrationWebhookLog.Status.FAILED
    log.save()
    logger.warning(
        "Webhook delivery failed after %d attempts: %s -> %s",
        log.attempt_count, webhook.name, webhook.url,
    )
