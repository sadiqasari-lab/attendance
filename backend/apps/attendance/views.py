"""Views for the attendance app."""
from datetime import timedelta

from django.db.models import Count, Q, Sum, F
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Employee
from apps.core.mixins import AuditLogMixin, TenantQuerySetMixin
from apps.core.permissions import IsEmployee, IsManager, IsTenantAdmin, IsTenantMember

from .models import (
    AttendanceCorrectionRequest,
    AttendancePolicy,
    AttendanceRecord,
    Geofence,
    Shift,
    WifiPolicy,
)
from .serializers import (
    AttendanceCorrectionRequestSerializer,
    AttendancePolicySerializer,
    AttendanceRecordSerializer,
    AttendanceSummarySerializer,
    ClockInSerializer,
    ClockOutSerializer,
    GeofenceSerializer,
    OfflineSyncSerializer,
    ShiftSerializer,
    WifiPolicySerializer,
)
from .services import AttendanceService


class ShiftViewSet(TenantQuerySetMixin, AuditLogMixin, viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    filterset_fields = ["is_active"]
    search_fields = ["name", "name_ar"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsTenantAdmin()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant, created_by=self.request.user)


class AttendancePolicyViewSet(TenantQuerySetMixin, AuditLogMixin, viewsets.ModelViewSet):
    queryset = AttendancePolicy.objects.all()
    serializer_class = AttendancePolicySerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant, created_by=self.request.user)


class GeofenceViewSet(TenantQuerySetMixin, AuditLogMixin, viewsets.ModelViewSet):
    queryset = Geofence.objects.all()
    serializer_class = GeofenceSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    filterset_fields = ["is_active"]
    search_fields = ["name", "name_ar"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsTenantAdmin()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant, created_by=self.request.user)


class WifiPolicyViewSet(TenantQuerySetMixin, AuditLogMixin, viewsets.ModelViewSet):
    queryset = WifiPolicy.objects.all()
    serializer_class = WifiPolicySerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant, created_by=self.request.user)


class AttendanceRecordViewSet(TenantQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = AttendanceRecord.objects.select_related("employee", "shift", "geofence")
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    filterset_fields = ["employee", "shift", "status", "date", "is_validated", "is_offline_record"]
    search_fields = ["employee__employee_id", "notes"]
    ordering_fields = ["date", "clock_in_time", "status"]

    def get_queryset(self):
        qs = super().get_queryset()
        # Date range filtering
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)

        # Non-admin users see only their own records
        if self.request.user.role not in ("SUPER_ADMIN", "TENANT_ADMIN", "MANAGER"):
            qs = qs.filter(employee__user=self.request.user)
        return qs


class ClockInView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request, tenant_slug):
        serializer = ClockInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        employee = Employee.objects.get(
            user=request.user, tenant=request.tenant, is_deleted=False
        )

        record = AttendanceService.clock_in(
            employee=employee,
            data=serializer.validated_data,
            request=request,
        )
        return Response(
            {"success": True, "data": AttendanceRecordSerializer(record).data},
            status=status.HTTP_201_CREATED,
        )


class ClockOutView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request, tenant_slug):
        serializer = ClockOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        employee = Employee.objects.get(
            user=request.user, tenant=request.tenant, is_deleted=False
        )

        record = AttendanceService.clock_out(
            employee=employee,
            record_id=serializer.validated_data["record_id"],
            data=serializer.validated_data,
            request=request,
        )
        return Response(
            {"success": True, "data": AttendanceRecordSerializer(record).data},
        )


class OfflineSyncView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request, tenant_slug):
        serializer = OfflineSyncSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        employee = Employee.objects.get(
            user=request.user, tenant=request.tenant, is_deleted=False
        )

        record = AttendanceService.sync_offline_record(
            employee=employee,
            data=serializer.validated_data,
            request=request,
        )
        return Response(
            {"success": True, "data": AttendanceRecordSerializer(record).data},
            status=status.HTTP_201_CREATED,
        )


class AttendanceCorrectionRequestViewSet(
    TenantQuerySetMixin, AuditLogMixin, viewsets.ModelViewSet
):
    queryset = AttendanceCorrectionRequest.objects.select_related(
        "attendance_record", "employee", "reviewed_by"
    )
    serializer_class = AttendanceCorrectionRequestSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    filterset_fields = ["status", "employee"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role not in ("SUPER_ADMIN", "TENANT_ADMIN", "MANAGER"):
            qs = qs.filter(employee__user=self.request.user)
        return qs

    def perform_create(self, serializer):
        employee = Employee.objects.get(
            user=self.request.user, tenant=self.request.tenant, is_deleted=False
        )
        serializer.save(
            tenant=self.request.tenant,
            employee=employee,
            created_by=self.request.user,
        )


class AttendanceSummaryView(APIView):
    """Aggregate attendance summary for a date range."""
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get(self, request, tenant_slug):
        tenant = request.tenant
        date_from = request.query_params.get("date_from", str(timezone.localdate() - timedelta(days=30)))
        date_to = request.query_params.get("date_to", str(timezone.localdate()))
        employee_id = request.query_params.get("employee_id")

        records = AttendanceRecord.objects.filter(
            tenant=tenant,
            date__gte=date_from,
            date__lte=date_to,
            is_deleted=False,
        )

        if employee_id:
            records = records.filter(employee_id=employee_id)
        elif request.user.role not in ("SUPER_ADMIN", "TENANT_ADMIN", "MANAGER"):
            records = records.filter(employee__user=request.user)

        employees = (
            records.values("employee__id", "employee__employee_id", "employee__user__first_name", "employee__user__last_name")
            .annotate(
                total_days=Count("id"),
                present_count=Count("id", filter=Q(status="PRESENT")),
                absent_count=Count("id", filter=Q(status="ABSENT")),
                late_count=Count("id", filter=Q(status="LATE")),
                early_departure_count=Count("id", filter=Q(status="EARLY_DEPARTURE")),
                half_day_count=Count("id", filter=Q(status="HALF_DAY")),
                leave_count=Count("id", filter=Q(status="ON_LEAVE")),
            )
        )

        summaries = []
        for emp in employees:
            emp_records = records.filter(employee__id=emp["employee__id"])
            total_hours = 0.0
            for r in emp_records.filter(clock_out_time__isnull=False):
                if r.duration_hours:
                    total_hours += r.duration_hours

            days = emp["total_days"] or 1
            summaries.append({
                "employee_id": emp["employee__id"],
                "employee_name": f"{emp['employee__user__first_name']} {emp['employee__user__last_name']}",
                "date_from": date_from,
                "date_to": date_to,
                "total_days": emp["total_days"],
                "present_count": emp["present_count"],
                "absent_count": emp["absent_count"],
                "late_count": emp["late_count"],
                "early_departure_count": emp["early_departure_count"],
                "half_day_count": emp["half_day_count"],
                "leave_count": emp["leave_count"],
                "total_hours": round(total_hours, 2),
                "avg_hours_per_day": round(total_hours / days, 2),
            })

        serializer = AttendanceSummarySerializer(summaries, many=True)
        return Response({"success": True, "data": serializer.data})
