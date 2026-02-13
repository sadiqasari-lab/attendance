"""Views for the devices app."""
import logging

from django.utils import timezone

logger = logging.getLogger(__name__)
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Employee
from apps.core.exceptions import DeviceNotRegisteredError
from apps.core.mixins import AuditLogMixin, TenantQuerySetMixin
from apps.core.models import AuditLog
from apps.core.permissions import IsEmployee, IsTenantAdmin, IsTenantMember
from apps.core.utils import get_client_ip

from .models import DeviceChangeRequest, DeviceRegistry
from .serializers import (
    DeviceChangeRequestSerializer,
    DeviceRegisterSerializer,
    DeviceRegistrySerializer,
    RootDetectionSerializer,
)


class DeviceRegistryViewSet(TenantQuerySetMixin, AuditLogMixin, viewsets.ReadOnlyModelViewSet):
    """List and retrieve registered devices. Admin can see all, employees see own."""
    queryset = DeviceRegistry.objects.select_related("employee", "employee__user")
    serializer_class = DeviceRegistrySerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    filterset_fields = ["employee", "status", "device_type", "platform"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role not in ("SUPER_ADMIN", "TENANT_ADMIN", "MANAGER"):
            qs = qs.filter(employee__user=self.request.user)
        return qs


class DeviceRegisterView(APIView):
    """Register a new device for the authenticated employee."""
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request, tenant_slug):
        serializer = DeviceRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        tenant = request.tenant

        employee = Employee.objects.get(
            user=request.user, tenant=tenant, is_deleted=False
        )

        # Reject rooted devices for company type
        if data.get("is_rooted") and data["device_type"] == DeviceRegistry.DeviceType.COMPANY:
            return Response(
                {"success": False, "error": "Rooted company devices are not allowed."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # BYOD: one-device-per-user enforcement
        existing_active = DeviceRegistry.objects.filter(
            tenant=tenant,
            employee=employee,
            status=DeviceRegistry.Status.ACTIVE,
            is_deleted=False,
        )

        if data["device_type"] == DeviceRegistry.DeviceType.BYOD and existing_active.exists():
            return Response(
                {
                    "success": False,
                    "error": "You already have an active device. Submit a device change request.",
                },
                status=status.HTTP_409_CONFLICT,
            )

        # Check if same device already registered
        existing_device = DeviceRegistry.objects.filter(
            tenant=tenant,
            employee=employee,
            device_identifier=data["device_identifier"],
            is_deleted=False,
        ).first()

        if existing_device:
            if existing_device.status == DeviceRegistry.Status.ACTIVE:
                return Response(
                    {"success": True, "data": DeviceRegistrySerializer(existing_device).data},
                )
            existing_device.status = DeviceRegistry.Status.PENDING
            existing_device.save(update_fields=["status", "updated_at"])
            device = existing_device
        else:
            auto_approve = data["device_type"] == DeviceRegistry.DeviceType.COMPANY
            device = DeviceRegistry.objects.create(
                tenant=tenant,
                employee=employee,
                device_type=data["device_type"],
                platform=data["platform"],
                device_identifier=data["device_identifier"],
                device_model=data.get("device_model", ""),
                device_manufacturer=data.get("device_manufacturer", ""),
                os_version=data.get("os_version", ""),
                app_version=data.get("app_version", ""),
                fcm_token=data.get("fcm_token", ""),
                is_rooted=data.get("is_rooted", False),
                status=(
                    DeviceRegistry.Status.ACTIVE if auto_approve
                    else DeviceRegistry.Status.PENDING
                ),
                created_by=request.user,
            )

        AuditLog.objects.create(
            tenant=tenant,
            user=request.user,
            action="DEVICE_REGISTER",
            resource_type="DeviceRegistry",
            resource_id=device.pk,
            details={
                "device_type": data["device_type"],
                "platform": data["platform"],
                "device_model": data.get("device_model", ""),
            },
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return Response(
            {"success": True, "data": DeviceRegistrySerializer(device).data},
            status=status.HTTP_201_CREATED,
        )


class DeviceApproveView(APIView):
    """Admin endpoint to approve/revoke a device."""
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def post(self, request, tenant_slug, device_id):
        action = request.data.get("action")  # "approve" or "revoke"
        if action not in ("approve", "revoke"):
            return Response(
                {"success": False, "error": "Action must be 'approve' or 'revoke'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            device = DeviceRegistry.objects.get(
                id=device_id, tenant=request.tenant, is_deleted=False,
            )
        except DeviceRegistry.DoesNotExist:
            return Response(
                {"success": False, "error": "Device not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if action == "approve":
            device.status = DeviceRegistry.Status.ACTIVE
        else:
            device.status = DeviceRegistry.Status.REVOKED

        device.save(update_fields=["status", "updated_at"])

        AuditLog.objects.create(
            tenant=request.tenant,
            user=request.user,
            action="APPROVAL" if action == "approve" else "REJECTION",
            resource_type="DeviceRegistry",
            resource_id=device.pk,
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return Response({"success": True, "data": DeviceRegistrySerializer(device).data})


class DeviceChangeRequestViewSet(
    TenantQuerySetMixin, AuditLogMixin, viewsets.ModelViewSet
):
    queryset = DeviceChangeRequest.objects.select_related("employee", "old_device")
    serializer_class = DeviceChangeRequestSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    filterset_fields = ["status", "employee"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role not in ("SUPER_ADMIN", "TENANT_ADMIN", "MANAGER"):
            qs = qs.filter(employee__user=self.request.user)
        return qs

    def perform_create(self, serializer):
        employee = Employee.objects.get(
            user=self.request.user, tenant=self.request.tenant, is_deleted=False,
        )
        current_device = DeviceRegistry.objects.filter(
            tenant=self.request.tenant,
            employee=employee,
            status=DeviceRegistry.Status.ACTIVE,
            is_deleted=False,
        ).first()
        serializer.save(
            tenant=self.request.tenant,
            employee=employee,
            old_device=current_device,
            created_by=self.request.user,
        )


class RootDetectionView(APIView):
    """Endpoint for mobile app to report root detection results."""
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request, tenant_slug):
        serializer = RootDetectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        device = DeviceRegistry.objects.filter(
            tenant=request.tenant,
            employee__user=request.user,
            device_identifier=data["device_identifier"],
            is_deleted=False,
        ).first()

        if not device:
            raise DeviceNotRegisteredError()

        if data["is_rooted"]:
            device.is_rooted = True
            if device.device_type == DeviceRegistry.DeviceType.COMPANY:
                device.status = DeviceRegistry.Status.REVOKED
            device.save(update_fields=["is_rooted", "status", "updated_at"])

            AuditLog.objects.create(
                tenant=request.tenant,
                user=request.user,
                action="DEVICE_REGISTER",
                resource_type="DeviceRegistry",
                resource_id=device.pk,
                details={
                    "root_detected": True,
                    "indicators": data.get("root_indicators", []),
                },
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )

        return Response({"success": True, "rooted": data["is_rooted"]})
