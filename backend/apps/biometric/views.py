"""Views for the biometric app."""
import logging

from rest_framework import status, viewsets

logger = logging.getLogger(__name__)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Employee
from apps.core.mixins import TenantQuerySetMixin
from apps.core.permissions import IsEmployee, IsTenantAdmin, IsTenantMember

from .models import BiometricEnrollmentLog, BiometricTemplate
from .serializers import (
    BiometricEnrollmentLogSerializer,
    BiometricEnrollSerializer,
    BiometricTemplateSerializer,
    BiometricVerifyResponseSerializer,
    BiometricVerifySerializer,
)
from .services import BiometricService


class BiometricTemplateViewSet(TenantQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    """List and retrieve biometric templates. Admin sees all; employees see own."""
    queryset = BiometricTemplate.objects.select_related("employee", "employee__user")
    serializer_class = BiometricTemplateSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    filterset_fields = ["employee", "status"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role not in ("SUPER_ADMIN", "TENANT_ADMIN", "MANAGER"):
            qs = qs.filter(employee__user=self.request.user)
        return qs


class BiometricEnrollView(APIView):
    """Self-enrollment endpoint for biometric face recognition."""
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request, tenant_slug):
        serializer = BiometricEnrollSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not serializer.validated_data["liveness_passed"]:
            return Response(
                {"success": False, "error": "Liveness challenge must be passed before enrollment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        employee = Employee.objects.get(
            user=request.user, tenant=request.tenant, is_deleted=False
        )

        try:
            template = BiometricService.enroll(
                employee=employee,
                images=serializer.validated_data["images"],
                request=request,
            )
        except ValueError as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        return Response(
            {"success": True, "data": BiometricTemplateSerializer(template).data},
            status=status.HTTP_201_CREATED,
        )


class BiometricVerifyView(APIView):
    """Verify a face image against stored biometric template."""
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request, tenant_slug):
        serializer = BiometricVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        employee = Employee.objects.get(
            user=request.user, tenant=request.tenant, is_deleted=False
        )

        match, score = BiometricService.verify(
            employee=employee,
            image_file=serializer.validated_data["image"],
            tenant=request.tenant,
        )

        response_serializer = BiometricVerifyResponseSerializer(
            {"match": match, "score": score}
        )
        return Response({"success": True, "data": response_serializer.data})


class BiometricRevokeView(APIView):
    """Revoke an employee's biometric template (admin only)."""
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def post(self, request, tenant_slug, employee_id):
        try:
            employee = Employee.objects.get(
                id=employee_id, tenant=request.tenant, is_deleted=False
            )
        except Employee.DoesNotExist:
            return Response(
                {"success": False, "error": "Employee not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        revoked = BiometricService.revoke_template(
            employee=employee, tenant=request.tenant, user=request.user,
        )

        return Response({
            "success": True,
            "revoked": revoked,
            "message": "Biometric template revoked." if revoked else "No active template found.",
        })


class BiometricDeleteView(APIView):
    """Permanently delete biometric data for an employee (compliance/GDPR)."""
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def delete(self, request, tenant_slug, employee_id):
        try:
            employee = Employee.objects.get(
                id=employee_id, tenant=request.tenant, is_deleted=False
            )
        except Employee.DoesNotExist:
            return Response(
                {"success": False, "error": "Employee not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count = BiometricService.delete_template(
            employee=employee, tenant=request.tenant, user=request.user,
        )

        return Response({
            "success": True,
            "deleted_count": count,
            "message": f"Deleted {count} biometric template(s).",
        })


class BiometricEnrollmentLogViewSet(TenantQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    """Audit log of biometric enrollment events."""
    queryset = BiometricEnrollmentLog.objects.select_related("employee", "template")
    serializer_class = BiometricEnrollmentLogSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]
    filterset_fields = ["employee", "event"]
