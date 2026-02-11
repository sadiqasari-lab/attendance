"""ViewSets for the approvals app."""
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.core.mixins import AuditLogMixin, TenantQuerySetMixin
from apps.core.models import AuditLog
from apps.core.permissions import IsEmployee, IsManager, IsTenantAdmin
from apps.core.utils import get_client_ip

from .models import ApprovalRequest
from .serializers import (
    ApprovalActionSerializer,
    ApprovalRequestCreateSerializer,
    ApprovalRequestSerializer,
)


class ApprovalRequestViewSet(TenantQuerySetMixin, AuditLogMixin, ModelViewSet):
    """
    CRUD plus workflow actions for approval requests.

    Endpoints
    ---------
    - **list / retrieve** : any authenticated employee (filtered by tenant).
    - **create** : any authenticated employee.
    - **update / partial_update / destroy** : tenant admins only.
    - **approve** (POST detail): tenant admin or manager.
    - **reject** (POST detail): tenant admin or manager.
    - **cancel** (POST detail): request owner only.
    - **pending_count** (GET list): count of pending requests for the
      current tenant (admin/manager) or for the current user (employee).
    """

    lookup_field = "pk"

    # ------------------------------------------------------------------
    # Queryset
    # ------------------------------------------------------------------
    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related(
                "requester",
                "requester__user",
                "reviewed_by",
                "created_by",
            )
        )

        # Optional query-parameter filters
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        request_type = self.request.query_params.get("request_type")
        if request_type:
            qs = qs.filter(request_type=request_type)

        requester_id = self.request.query_params.get("requester")
        if requester_id:
            qs = qs.filter(requester_id=requester_id)

        priority = self.request.query_params.get("priority")
        if priority:
            qs = qs.filter(priority=priority)

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        return qs

    # ------------------------------------------------------------------
    # Serializer selection
    # ------------------------------------------------------------------
    def get_serializer_class(self):
        if self.action == "create":
            return ApprovalRequestCreateSerializer
        if self.action in ("approve", "reject"):
            return ApprovalActionSerializer
        return ApprovalRequestSerializer

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------
    def get_permissions(self):
        if self.action in ("list", "retrieve", "create", "pending_count"):
            return [IsAuthenticated(), IsEmployee()]
        if self.action in ("approve", "reject"):
            return [IsAuthenticated(), IsManager()]
        if self.action == "cancel":
            # Object-level check is done inside the action itself.
            return [IsAuthenticated(), IsEmployee()]
        # update / partial_update / destroy
        return [IsAuthenticated(), IsTenantAdmin()]

    # ------------------------------------------------------------------
    # Create override
    # ------------------------------------------------------------------
    def perform_create(self, serializer):
        """
        Set tenant, requester (employee profile for the current user
        within the current tenant), and created_by automatically.
        """
        tenant = self.request.tenant
        employee = self.request.user.employee_profiles.filter(
            tenant=tenant, is_deleted=False
        ).first()

        if not employee:
            raise serializers.ValidationError(
                "You do not have an employee profile in this tenant."
            )

        instance = serializer.save(
            tenant=tenant,
            requester=employee,
            created_by=self.request.user,
        )
        self._log_audit("CREATE", instance)
        return instance

    # ------------------------------------------------------------------
    # Custom actions
    # ------------------------------------------------------------------
    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        """Approve a pending approval request."""
        instance = self.get_object()

        if instance.status != ApprovalRequest.Status.PENDING:
            return Response(
                {"detail": f"Cannot approve a request with status '{instance.get_status_display()}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        instance.status = ApprovalRequest.Status.APPROVED
        instance.reviewed_by = request.user
        instance.reviewed_at = timezone.now()
        instance.review_notes = serializer.validated_data.get("review_notes", "")
        instance.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "review_notes",
                "updated_at",
            ]
        )

        self._log_approval_audit("APPROVAL", instance)

        return Response(
            ApprovalRequestSerializer(instance).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        """Reject a pending approval request."""
        instance = self.get_object()

        if instance.status != ApprovalRequest.Status.PENDING:
            return Response(
                {"detail": f"Cannot reject a request with status '{instance.get_status_display()}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        instance.status = ApprovalRequest.Status.REJECTED
        instance.reviewed_by = request.user
        instance.reviewed_at = timezone.now()
        instance.review_notes = serializer.validated_data.get("review_notes", "")
        instance.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "review_notes",
                "updated_at",
            ]
        )

        self._log_approval_audit("REJECTION", instance)

        return Response(
            ApprovalRequestSerializer(instance).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        """
        Cancel a pending approval request.

        Only the original requester (owner) may cancel their own request.
        """
        instance = self.get_object()

        # Ownership check: the requesting user must own this approval.
        employee = request.user.employee_profiles.filter(
            tenant=request.tenant, is_deleted=False
        ).first()

        if not employee or instance.requester_id != employee.pk:
            return Response(
                {"detail": "You can only cancel your own requests."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if instance.status != ApprovalRequest.Status.PENDING:
            return Response(
                {"detail": f"Cannot cancel a request with status '{instance.get_status_display()}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.status = ApprovalRequest.Status.CANCELLED
        instance.save(update_fields=["status", "updated_at"])

        self._log_approval_audit("UPDATE", instance)

        return Response(
            ApprovalRequestSerializer(instance).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="pending-count")
    def pending_count(self, request):
        """
        Return the count of pending approval requests.

        For admin / manager roles the count covers the entire tenant.
        For regular employees the count covers only their own requests.
        """
        qs = self.get_queryset().filter(status=ApprovalRequest.Status.PENDING)

        if request.user.role not in ("SUPER_ADMIN", "TENANT_ADMIN", "MANAGER"):
            employee = request.user.employee_profiles.filter(
                tenant=request.tenant, is_deleted=False
            ).first()
            if employee:
                qs = qs.filter(requester=employee)
            else:
                qs = qs.none()

        return Response({"pending_count": qs.count()}, status=status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _log_approval_audit(self, action_type, instance):
        """Create an audit-log entry for approval workflow actions."""
        AuditLog.objects.create(
            tenant=getattr(self.request, "tenant", None),
            user=self.request.user if self.request.user.is_authenticated else None,
            action=action_type,
            resource_type=instance.__class__.__name__,
            resource_id=instance.pk,
            details={
                "status": instance.status,
                "request_type": instance.request_type,
                "title": instance.title,
            },
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get("HTTP_USER_AGENT", ""),
        )

    class Meta:
        model = ApprovalRequest
