"""Serializers for the projects app."""
from rest_framework import serializers

from apps.accounts.models import Employee

from .models import EmployeeProjectAssignment, Project


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for the Project model.

    Includes a read-only ``assignment_count`` that reflects the number
    of active employee assignments linked to this project.
    """

    assignment_count = serializers.IntegerField(read_only=True, source="assignment_count_annotation", default=0)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "tenant",
            "name",
            "name_ar",
            "description",
            "location_name",
            "latitude",
            "longitude",
            "geofence",
            "start_date",
            "end_date",
            "is_active",
            "status",
            "status_display",
            "assignment_count",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "tenant",
            "created_at",
            "updated_at",
            "created_by",
        ]

    def validate(self, attrs):
        """Ensure end_date is not before start_date when both are provided."""
        start = attrs.get("start_date") or (self.instance and self.instance.start_date)
        end = attrs.get("end_date") or (self.instance and self.instance.end_date)
        if start and end and end < start:
            raise serializers.ValidationError(
                {"end_date": "End date cannot be earlier than start date."}
            )
        return attrs


class EmployeeProjectAssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer for the EmployeeProjectAssignment model.

    Provides nested read-only representations of the related employee
    and project names for convenient display in list / detail views.
    """

    employee_name = serializers.SerializerMethodField()
    employee_id_display = serializers.CharField(
        source="employee.employee_id", read_only=True
    )
    project_name = serializers.CharField(
        source="project.name", read_only=True
    )
    role_display = serializers.CharField(
        source="get_role_display", read_only=True
    )

    class Meta:
        model = EmployeeProjectAssignment
        fields = [
            "id",
            "tenant",
            "employee",
            "employee_name",
            "employee_id_display",
            "project",
            "project_name",
            "role",
            "role_display",
            "start_date",
            "end_date",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "tenant",
            "created_at",
            "updated_at",
            "created_by",
        ]

    def get_employee_name(self, obj) -> str:
        """Return the employee's full name via their linked user."""
        return obj.employee.user.full_name

    def validate(self, attrs):
        """
        Cross-field validations:
        - end_date must not precede start_date.
        - employee must belong to the same tenant as the project.
        """
        start = attrs.get("start_date") or (self.instance and self.instance.start_date)
        end = attrs.get("end_date") or (self.instance and self.instance.end_date)
        if start and end and end < start:
            raise serializers.ValidationError(
                {"end_date": "End date cannot be earlier than start date."}
            )

        employee = attrs.get("employee") or (self.instance and self.instance.employee)
        project = attrs.get("project") or (self.instance and self.instance.project)
        if employee and project and employee.tenant_id != project.tenant_id:
            raise serializers.ValidationError(
                "Employee and project must belong to the same tenant."
            )

        return attrs
