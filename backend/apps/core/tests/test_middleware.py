"""Tests for the tenant middleware."""
import pytest
from django.test import RequestFactory

from apps.core.middleware import TenantMiddleware


class TestTenantMiddleware:
    @pytest.fixture
    def middleware(self):
        return TenantMiddleware(lambda req: req)

    @pytest.fixture
    def rf(self):
        return RequestFactory()

    @pytest.mark.django_db
    def test_exempt_paths_skip_tenant(self, middleware, rf):
        request = rf.get("/admin/")
        result = middleware(request)
        assert result.tenant is None

    @pytest.mark.django_db
    def test_auth_path_exempt(self, middleware, rf):
        request = rf.get("/api/v1/auth/login/")
        result = middleware(request)
        assert result.tenant is None

    @pytest.mark.django_db
    def test_valid_tenant_slug(self, middleware, rf, tenant):
        request = rf.get(f"/api/v1/{tenant.slug}/attendance/records/")
        result = middleware(request)
        assert result.tenant == tenant

    @pytest.mark.django_db
    def test_invalid_tenant_slug_returns_404(self, middleware, rf):
        from django.http import JsonResponse
        request = rf.get("/api/v1/nonexistent/attendance/records/")
        result = middleware(request)
        assert isinstance(result, JsonResponse)
        assert result.status_code == 404

    @pytest.mark.django_db
    def test_inactive_tenant_returns_404(self, middleware, rf, tenant):
        tenant.is_active = False
        tenant.save()
        from django.http import JsonResponse
        request = rf.get(f"/api/v1/{tenant.slug}/attendance/records/")
        result = middleware(request)
        assert isinstance(result, JsonResponse)
        assert result.status_code == 404
