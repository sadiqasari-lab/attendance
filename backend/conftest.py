"""Shared test fixtures for the Inspire Attendance System."""
import uuid
from datetime import time
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.accounts.models import Employee, User
from apps.attendance.models import (
    AttendancePolicy,
    AttendanceRecord,
    Geofence,
    Shift,
    WifiPolicy,
)
from apps.biometric.models import BiometricTemplate
from apps.devices.models import DeviceRegistry
from apps.tenants.models import Department, Group, Tenant


@pytest.fixture
def group(db):
    return Group.objects.create(
        name="Arab Inspire Company",
        name_ar="شركة عرب إنسباير",
    )


@pytest.fixture
def tenant(db, group):
    return Tenant.objects.create(
        group=group,
        name="Abu Waleed Tea Franchise",
        name_ar="فرانشايز أبو وليد للشاي",
        slug="abuwaleed",
        is_active=True,
    )


@pytest.fixture
def tenant_b(db, group):
    return Tenant.objects.create(
        group=group,
        name="Elham Al Arab Office",
        name_ar="مكتب إلهام العرب",
        slug="unaiza",
        is_active=True,
    )


@pytest.fixture
def department(db, tenant):
    return Department.objects.create(
        tenant=tenant,
        name="Operations",
        name_ar="العمليات",
    )


@pytest.fixture
def super_admin(db):
    return User.objects.create_superuser(
        email="admin@arabinspire.cloud",
        password="SuperSecure123!",
        first_name="Super",
        last_name="Admin",
    )


@pytest.fixture
def tenant_admin_user(db):
    return User.objects.create_user(
        email="tenantadmin@arabinspire.cloud",
        password="TenantAdmin123!",
        first_name="Tenant",
        last_name="Admin",
        role="TENANT_ADMIN",
    )


@pytest.fixture
def employee_user(db):
    return User.objects.create_user(
        email="employee@arabinspire.cloud",
        password="Employee123!",
        first_name="Ahmed",
        last_name="Hassan",
        role="EMPLOYEE",
    )


@pytest.fixture
def employee_user_b(db):
    return User.objects.create_user(
        email="employee_b@arabinspire.cloud",
        password="Employee123!",
        first_name="Fatima",
        last_name="Ali",
        role="EMPLOYEE",
    )


@pytest.fixture
def employee(db, tenant, employee_user, department):
    return Employee.objects.create(
        tenant=tenant,
        user=employee_user,
        employee_id="EMP001",
        department=department,
        designation="Engineer",
        is_active=True,
    )


@pytest.fixture
def employee_b(db, tenant_b, employee_user_b):
    return Employee.objects.create(
        tenant=tenant_b,
        user=employee_user_b,
        employee_id="EMP002",
        designation="Analyst",
        is_active=True,
    )


@pytest.fixture
def tenant_admin_employee(db, tenant, tenant_admin_user):
    return Employee.objects.create(
        tenant=tenant,
        user=tenant_admin_user,
        employee_id="ADM001",
        designation="Admin",
        is_active=True,
    )


@pytest.fixture
def shift(db, tenant):
    return Shift.objects.create(
        tenant=tenant,
        name="Morning Shift",
        name_ar="الوردية الصباحية",
        start_time=time(8, 0),
        end_time=time(16, 0),
        grace_period_minutes=15,
        is_overnight=False,
        is_active=True,
    )


@pytest.fixture
def attendance_policy(db, tenant):
    return AttendancePolicy.objects.create(
        tenant=tenant,
        name="Default Policy",
        require_selfie=True,
        require_liveness=True,
        require_gps=True,
        require_geofence=True,
        require_wifi=False,
        require_device_registered=True,
        max_offline_per_shift=1,
    )


@pytest.fixture
def geofence(db, tenant):
    return Geofence.objects.create(
        tenant=tenant,
        name="HQ Office",
        name_ar="المقر الرئيسي",
        latitude=Decimal("24.7136000"),
        longitude=Decimal("46.6753000"),
        radius_meters=200,
        is_active=True,
    )


@pytest.fixture
def wifi_policy(db, tenant, geofence):
    return WifiPolicy.objects.create(
        tenant=tenant,
        name="Office WiFi",
        ssid="ArabInspire-Corp",
        bssid="AA:BB:CC:DD:EE:FF",
        geofence=geofence,
        is_active=True,
    )


@pytest.fixture
def device(db, tenant, employee):
    return DeviceRegistry.objects.create(
        tenant=tenant,
        employee=employee,
        device_type=DeviceRegistry.DeviceType.COMPANY,
        platform=DeviceRegistry.Platform.ANDROID,
        device_identifier="test-device-id-12345",
        device_model="Samsung Galaxy S23",
        device_manufacturer="Samsung",
        os_version="14",
        status=DeviceRegistry.Status.ACTIVE,
    )


@pytest.fixture
def attendance_record(db, tenant, employee, shift):
    return AttendanceRecord.objects.create(
        tenant=tenant,
        employee=employee,
        shift=shift,
        date=timezone.localdate(),
        clock_in_time=timezone.now(),
        status=AttendanceRecord.Status.PRESENT,
        is_validated=True,
    )


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, employee_user):
    api_client.force_authenticate(user=employee_user)
    return api_client


@pytest.fixture
def admin_client(api_client, super_admin):
    api_client.force_authenticate(user=super_admin)
    return api_client


@pytest.fixture
def tenant_admin_client(api_client, tenant_admin_user):
    api_client.force_authenticate(user=tenant_admin_user)
    return api_client
