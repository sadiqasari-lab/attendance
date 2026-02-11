"""ViewSets for the projects app."""
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.core.mixins import AuditLogMixin, TenantQuerySetMixin
from apps.core.permissions import IsEmployee, IsTenantAdmin

from .models import EmployeeProjectAssignment, Project
from .serializers import (
    EmployeeProjectAssignmentSerializer,
    ProjectSerializer,
)


class ProjectViewSet(TenantQuerySetMixin, AuditLogMixin, ModelViewSet):
    """
    CRUD operations for projects within the current tenant.

    Permissions
    -----------
    - **Read** (list / retrieve): any authenticated employee in the tenant.
    - **Write** (create / update / delete): tenant administrators only.

    The queryset is automatically scoped to the tenant attached to the
    incoming request via ``TenantQuerySetMixin``.
    """

    serializer_class = ProjectSerializer
    lookup_field = "pk"

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("geofence", "created_by")
            .annotate(
                assignment_count_annotation=Count(
                    "assignments",
                    filter=Q(
                        assignments__is_active=True,
                        assignments__is_deleted=False,
                    ),
                )
            )
        )

        # Optional query-parameter filters
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ("true", "1"))

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(name_ar__icontains=search)
                | Q(location_name__icontains=search)
            )

        return qs

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated(), IsEmployee()]
        return [IsAuthenticated(), IsTenantAdmin()]

    def perform_create(self, serializer):
        """Assign the current tenant and user, then save."""
        instance = serializer.save(
            tenant=self.request.tenant,
            created_by=self.request.user,
        )
        self._log_audit("CREATE", instance)
        return instance

    class Meta:
        model = Project


class EmployeeProjectAssignmentViewSet(
    TenantQuerySetMixin, AuditLogMixin, ModelViewSet
):
    """
    CRUD operations for employee-project assignments within the tenant.

    Permissions
    -----------
    - **Read**: any authenticated employee in the tenant.
    - **Write**: tenant administrators only.
    """

    serializer_class = EmployeeProjectAssignmentSerializer
    lookup_field = "pk"

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related(
                "employee",
                "employee__user",
                "project",
                "created_by",
            )
        )

        # Optional query-parameter filters
        project_id = self.request.query_params.get("project")
        if project_id:
            qs = qs.filter(project_id=project_id)

        employee_id = self.request.query_params.get("employee")
        if employee_id:
            qs = qs.filter(employee_id=employee_id)

        role = self.request.query_params.get("role")
        if role:
            qs = qs.filter(role=role)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ("true", "1"))

        return qs

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated(), IsEmployee()]
        return [IsAuthenticated(), IsTenantAdmin()]

    def perform_create(self, serializer):
        """Assign the current tenant and user, then save."""
        instance = serializer.save(
            tenant=self.request.tenant,
            created_by=self.request.user,
        )
        self._log_audit("CREATE", instance)
        return instance

    class Meta:
        model = EmployeeProjectAssignment
