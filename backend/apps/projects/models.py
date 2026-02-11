"""Models for the projects app — Project and EmployeeProjectAssignment."""
from django.db import models

from apps.core.models import ActiveManager, TenantBaseModel


class Project(TenantBaseModel):
    """
    A project within a tenant that employees can be assigned to.

    Projects represent distinct work units or sites and may be tied to a
    geographic location via a geofence for attendance tracking purposes.
    """

    class Status(models.TextChoices):
        PLANNING = "PLANNING", "Planning"
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        ON_HOLD = "ON_HOLD", "On Hold"

    name = models.CharField(max_length=255)
    name_ar = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Name (Arabic)",
    )
    description = models.TextField(blank=True, default="")
    location_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Location Name",
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )
    geofence = models.ForeignKey(
        "attendance.Geofence",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta(TenantBaseModel.Meta):
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ["-created_at"]
        unique_together = [("tenant", "name")]

    def __str__(self):
        return self.name

    @property
    def assignment_count(self):
        """Return the number of active employee assignments."""
        return self.assignments.filter(is_active=True, is_deleted=False).count()


class EmployeeProjectAssignment(TenantBaseModel):
    """
    Maps an employee to a project within the same tenant.

    Each assignment carries a role that determines the employee's
    responsibilities within that project context.
    """

    class Role(models.TextChoices):
        WORKER = "WORKER", "Worker"
        SUPERVISOR = "SUPERVISOR", "Supervisor"
        MANAGER = "MANAGER", "Manager"

    employee = models.ForeignKey(
        "accounts.Employee",
        on_delete=models.CASCADE,
        related_name="project_assignments",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.WORKER,
        db_index=True,
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    notes = models.TextField(blank=True, default="")

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta(TenantBaseModel.Meta):
        verbose_name = "Employee Project Assignment"
        verbose_name_plural = "Employee Project Assignments"
        ordering = ["-created_at"]
        unique_together = [("tenant", "employee", "project")]

    def __str__(self):
        return (
            f"{self.employee} -> {self.project.name} ({self.get_role_display()})"
        )
