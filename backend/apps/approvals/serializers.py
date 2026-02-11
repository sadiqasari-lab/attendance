"""Serializers for the approvals app."""
from rest_framework import serializers

from .models import ApprovalRequest


class ApprovalRequestSerializer(serializers.ModelSerializer):
    """
    Read-oriented serializer for ApprovalRequest.

    Includes nested read-only requester and reviewer information so
    that consumers do not need additional API calls for display names.
    """

    requester_name = serializers.SerializerMethodField()
    requester_employee_id = serializers.CharField(
        source="requester.employee_id", read_only=True
    )
    reviewer_name = serializers.SerializerMethodField()
    request_type_display = serializers.CharField(
        source="get_request_type_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )

    class Meta:
        model = ApprovalRequest
        fields = [
            "id",
            "tenant",
            "request_type",
            "request_type_display",
            "requester",
            "requester_name",
            "requester_employee_id",
            "status",
            "status_display",
            "title",
            "description",
            "metadata",
            "reviewed_by",
            "reviewer_name",
            "reviewed_at",
            "review_notes",
            "priority",
            "priority_display",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "tenant",
            "requester",
            "status",
            "reviewed_by",
            "reviewed_at",
            "review_notes",
            "created_at",
            "updated_at",
            "created_by",
        ]

    def get_requester_name(self, obj) -> str:
        """Return the requester's full name via their linked user."""
        return obj.requester.user.full_name

    def get_reviewer_name(self, obj) -> str | None:
        """Return the reviewer's full name, or None if not yet reviewed."""
        if obj.reviewed_by:
            return obj.reviewed_by.full_name
        return None


class ApprovalRequestCreateSerializer(serializers.ModelSerializer):
    """
    Write-oriented serializer used when creating a new approval request.

    Intentionally limits the writeable fields to those that a requester
    is allowed to set.  Status, reviewer, and audit fields are managed
    by the system.
    """

    class Meta:
        model = ApprovalRequest
        fields = [
            "id",
            "request_type",
            "title",
            "description",
            "metadata",
            "priority",
        ]
        read_only_fields = ["id"]

    def validate_metadata(self, value):
        """Ensure metadata is a dictionary."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Metadata must be a JSON object.")
        return value


class ApprovalActionSerializer(serializers.Serializer):
    """
    Serializer for the approve / reject custom actions.

    Only ``review_notes`` is accepted; the action itself (approve or
    reject) is determined by the URL endpoint invoked.
    """

    review_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Optional notes from the reviewer explaining the decision.",
    )
