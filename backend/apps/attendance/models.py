"""Models for the attendance app — Shift, Policy, Geofence, Wifi, Record, Correction."""
from django.conf import settings
from django.db import models

from apps.core.models import ActiveManager, TenantBaseModel


# ---------------------------------------------------------------------------
# Shift
# ---------------------------------------------------------------------------
class Shift(TenantBaseModel):
    """Work shift definition with start/end times and grace period."""

    name = models.CharField(max_length=255)
    name_ar = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Name (Arabic)",
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    grace_period_minutes = models.PositiveIntegerField(
        default=15,
        help_text="Minutes after shift start before marking as late.",
    )
    is_overnight = models.BooleanField(
        default=False,
        help_text="Whether this shift spans midnight.",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    description = models.TextField(blank=True, default="")

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta(TenantBaseModel.Meta):
        verbose_name = "Shift"
        verbose_name_plural = "Shifts"
        unique_together = [("tenant", "name")]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"


# ---------------------------------------------------------------------------
# Attendance Policy
# ---------------------------------------------------------------------------
class AttendancePolicy(TenantBaseModel):
    """Configurable attendance validation policy per tenant."""

    name = models.CharField(max_length=255)
    name_ar = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Name (Arabic)",
    )

    # Biometric requirements
    require_selfie = models.BooleanField(
        default=True,
        help_text="Require a selfie photo during clock-in/out.",
    )
    require_liveness = models.BooleanField(
        default=True,
        help_text="Require liveness detection for biometric verification.",
    )

    # Location requirements
    require_gps = models.BooleanField(
        default=True,
        help_text="Require GPS coordinates during clock-in/out.",
    )
    require_geofence = models.BooleanField(
        default=True,
        help_text="Require employee to be within an assigned geofence.",
    )

    # Network requirements
    require_wifi = models.BooleanField(
        default=False,
        help_text="Require connection to a registered WiFi network.",
    )

    # Device requirements
    require_device_registered = models.BooleanField(
        default=True,
        help_text="Require the device to be registered for this employee.",
    )

    # Offline settings
    max_offline_per_shift = models.PositiveIntegerField(
        default=1,
        help_text="Maximum offline attendance records allowed per shift.",
    )

    # Time window settings
    allow_early_clockin_minutes = models.IntegerField(
        default=30,
        help_text="Minutes before shift start that clock-in is allowed.",
    )
    allow_late_clockout_minutes = models.IntegerField(
        default=30,
        help_text="Minutes after shift end that clock-out is allowed.",
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta(TenantBaseModel.Meta):
        verbose_name = "Attendance Policy"
        verbose_name_plural = "Attendance Policies"
        unique_together = [("tenant", "name")]
        ordering = ["name"]

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Geofence
# ---------------------------------------------------------------------------
class Geofence(TenantBaseModel):
    """Geographic boundary for attendance location validation."""

    name = models.CharField(max_length=255)
    name_ar = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Name (Arabic)",
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        help_text="Center latitude of the geofence.",
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        help_text="Center longitude of the geofence.",
    )
    radius_meters = models.PositiveIntegerField(
        help_text="Radius of the geofence in meters.",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    description = models.TextField(blank=True, default="")

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta(TenantBaseModel.Meta):
        verbose_name = "Geofence"
        verbose_name_plural = "Geofences"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.latitude}, {self.longitude} r={self.radius_meters}m)"


# ---------------------------------------------------------------------------
# WiFi Policy
# ---------------------------------------------------------------------------
class WifiPolicy(TenantBaseModel):
    """Registered WiFi network used for attendance location verification."""

    name = models.CharField(max_length=255)
    ssid = models.CharField(
        max_length=100,
        help_text="WiFi network SSID (name).",
    )
    bssid = models.CharField(
        max_length=17,
        blank=True,
        default="",
        help_text="WiFi access point BSSID (MAC address). Optional.",
    )
    geofence = models.ForeignKey(
        Geofence,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wifi_policies",
        help_text="Optional geofence linked to this WiFi network.",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta(TenantBaseModel.Meta):
        verbose_name = "WiFi Policy"
        verbose_name_plural = "WiFi Policies"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.ssid})"


# ---------------------------------------------------------------------------
# Attendance Record
# ---------------------------------------------------------------------------
class AttendanceRecord(TenantBaseModel):
    """Core attendance record capturing clock-in/out with full validation data."""

    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        LATE = "LATE", "Late"
        EARLY_DEPARTURE = "EARLY_DEPARTURE", "Early Departure"
        HALF_DAY = "HALF_DAY", "Half Day"
        ON_LEAVE = "ON_LEAVE", "On Leave"

    # Core relations
    employee = models.ForeignKey(
        "accounts.Employee",
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    shift = models.ForeignKey(
        Shift,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    policy = models.ForeignKey(
        AttendancePolicy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_records",
    )
    date = models.DateField(db_index=True)

    # Clock times
    clock_in_time = models.DateTimeField(null=True, blank=True)
    clock_out_time = models.DateTimeField(null=True, blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PRESENT,
        db_index=True,
    )

    # Clock-in GPS
    clock_in_latitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    clock_in_longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )

    # Clock-out GPS
    clock_out_latitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    clock_out_longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )

    # Selfie images
    clock_in_selfie = models.ImageField(
        upload_to="attendance/selfies/",
        null=True,
        blank=True,
    )
    clock_out_selfie = models.ImageField(
        upload_to="attendance/selfies/",
        null=True,
        blank=True,
    )

    # Device info
    clock_in_device = models.ForeignKey(
        "devices.DeviceRegistry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_records",
    )

    # WiFi info
    clock_in_wifi_ssid = models.CharField(max_length=100, blank=True, default="")
    clock_in_wifi_bssid = models.CharField(max_length=17, blank=True, default="")

    # Offline sync
    is_offline_record = models.BooleanField(
        default=False,
        help_text="Whether this record was created offline and synced later.",
    )
    offline_integrity_hash = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="SHA-256 hash for verifying offline record integrity.",
    )

    # Validation state
    is_validated = models.BooleanField(
        default=False,
        help_text="Whether the record has passed server-side validation.",
    )
    validation_errors = models.JSONField(
        default=list,
        blank=True,
        help_text="List of validation error messages.",
    )
    is_synced = models.BooleanField(
        default=True,
        help_text="Whether the record has been synced to the server.",
    )

    # Biometric verification results
    liveness_passed = models.BooleanField(
        default=False,
        help_text="Whether liveness detection passed.",
    )
    face_match_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Face recognition match confidence score (0-1).",
    )

    # GPS accuracy and geofence
    gps_accuracy = models.FloatField(
        null=True,
        blank=True,
        help_text="GPS accuracy in meters as reported by the device.",
    )
    geofence = models.ForeignKey(
        Geofence,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_records",
    )
    geofence_valid = models.BooleanField(
        default=False,
        help_text="Whether the employee was within the assigned geofence.",
    )

    # WiFi validation
    wifi_valid = models.BooleanField(
        default=False,
        help_text="Whether the WiFi network matched the policy.",
    )

    # Device validation
    device_valid = models.BooleanField(
        default=False,
        help_text="Whether the device was registered for this employee.",
    )

    # Tamper detection
    clock_skew_detected = models.BooleanField(
        default=False,
        help_text="Whether a significant clock skew was detected.",
    )
    client_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp reported by the client device.",
    )

    # Notes
    notes = models.TextField(blank=True, default="")

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta(TenantBaseModel.Meta):
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"
        unique_together = [("tenant", "employee", "date", "shift")]
        ordering = ["-date", "-clock_in_time"]
        indexes = [
            models.Index(
                fields=["tenant", "date"],
                name="idx_attendance_tenant_date",
            ),
            models.Index(
                fields=["employee", "date"],
                name="idx_attendance_employee_date",
            ),
            models.Index(
                fields=["tenant", "employee", "date"],
                name="idx_attendance_tenant_emp_date",
            ),
            models.Index(
                fields=["tenant", "status", "date"],
                name="idx_attendance_tenant_status",
            ),
            models.Index(
                fields=["tenant", "date", "is_validated"],
                name="idx_attendance_validated",
            ),
            models.Index(
                fields=["is_offline_record", "is_synced"],
                name="idx_attendance_offline_sync",
            ),
        ]

    def __str__(self):
        return (
            f"{self.employee} - {self.date} - {self.shift.name} - {self.status}"
        )

    @property
    def duration(self):
        """Calculate the duration between clock-in and clock-out."""
        if self.clock_in_time and self.clock_out_time:
            return self.clock_out_time - self.clock_in_time
        return None

    @property
    def duration_hours(self):
        """Return the duration as a float of hours."""
        d = self.duration
        if d is not None:
            return d.total_seconds() / 3600.0
        return None


# ---------------------------------------------------------------------------
# Attendance Correction Request
# ---------------------------------------------------------------------------
class AttendanceCorrectionRequest(TenantBaseModel):
    """Employee-submitted request to correct an attendance record."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    attendance_record = models.ForeignKey(
        AttendanceRecord,
        on_delete=models.CASCADE,
        related_name="correction_requests",
    )
    employee = models.ForeignKey(
        "accounts.Employee",
        on_delete=models.CASCADE,
        related_name="correction_requests",
    )
    reason = models.TextField(
        help_text="Employee's reason for requesting the correction.",
    )
    requested_clock_in = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Corrected clock-in time requested by the employee.",
    )
    requested_clock_out = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Corrected clock-out time requested by the employee.",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_corrections",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes from the reviewer.",
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta(TenantBaseModel.Meta):
        verbose_name = "Attendance Correction Request"
        verbose_name_plural = "Attendance Correction Requests"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Correction for {self.employee} on "
            f"{self.attendance_record.date} - {self.status}"
        )
