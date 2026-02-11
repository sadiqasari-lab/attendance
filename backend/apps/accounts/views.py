"""Views for authentication, user profile, and employee management."""
from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.core.mixins import AuditLogMixin, TenantQuerySetMixin
from apps.core.models import AuditLog
from apps.core.permissions import IsEmployee, IsTenantAdmin
from apps.core.utils import get_client_ip

from .models import Employee, User
from .serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    EmployeeCreateSerializer,
    EmployeeSerializer,
    ProfileSerializer,
)


# ---------------------------------------------------------------
# Authentication Views
# ---------------------------------------------------------------
class LoginView(TokenObtainPairView):
    """Authenticate a user and return JWT access/refresh tokens."""

    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, InvalidToken) as e:
            return Response(
                {"success": False, "error": {"code": 401, "detail": str(e)}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Audit log
        user = serializer.user
        AuditLog.objects.create(
            user=user,
            action="LOGIN",
            resource_type="User",
            resource_id=user.pk,
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return Response(
            {"success": True, "data": serializer.validated_data},
            status=status.HTTP_200_OK,
        )


class CustomTokenRefreshView(TokenRefreshView):
    """Refresh an access token using a valid refresh token."""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, InvalidToken) as e:
            return Response(
                {"success": False, "error": {"code": 401, "detail": str(e)}},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(
            {"success": True, "data": serializer.validated_data},
            status=status.HTTP_200_OK,
        )


class LogoutView(generics.GenericAPIView):
    """Blacklist the provided refresh token to log the user out."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": 400,
                        "detail": "Refresh token is required.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except (TokenError, InvalidToken) as e:
            return Response(
                {"success": False, "error": {"code": 400, "detail": str(e)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Audit log
        AuditLog.objects.create(
            user=request.user,
            action="LOGOUT",
            resource_type="User",
            resource_id=request.user.pk,
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return Response(
            {"success": True, "data": {"detail": "Successfully logged out."}},
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------
# Profile Views
# ---------------------------------------------------------------
class UserProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the authenticated user's profile."""

    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(
            {"success": True, "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"success": True, "data": serializer.data},
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(generics.GenericAPIView):
    """Allow the authenticated user to change their password."""

    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"success": True, "data": {"detail": "Password updated successfully."}},
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------
# Employee ViewSet
# ---------------------------------------------------------------
class EmployeeViewSet(TenantQuerySetMixin, AuditLogMixin, viewsets.ModelViewSet):
    """CRUD operations for employees, scoped to the current tenant."""

    queryset = Employee.objects.select_related("user", "department", "tenant").all()
    permission_classes = [IsAuthenticated, IsTenantAdmin]
    filterset_fields = ["is_active", "department", "user__role"]
    search_fields = ["employee_id", "user__email", "user__first_name", "user__last_name"]
    ordering_fields = ["employee_id", "date_of_joining", "created_at"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return EmployeeCreateSerializer
        return EmployeeSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated(), IsEmployee()]
        return [IsAuthenticated(), IsTenantAdmin()]

    def perform_create(self, serializer):
        tenant = getattr(self.request, "tenant", None)
        instance = serializer.save(
            tenant=tenant,
            created_by=self.request.user,
        )
        self._log_audit("CREATE", instance)
        return instance

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            paginated.data = {"success": True, "data": paginated.data}
            return paginated
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {"success": True, "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            {"success": True, "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        output_serializer = EmployeeSerializer(
            serializer.instance,
            context=self.get_serializer_context(),
        )
        return Response(
            {"success": True, "data": output_serializer.data},
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        output_serializer = EmployeeSerializer(
            instance, context=self.get_serializer_context()
        )
        return Response(
            {"success": True, "data": output_serializer.data},
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"success": True, "data": {"detail": "Employee deleted successfully."}},
            status=status.HTTP_200_OK,
        )
