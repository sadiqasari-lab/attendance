"""DRF ViewSets for the tenants app."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.mixins import AuditLogMixin, TenantQuerySetMixin
from apps.core.models import AuditLog
from apps.core.pagination import StandardPagination
from apps.core.permissions import IsSuperAdmin, IsTenantAdmin
from apps.core.utils import get_client_ip

from apps.tenants.models import Department, Group, Tenant
from apps.tenants.serializers import (
    DepartmentSerializer,
    GroupSerializer,
    TenantSerializer,
)


# ---------------------------------------------------------------------------
# Group ViewSet — SuperAdmin only
# ---------------------------------------------------------------------------
class GroupViewSet(AuditLogMixin, viewsets.ModelViewSet):
    """CRUD for corporate groups. Restricted to SuperAdmin users."""

    queryset = Group.objects.filter(is_deleted=False)
    serializer_class = GroupSerializer
    permission_classes = [IsSuperAdmin]
    pagination_class = StandardPagination
    lookup_field = "pk"

    def get_queryset(self):
        qs = super().get_queryset()
        # Optional filter by active status
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        return qs


# ---------------------------------------------------------------------------
# Tenant ViewSet — SuperAdmin full CRUD, TenantAdmin read own
# ---------------------------------------------------------------------------
class TenantViewSet(AuditLogMixin, viewsets.ModelViewSet):
    """CRUD for tenants (branches / child companies).

    * **SuperAdmin** -- full CRUD across all tenants.
    * **TenantAdmin** -- read-only access to their own tenant.
    """

    queryset = Tenant.objects.filter(is_deleted=False)
    serializer_class = TenantSerializer
    permission_classes = [IsSuperAdmin | IsTenantAdmin]
    pagination_class = StandardPagination
    lookup_field = "pk"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # TenantAdmins may only see their own tenant
        if user.role != "SUPER_ADMIN":
            tenant = getattr(self.request, "tenant", None)
            if tenant:
                qs = qs.filter(pk=tenant.pk)

        # Optional filters
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")

        group_id = self.request.query_params.get("group")
        if group_id:
            qs = qs.filter(group_id=group_id)

        return qs

    def check_permissions(self, request):
        """
        Allow TenantAdmin read access but restrict writes to SuperAdmin.
        """
        super().check_permissions(request)
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            if not IsSuperAdmin().has_permission(request, self):
                self.permission_denied(request)

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        """Return lightweight statistics for a single tenant."""
        tenant = self.get_object()
        data = {
            "id": str(tenant.pk),
            "name": tenant.name,
            "department_count": Department.objects.filter(
                tenant=tenant, is_deleted=False
            ).count(),
        }
        return Response(data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Department ViewSet — tenant-scoped
# ---------------------------------------------------------------------------
class DepartmentViewSet(
    TenantQuerySetMixin, AuditLogMixin, viewsets.ModelViewSet
):
    """CRUD for departments within the current tenant.

    Uses TenantQuerySetMixin to automatically scope querysets to the
    request's tenant.  The tenant can be resolved from:
      1. ``request.tenant`` (set by TenantMiddleware for path-based URLs)
      2. ``tenant_slug`` query-parameter or request-body field (for the
         tenant-exempt ``/api/v1/tenants/departments/`` endpoint)
    """

    queryset = Department.objects.filter(is_deleted=False)
    serializer_class = DepartmentSerializer
    permission_classes = [IsTenantAdmin]
    pagination_class = StandardPagination
    lookup_field = "pk"

    def _resolve_tenant(self):
        """Return the Tenant from the request or from tenant_slug."""
        tenant = getattr(self.request, "tenant", None)
        if tenant:
            return tenant
        # Fall back to tenant_slug from query params or body
        slug = (
            self.request.query_params.get("tenant_slug")
            or self.request.data.get("tenant_slug")
        )
        if slug:
            try:
                return Tenant.objects.get(slug=slug, is_deleted=False)
            except Tenant.DoesNotExist:
                return None
        return None

    def get_queryset(self):
        qs = super().get_queryset()

        # Scope to tenant (supports both middleware-set and slug-resolved)
        tenant = self._resolve_tenant()
        if tenant:
            qs = qs.filter(tenant=tenant)

        # Optional filters
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")

        parent = self.request.query_params.get("parent")
        if parent == "root":
            qs = qs.filter(parent__isnull=True)
        elif parent:
            qs = qs.filter(parent_id=parent)

        return qs

    def perform_create(self, serializer):
        """Attach the resolved tenant automatically on creation."""
        tenant = self._resolve_tenant()
        if not tenant:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                {"tenant_slug": "A valid tenant_slug is required to create a department."}
            )
        instance = serializer.save(
            tenant=tenant,
            created_by=self.request.user,
        )
        # Audit log
        AuditLog.objects.create(
            tenant=tenant,
            user=self.request.user if self.request.user.is_authenticated else None,
            action="CREATE",
            resource_type="Department",
            resource_id=instance.pk,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get("HTTP_USER_AGENT", ""),
        )
        return instance
