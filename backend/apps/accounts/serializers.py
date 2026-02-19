"""Serializers for the accounts app."""
from django.contrib.auth import password_validation
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Employee, User


# ---------------------------------------------------------------
# User Serializers
# ---------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    """Read-only serializer for user data."""

    full_name = serializers.CharField(read_only=True)
    full_name_ar = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "first_name_ar",
            "last_name_ar",
            "phone",
            "role",
            "is_active",
            "date_joined",
            "requires_biometric_enrollment",
            "full_name",
            "full_name_ar",
        ]
        read_only_fields = fields


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for user registration with password validation."""

    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "first_name_ar",
            "last_name_ar",
            "phone",
            "role",
            "password",
            "password_confirm",
        ]
        read_only_fields = ["id"]

    def validate_password(self, value):
        """Run Django's built-in password validators."""
        password_validation.validate_password(value)
        return value

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


# ---------------------------------------------------------------
# Employee Serializers
# ---------------------------------------------------------------
class EmployeeSerializer(serializers.ModelSerializer):
    """Serializer for reading employee data, with nested user info."""

    user = UserSerializer(read_only=True)
    department_name = serializers.CharField(
        source="department.name", read_only=True, default=None
    )

    class Meta:
        model = Employee
        fields = [
            "id",
            "user",
            "employee_id",
            "department",
            "department_name",
            "designation",
            "designation_ar",
            "date_of_joining",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EmployeeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating / updating employee records."""

    user_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Employee
        fields = [
            "id",
            "user_id",
            "employee_id",
            "department",
            "designation",
            "designation_ar",
            "date_of_joining",
            "is_active",
        ]
        read_only_fields = ["id"]

    def validate_user_id(self, value):
        """Ensure the referenced user exists."""
        try:
            User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this ID does not exist.")
        return value

    def create(self, validated_data):
        user_id = validated_data.pop("user_id")
        validated_data["user_id"] = user_id
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("user_id", None)
        return super().update(instance, validated_data)


class EmployeeWithUserCreateSerializer(serializers.Serializer):
    """Create a User and Employee record in a single request."""

    # User fields
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    first_name = serializers.CharField(required=False, default="", allow_blank=True)
    last_name = serializers.CharField(required=False, default="", allow_blank=True)
    first_name_ar = serializers.CharField(required=False, default="", allow_blank=True)
    last_name_ar = serializers.CharField(required=False, default="", allow_blank=True)
    phone = serializers.CharField(required=False, default="", allow_blank=True)
    role = serializers.ChoiceField(
        choices=User.Role.choices, required=False, default="EMPLOYEE"
    )

    # Employee fields
    employee_id = serializers.CharField(max_length=50)
    department = serializers.UUIDField(required=False, allow_null=True, default=None)
    designation = serializers.CharField(required=False, default="", allow_blank=True)
    designation_ar = serializers.CharField(required=False, default="", allow_blank=True)
    date_of_joining = serializers.DateField(required=False, allow_null=True, default=None)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def validate_department(self, value):
        if value is not None:
            from apps.tenants.models import Department

            if not Department.objects.filter(pk=value).exists():
                raise serializers.ValidationError("Department does not exist.")
        return value

    def create(self, validated_data):
        from django.db import transaction

        from apps.tenants.models import Department

        dept_id = validated_data.pop("department", None)
        employee_id_val = validated_data.pop("employee_id")
        designation = validated_data.pop("designation", "")
        designation_ar = validated_data.pop("designation_ar", "")
        date_of_joining = validated_data.pop("date_of_joining", None)
        password = validated_data.pop("password")

        with transaction.atomic():
            user = User(**validated_data)
            user.set_password(password)
            user.save()

            dept = Department.objects.get(pk=dept_id) if dept_id else None
            employee = Employee.objects.create(
                user=user,
                employee_id=employee_id_val,
                department=dept,
                designation=designation,
                designation_ar=designation_ar,
                date_of_joining=date_of_joining,
                tenant=self.context.get("tenant"),
                created_by=self.context.get("created_by"),
            )
        return employee


# ---------------------------------------------------------------
# Authentication Serializers
# ---------------------------------------------------------------
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extend JWT claims with user role, email, and tenant information."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["user_id"] = str(user.id)
        token["email"] = user.email
        token["role"] = user.role
        token["full_name"] = user.full_name

        # Include first active tenant info if available
        employee_profile = (
            user.employee_profiles.filter(is_active=True, is_deleted=False)
            .select_related("tenant")
            .first()
        )
        if employee_profile:
            token["tenant_id"] = str(employee_profile.tenant_id)
            token["tenant_slug"] = employee_profile.tenant.slug
            token["employee_id"] = str(employee_profile.id)
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": str(self.user.id),
            "email": self.user.email,
            "full_name": self.user.full_name,
            "role": self.user.role,
            "requires_biometric_enrollment": self.user.requires_biometric_enrollment,
        }

        # Attach tenant information
        employee_profile = (
            self.user.employee_profiles.filter(is_active=True, is_deleted=False)
            .select_related("tenant")
            .first()
        )
        if employee_profile:
            data["tenant"] = {
                "id": str(employee_profile.tenant_id),
                "name": employee_profile.tenant.name,
                "slug": employee_profile.tenant.slug,
            }
        else:
            data["tenant"] = None
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing the authenticated user's password."""

    old_password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )
    new_password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )
    new_password_confirm = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        password_validation.validate_password(value, self.context["request"].user)
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "New passwords do not match."}
            )
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


# ---------------------------------------------------------------
# Profile Serializer
# ---------------------------------------------------------------
class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for viewing / updating the authenticated user's profile."""

    full_name = serializers.CharField(read_only=True)
    full_name_ar = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "first_name_ar",
            "last_name_ar",
            "phone",
            "role",
            "is_active",
            "date_joined",
            "requires_biometric_enrollment",
            "full_name",
            "full_name_ar",
        ]
        read_only_fields = [
            "id",
            "email",
            "role",
            "is_active",
            "date_joined",
            "requires_biometric_enrollment",
        ]
