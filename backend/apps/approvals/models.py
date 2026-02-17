"""Models for the approvals app — generic approval workflow."""
from django.conf import settings
from django.db import models

from apps.core.models import ActiveManager, TenantBaseModel


class ApprovalRequest(TenantBaseModel):
    """
    Generic, extensible approval-request model.

    Stores approval workflows for various request types such as
    attendance corrections, device changes, and leave requests.
    Type-specific payload is stored in the ``metadata`` JSONField,
    keeping the schema flexible for future request types.
    """

    class RequestType(models.TextChoices):
        ATTENDANCE_CORRECTION = "ATTENDANCE_CORRECTION", "Attendance Correction"
        DEVICE_CHANGE = "DEVICE_CHANGE", "Device Change"
        LEAVE_REQUEST = "LEAVE_REQUEST", "Leave Request"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    request_type = models.CharField(
        max_length=30,
        choices=RequestType.choices,
        db_index=True,
    )
    requester = models.ForeignKey(
        "accounts.Employee",
        on_delete=models.CASCADE,
        related_name="approval_requests",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Stores request-type-specific data as JSON.",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_approvals",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, default="")
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True,
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta(TenantBaseModel.Meta):
        verbose_name = "Approval Request"
        verbose_name_plural = "Approval Requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["tenant", "status", "created_at"],
                name="idx_appr_tnt_status_date",
            ),
            models.Index(
                fields=["requester", "status"],
                name="idx_appr_requester_status",
            ),
        ]

    def __str__(self):
        return f"[{self.get_request_type_display()}] {self.title} ({self.get_status_display()})"
