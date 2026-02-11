"""Tenant middleware for path-based multi-tenancy."""
import re

from django.http import JsonResponse

# Paths that do NOT require tenant context
TENANT_EXEMPT_PATHS = [
    r"^/admin/",
    r"^/api/v1/auth/",
    r"^/api/v1/tenants/",
    r"^/api/v1/integration/",
    r"^/api/schema",
    r"^/api/docs",
    r"^/api/redoc",
    r"^/static/",
    r"^/media/",
    r"^/ws/",
]

TENANT_URL_PATTERN = re.compile(r"^/api/v1/(?P<tenant_slug>[\w-]+)/")


class TenantMiddleware:
    """Extract tenant from URL path and attach to request."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_patterns = [re.compile(p) for p in TENANT_EXEMPT_PATHS]

    def __call__(self, request):
        request.tenant = None

        if any(p.match(request.path) for p in self.exempt_patterns):
            return self.get_response(request)

        match = TENANT_URL_PATTERN.match(request.path)
        if match:
            from apps.tenants.models import Tenant

            slug = match.group("tenant_slug")
            try:
                tenant = Tenant.objects.get(slug=slug, is_active=True, is_deleted=False)
                request.tenant = tenant
            except Tenant.DoesNotExist:
                return JsonResponse(
                    {"detail": f"Tenant '{slug}' not found or inactive."},
                    status=404,
                )

        return self.get_response(request)
