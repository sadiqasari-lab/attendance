"""View mixins for tenant isolation and audit logging."""
from apps.core.models import AuditLog
from apps.core.utils import get_client_ip


class TenantQuerySetMixin:
    """Filter querysets by the tenant in the request."""

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = getattr(self.request, "tenant", None)
        if tenant and hasattr(qs.model, "tenant"):
            qs = qs.filter(tenant=tenant)
        return qs.filter(is_deleted=False)


class AuditLogMixin:
    """Log create/update/delete actions to AuditLog."""

    audit_action = None

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        self._log_audit("CREATE", instance)
        return instance

    def perform_update(self, serializer):
        instance = serializer.save()
        self._log_audit("UPDATE", instance)
        return instance

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user)
        self._log_audit("DELETE", instance)

    def _log_audit(self, action, instance):
        AuditLog.objects.create(
            tenant=getattr(self.request, "tenant", None),
            user=self.request.user if self.request.user.is_authenticated else None,
            action=self.audit_action or action,
            resource_type=instance.__class__.__name__,
            resource_id=instance.pk,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get("HTTP_USER_AGENT", ""),
        )
