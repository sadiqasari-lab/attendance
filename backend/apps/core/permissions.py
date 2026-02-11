"""RBAC permission classes for the Inspire Attendance System."""
from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """Full system access across all tenants."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "SUPER_ADMIN"
        )


class IsTenantAdmin(BasePermission):
    """Administrative access within a specific tenant."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role == "SUPER_ADMIN":
            return True
        if request.user.role != "TENANT_ADMIN":
            return False
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return True
        return request.user.employee_profiles.filter(
            tenant=tenant, is_deleted=False
        ).exists()


class IsManager(BasePermission):
    """Manager access within a tenant."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role in ("SUPER_ADMIN", "TENANT_ADMIN"):
            return True
        if request.user.role != "MANAGER":
            return False
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return True
        return request.user.employee_profiles.filter(
            tenant=tenant, is_deleted=False
        ).exists()


class IsEmployee(BasePermission):
    """Authenticated employee access within a tenant."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role in ("SUPER_ADMIN", "TENANT_ADMIN", "MANAGER"):
            return True
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return True
        return request.user.employee_profiles.filter(
            tenant=tenant, is_deleted=False
        ).exists()


class IsTenantMember(BasePermission):
    """Check that the user belongs to the tenant in the URL."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role == "SUPER_ADMIN":
            return True
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return False
        return request.user.employee_profiles.filter(
            tenant=tenant, is_deleted=False
        ).exists()


class IsOwnerOrAdmin(BasePermission):
    """Object-level: owner or admin can access."""

    def has_object_permission(self, request, view, obj):
        if request.user.role in ("SUPER_ADMIN", "TENANT_ADMIN"):
            return True
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "employee") and hasattr(obj.employee, "user"):
            return obj.employee.user == request.user
        if hasattr(obj, "created_by"):
            return obj.created_by == request.user
        return False


class ReadOnly(BasePermission):
    """Allow read-only access."""

    def has_permission(self, request, view):
        return request.method in ("GET", "HEAD", "OPTIONS")
