"""Tests for the projects app."""
from datetime import date

import pytest

from apps.projects.models import EmployeeProjectAssignment, Project


class TestProjectModel:
    @pytest.mark.django_db
    def test_project_creation(self, tenant, geofence):
        project = Project.objects.create(
            tenant=tenant,
            name="Office Renovation",
            geofence=geofence,
            is_active=True,
        )
        assert project.geofence == geofence
        assert project.is_active is True


class TestProjectAssignment:
    @pytest.mark.django_db
    def test_assign_employee(self, tenant, employee, geofence):
        project = Project.objects.create(
            tenant=tenant,
            name="Test Project",
        )
        assignment = EmployeeProjectAssignment.objects.create(
            tenant=tenant,
            project=project,
            employee=employee,
            role="WORKER",
            start_date=date.today(),
        )
        assert assignment.project == project
        assert assignment.employee == employee
