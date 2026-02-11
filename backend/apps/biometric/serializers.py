"""Serializers for the biometric app."""
from rest_framework import serializers

from .models import BiometricEnrollmentLog, BiometricTemplate


class BiometricTemplateSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source="employee.user.get_full_name", read_only=True
    )

    class Meta:
        model = BiometricTemplate
        fields = [
            "id", "employee", "employee_name", "embedding_version",
            "num_images_used", "status", "enrolled_at",
            "quality_score", "created_at", "updated_at",
        ]
        read_only_fields = fields  # All read-only — templates are managed via services


class BiometricEnrollSerializer(serializers.Serializer):
    """Serializer for biometric enrollment request."""
    images = serializers.ListField(
        child=serializers.ImageField(),
        min_length=3,
        max_length=10,
        help_text="List of face images for enrollment (minimum 3).",
    )
    liveness_passed = serializers.BooleanField(
        help_text="Whether liveness challenge was passed on client.",
    )


class BiometricVerifySerializer(serializers.Serializer):
    """Serializer for biometric verification request."""
    image = serializers.ImageField(help_text="Face image to verify.")


class BiometricVerifyResponseSerializer(serializers.Serializer):
    match = serializers.BooleanField()
    score = serializers.FloatField()


class BiometricEnrollmentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiometricEnrollmentLog
        fields = [
            "id", "employee", "template", "event", "details", "created_at",
        ]
        read_only_fields = fields
