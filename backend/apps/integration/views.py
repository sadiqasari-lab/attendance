"""Views for the HRIS integration app."""
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.attendance.models import AttendanceRecord, Shift
from apps.core.mixins import AuditLogMixin, TenantQuerySetMixin
from apps.core.models import AuditLog
from apps.core.permissions import IsSuperAdmin, IsTenantAdmin
from apps.core.utils import get_client_ip

from .authentication import IntegrationTokenAuthentication
from .models import IntegrationToken, IntegrationWebhookLog, WebhookConfig
from .serializers import (
    AttendanceLogPullSerializer,
    IntegrationTokenCreateSerializer,
    IntegrationTokenSerializer,
    IntegrationWebhookLogSerializer,
    ShiftPullSerializer,
    WebhookConfigSerializer,
)


# ---------------------------------------------------------------
# Admin endpoints (JWT-authenticated tenant admins)
# ---------------------------------------------------------------
class IntegrationTokenViewSet(viewsets.ModelViewSet):
    """Manage HRIS integration tokens."""
    queryset = IntegrationToken.objects.all()
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def get_serializer_class(self):
        if self.action == "create":
            return IntegrationTokenCreateSerializer
        return IntegrationTokenSerializer

    def get_queryset(self):
        qs = super().get_queryset().filter(is_deleted=False)
        user = self.request.user
        if user.role == "SUPER_ADMIN":
            return qs
        tenant_ids = user.employee_profiles.filter(
            is_deleted=False
        ).values_list("tenant_id", flat=True)
        return qs.filter(tenant_id__in=tenant_ids)

    def perform_create(self, serializer):
        tenant_id = self.request.data.get("tenant_id")
        if tenant_id:
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.get(id=tenant_id, is_deleted=False)
        else:
            tenant = self.request.user.employee_profiles.filter(
                is_deleted=False
            ).first().tenant
        serializer.save(tenant=tenant, created_by=self.request.user)


class WebhookConfigViewSet(viewsets.ModelViewSet):
    """Manage webhook configurations."""
    queryset = WebhookConfig.objects.all()
    serializer_class = WebhookConfigSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def get_queryset(self):
        qs = super().get_queryset().filter(is_deleted=False)
        user = self.request.user
        if user.role == "SUPER_ADMIN":
            return qs
        tenant_ids = user.employee_profiles.filter(
            is_deleted=False
        ).values_list("tenant_id", flat=True)
        return qs.filter(tenant_id__in=tenant_ids)

    def perform_create(self, serializer):
        tenant_id = self.request.data.get("tenant_id")
        if tenant_id:
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.get(id=tenant_id, is_deleted=False)
        else:
            tenant = self.request.user.employee_profiles.filter(
                is_deleted=False
            ).first().tenant
        serializer.save(tenant=tenant, created_by=self.request.user)


class WebhookLogViewSet(viewsets.ReadOnlyModelViewSet):
    """View webhook delivery logs."""
    queryset = IntegrationWebhookLog.objects.select_related("webhook")
    serializer_class = IntegrationWebhookLogSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]
    filterset_fields = ["status", "event_type"]

    def get_queryset(self):
        qs = super().get_queryset().filter(is_deleted=False)
        user = self.request.user
        if user.role == "SUPER_ADMIN":
            return qs
        tenant_ids = user.employee_profiles.filter(
            is_deleted=False
        ).values_list("tenant_id", flat=True)
        return qs.filter(tenant_id__in=tenant_ids)


# ---------------------------------------------------------------
# External HRIS pull endpoints (token-authenticated)
# ---------------------------------------------------------------
class AttendanceLogsPullView(APIView):
    """
    Pull attendance logs for a tenant.
    Authenticated via IntegrationToken, not JWT.
    """
    authentication_classes = [IntegrationTokenAuthentication]
    permission_classes = []

    def get(self, request):
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return Response(
                {"error": "Invalid token or tenant."}, status=status.HTTP_403_FORBIDDEN
            )

        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        employee_id = request.query_params.get("employee_id")

        records = AttendanceRecord.objects.filter(
            tenant=tenant, is_deleted=False
        ).select_related("employee", "employee__user", "shift")

        if date_from:
            records = records.filter(date__gte=date_from)
        if date_to:
            records = records.filter(date__lte=date_to)
        if employee_id:
            records = records.filter(employee__employee_id=employee_id)

        data = []
        for r in records[:1000]:
            data.append({
                "employee_id": r.employee.employee_id,
                "employee_email": r.employee.user.email,
                "date": r.date,
                "shift_name": r.shift.name,
                "clock_in_time": r.clock_in_time,
                "clock_out_time": r.clock_out_time,
                "status": r.status,
                "duration_hours": r.duration_hours,
                "is_validated": r.is_validated,
            })

        # Log the integration access
        AuditLog.objects.create(
            tenant=tenant,
            action="INTEGRATION",
            resource_type="AttendanceRecord",
            details={
                "endpoint": "attendance_logs_pull",
                "records_returned": len(data),
                "date_from": date_from,
                "date_to": date_to,
            },
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        serializer = AttendanceLogPullSerializer(data, many=True)
        return Response({"success": True, "data": serializer.data})


class ShiftsPullView(APIView):
    """Pull shift definitions for a tenant via integration token."""
    authentication_classes = [IntegrationTokenAuthentication]
    permission_classes = []

    def get(self, request):
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return Response(
                {"error": "Invalid token or tenant."}, status=status.HTTP_403_FORBIDDEN
            )

        shifts = Shift.objects.filter(tenant=tenant, is_active=True, is_deleted=False)
        data = []
        for s in shifts:
            data.append({
                "shift_id": s.id,
                "name": s.name,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "grace_period_minutes": s.grace_period_minutes,
                "is_overnight": s.is_overnight,
            })

        AuditLog.objects.create(
            tenant=tenant,
            action="INTEGRATION",
            resource_type="Shift",
            details={"endpoint": "shifts_pull", "records_returned": len(data)},
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        serializer = ShiftPullSerializer(data, many=True)
        return Response({"success": True, "data": serializer.data})


class AttendanceSummaryPullView(APIView):
    """Pull attendance summary for a tenant via integration token."""
    authentication_classes = [IntegrationTokenAuthentication]
    permission_classes = []

    def get(self, request):
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return Response(
                {"error": "Invalid token or tenant."}, status=status.HTTP_403_FORBIDDEN
            )

        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        records = AttendanceRecord.objects.filter(
            tenant=tenant, is_deleted=False
        )
        if date_from:
            records = records.filter(date__gte=date_from)
        if date_to:
            records = records.filter(date__lte=date_to)

        total = records.count()
        present = records.filter(status="PRESENT").count()
        late = records.filter(status="LATE").count()
        absent = records.filter(status="ABSENT").count()
        early_departure = records.filter(status="EARLY_DEPARTURE").count()

        summary = {
            "tenant": tenant.name,
            "date_from": date_from,
            "date_to": date_to,
            "total_records": total,
            "present": present,
            "late": late,
            "absent": absent,
            "early_departure": early_departure,
        }

        AuditLog.objects.create(
            tenant=tenant,
            action="INTEGRATION",
            resource_type="AttendanceSummary",
            details={"endpoint": "summary_pull", **summary},
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return Response({"success": True, "data": summary})
