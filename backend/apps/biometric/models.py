"""Biometric template models for face recognition enrollment."""
from django.db import models

from apps.core.models import ActiveManager, TenantBaseModel


class BiometricTemplate(TenantBaseModel):
    """Encrypted facial recognition embedding for an employee."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        REVOKED = "REVOKED", "Revoked"
        EXPIRED = "EXPIRED", "Expired"

    employee = models.ForeignKey(
        "accounts.Employee",
        on_delete=models.CASCADE,
        related_name="biometric_templates",
    )
    encrypted_embedding = models.BinaryField(
        help_text="AES-256 encrypted face embedding vector.",
    )
    embedding_version = models.PositiveIntegerField(
        default=1,
        help_text="Version number for embedding rotation support.",
    )
    encryption_iv = models.BinaryField(
        help_text="Initialization vector used for AES encryption.",
    )
    num_images_used = models.PositiveIntegerField(
        default=0,
        help_text="Number of images used to generate this embedding.",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    quality_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Overall quality score of the enrollment (0-1).",
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta(TenantBaseModel.Meta):
        verbose_name = "Biometric Template"
        verbose_name_plural = "Biometric Templates"
        indexes = [
            models.Index(fields=["tenant", "employee", "status"]),
        ]

    def __str__(self):
        return f"Template v{self.embedding_version} for {self.employee} ({self.status})"


class BiometricEnrollmentLog(TenantBaseModel):
    """Audit log for biometric enrollment events."""

    class Event(models.TextChoices):
        STARTED = "STARTED", "Enrollment Started"
        IMAGE_CAPTURED = "IMAGE_CAPTURED", "Image Captured"
        LIVENESS_PASSED = "LIVENESS_PASSED", "Liveness Passed"
        LIVENESS_FAILED = "LIVENESS_FAILED", "Liveness Failed"
        EMBEDDING_GENERATED = "EMBEDDING_GENERATED", "Embedding Generated"
        COMPLETED = "COMPLETED", "Enrollment Completed"
        FAILED = "FAILED", "Enrollment Failed"
        REVOKED = "REVOKED", "Template Revoked"

    employee = models.ForeignKey(
        "accounts.Employee",
        on_delete=models.CASCADE,
        related_name="enrollment_logs",
    )
    template = models.ForeignKey(
        BiometricTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enrollment_logs",
    )
    event = models.CharField(max_length=25, choices=Event.choices, db_index=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta(TenantBaseModel.Meta):
        verbose_name = "Biometric Enrollment Log"
        verbose_name_plural = "Biometric Enrollment Logs"

    def __str__(self):
        return f"{self.event} for {self.employee} at {self.created_at}"
