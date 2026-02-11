"""Tests for the HRIS integration app."""
import pytest

from apps.integration.models import IntegrationToken, IntegrationWebhookLog, WebhookConfig


class TestIntegrationTokenModel:
    @pytest.mark.django_db
    def test_token_auto_generation(self, tenant):
        token = IntegrationToken.objects.create(
            tenant=tenant,
            name="Test HRIS Token",
        )
        assert token.token != ""
        assert len(token.token) > 30

    @pytest.mark.django_db
    def test_token_str(self, tenant):
        token = IntegrationToken.objects.create(
            tenant=tenant,
            name="HRIS Token",
            is_active=True,
        )
        assert "HRIS Token" in str(token)
        assert "active" in str(token)


class TestWebhookConfigModel:
    @pytest.mark.django_db
    def test_webhook_creation(self, tenant):
        webhook = WebhookConfig.objects.create(
            tenant=tenant,
            name="HRIS Webhook",
            url="https://hris.example.com/webhook",
            events=["CLOCK_IN", "CLOCK_OUT"],
            is_active=True,
        )
        assert webhook.events == ["CLOCK_IN", "CLOCK_OUT"]
        assert webhook.max_retries == 3


class TestIntegrationPullAPI:
    @pytest.mark.django_db
    def test_pull_without_token_fails(self, api_client):
        response = api_client.get("/api/v1/integration/pull/attendance-logs/")
        assert response.status_code in (401, 403)

    @pytest.mark.django_db
    def test_pull_with_valid_token(self, api_client, tenant, attendance_record):
        token = IntegrationToken.objects.create(
            tenant=tenant,
            name="Test Token",
            is_active=True,
        )
        response = api_client.get(
            "/api/v1/integration/pull/attendance-logs/",
            HTTP_AUTHORIZATION=f"Token {token.token}",
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.django_db
    def test_pull_shifts(self, api_client, tenant, shift):
        token = IntegrationToken.objects.create(
            tenant=tenant,
            name="Shift Token",
            is_active=True,
        )
        response = api_client.get(
            "/api/v1/integration/pull/shifts/",
            HTTP_AUTHORIZATION=f"Token {token.token}",
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) > 0
        assert data[0]["name"] == "Morning Shift"

    @pytest.mark.django_db
    def test_pull_summary(self, api_client, tenant, attendance_record):
        token = IntegrationToken.objects.create(
            tenant=tenant,
            name="Summary Token",
            is_active=True,
        )
        response = api_client.get(
            "/api/v1/integration/pull/summary/",
            HTTP_AUTHORIZATION=f"Token {token.token}",
        )
        assert response.status_code == 200
        assert "total_records" in response.json()["data"]

    @pytest.mark.django_db
    def test_expired_token_rejected(self, api_client, tenant):
        from django.utils import timezone
        from datetime import timedelta

        token = IntegrationToken.objects.create(
            tenant=tenant,
            name="Expired Token",
            is_active=True,
            expires_at=timezone.now() - timedelta(days=1),
        )
        response = api_client.get(
            "/api/v1/integration/pull/attendance-logs/",
            HTTP_AUTHORIZATION=f"Token {token.token}",
        )
        assert response.status_code in (401, 403)

    @pytest.mark.django_db
    def test_inactive_token_rejected(self, api_client, tenant):
        token = IntegrationToken.objects.create(
            tenant=tenant,
            name="Inactive Token",
            is_active=False,
        )
        response = api_client.get(
            "/api/v1/integration/pull/attendance-logs/",
            HTTP_AUTHORIZATION=f"Token {token.token}",
        )
        assert response.status_code in (401, 403)


class TestIntegrationAdminAPI:
    @pytest.mark.django_db
    def test_list_tokens_requires_auth(self, api_client):
        response = api_client.get("/api/v1/integration/tokens/")
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_list_webhooks_as_admin(self, admin_client, tenant):
        WebhookConfig.objects.create(
            tenant=tenant,
            name="Test Hook",
            url="https://example.com/hook",
            events=["CLOCK_IN"],
        )
        response = admin_client.get("/api/v1/integration/webhooks/")
        assert response.status_code == 200
