"""Models for the tenants app — Group, Tenant, and Department."""
from django.db import models

from apps.core.models import ActiveManager, BaseModel, TenantBaseModel


class Group(BaseModel):
    """Parent company / corporate group that owns one or more tenants."""

    name = models.CharField(max_length=255)
    name_ar = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Name (Arabic)",
    )
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta(BaseModel.Meta):
        verbose_name = "Group"
        verbose_name_plural = "Groups"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tenant(BaseModel):
    """
    A child company or branch that belongs to a Group.

    Each tenant represents an isolated organisational unit with its own
    employees, departments, devices, and attendance data.
    """

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="tenants",
    )
    name = models.CharField(max_length=255)
    name_ar = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Name (Arabic)",
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        help_text="Unique URL-safe identifier for this tenant.",
    )
    description = models.TextField(blank=True, default="")
    address = models.TextField(blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=10, default="SA")
    phone = models.CharField(max_length=30, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    timezone = models.CharField(max_length=50, default="Asia/Riyadh")
    is_active = models.BooleanField(default=True, db_index=True)
    logo = models.ImageField(
        upload_to="tenants/logos/",
        blank=True,
        null=True,
    )
    settings = models.JSONField(default=dict, blank=True)

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta(BaseModel.Meta):
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Department(TenantBaseModel):
    """Department within a tenant, supporting a hierarchical tree via *parent*."""

    name = models.CharField(max_length=255)
    name_ar = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Name (Arabic)",
    )
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta(TenantBaseModel.Meta):
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"],
                condition=models.Q(is_deleted=False),
                name="unique_department_name_per_tenant",
            ),
        ]

    def __str__(self):
        return self.name
