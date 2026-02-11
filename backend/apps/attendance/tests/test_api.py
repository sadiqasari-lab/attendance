"""Tests for attendance API endpoints."""
import pytest
from django.utils import timezone

from apps.attendance.models import AttendanceRecord


class TestShiftAPI:
    @pytest.mark.django_db
    def test_list_shifts(self, tenant_admin_client, tenant, shift, tenant_admin_employee):
        response = tenant_admin_client.get(f"/api/v1/{tenant.slug}/attendance/shifts/")
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_create_shift(self, tenant_admin_client, tenant, tenant_admin_employee):
        response = tenant_admin_client.post(
            f"/api/v1/{tenant.slug}/attendance/shifts/",
            {
                "name": "Evening Shift",
                "start_time": "16:00:00",
                "end_time": "00:00:00",
                "grace_period_minutes": 10,
                "is_overnight": True,
                "is_active": True,
            },
        )
        assert response.status_code == 201

    @pytest.mark.django_db
    def test_create_shift_unauthorized(self, authenticated_client, tenant, employee):
        response = authenticated_client.post(
            f"/api/v1/{tenant.slug}/attendance/shifts/",
            {"name": "Night Shift", "start_time": "22:00:00", "end_time": "06:00:00"},
        )
        assert response.status_code == 403


class TestGeofenceAPI:
    @pytest.mark.django_db
    def test_list_geofences(self, tenant_admin_client, tenant, geofence, tenant_admin_employee):
        response = tenant_admin_client.get(f"/api/v1/{tenant.slug}/attendance/geofences/")
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_create_geofence(self, tenant_admin_client, tenant, tenant_admin_employee):
        response = tenant_admin_client.post(
            f"/api/v1/{tenant.slug}/attendance/geofences/",
            {
                "name": "Branch Office",
                "latitude": "26.3260000",
                "longitude": "43.9750000",
                "radius_meters": 150,
                "is_active": True,
            },
        )
        assert response.status_code == 201


class TestAttendanceRecordAPI:
    @pytest.mark.django_db
    def test_list_records(self, authenticated_client, tenant, employee, attendance_record):
        response = authenticated_client.get(
            f"/api/v1/{tenant.slug}/attendance/records/"
        )
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_records_filtered_by_date(self, authenticated_client, tenant, employee, attendance_record):
        today = str(timezone.localdate())
        response = authenticated_client.get(
            f"/api/v1/{tenant.slug}/attendance/records/?date_from={today}&date_to={today}"
        )
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_employee_sees_only_own_records(
        self, api_client, tenant, employee, employee_b, attendance_record, employee_user_b
    ):
        """Employee B should not see Employee A's records."""
        # Create employee B in same tenant for this test
        from apps.accounts.models import Employee
        emp_b_same_tenant = Employee.objects.create(
            tenant=tenant,
            user=employee_user_b,
            employee_id="EMP-B-SAME",
            is_active=True,
        )
        api_client.force_authenticate(user=employee_user_b)
        response = api_client.get(f"/api/v1/{tenant.slug}/attendance/records/")
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", data.get("data", []))
        # Employee B should see 0 records (only A has records)
        for r in results:
            assert r.get("employee") != str(employee.id)


class TestAttendanceSummaryAPI:
    @pytest.mark.django_db
    def test_summary_endpoint(self, authenticated_client, tenant, employee, attendance_record):
        response = authenticated_client.get(
            f"/api/v1/{tenant.slug}/attendance/summary/"
        )
        assert response.status_code == 200
