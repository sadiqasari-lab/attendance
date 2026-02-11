"""User and Employee models for the Inspire Attendance System."""
import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.core.models import TenantBaseModel

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model using email as the unique identifier."""

    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        TENANT_ADMIN = "TENANT_ADMIN", "Tenant Admin"
        MANAGER = "MANAGER", "Manager"
        EMPLOYEE = "EMPLOYEE", "Employee"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    first_name_ar = models.CharField(
        max_length=150, blank=True, verbose_name="First Name (Arabic)"
    )
    last_name_ar = models.CharField(
        max_length=150, blank=True, verbose_name="Last Name (Arabic)"
    )
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        db_index=True,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    requires_biometric_enrollment = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Return full name in English."""
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.email

    @property
    def full_name_ar(self):
        """Return full name in Arabic."""
        name = f"{self.first_name_ar} {self.last_name_ar}".strip()
        return name or self.full_name


class Employee(TenantBaseModel):
    """Employee profile linked to a user within a specific tenant."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="employee_profiles",
    )
    employee_id = models.CharField(
        max_length=50,
        help_text="Unique employee identifier within the tenant.",
    )
    department = models.ForeignKey(
        "tenants.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    designation = models.CharField(max_length=150, blank=True)
    designation_ar = models.CharField(
        max_length=150, blank=True, verbose_name="Designation (Arabic)"
    )
    date_of_joining = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta(TenantBaseModel.Meta):
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        unique_together = [
            ("tenant", "employee_id"),
            ("tenant", "user"),
        ]

    def __str__(self):
        return f"{self.employee_id} - {self.user.full_name}"
