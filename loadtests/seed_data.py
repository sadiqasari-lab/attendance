"""
Seed script to create load test data in the database.

Run before load testing:
    cd backend && python manage.py shell < ../loadtests/seed_data.py
"""
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from datetime import time, date
from apps.tenants.models import Group, Tenant, Department
from apps.accounts.models import User, Employee
from apps.attendance.models import Shift, AttendancePolicy, Geofence, WifiPolicy

USER_COUNT = 500
TENANT_SLUG = "loadtest-tenant"
USER_PASSWORD = "LoadTest123!"

print("=== Inspire Attendance Load Test Data Seeder ===\n")

# 1. Create Group
group, created = Group.objects.get_or_create(
    name="Load Test Group",
    defaults={"is_active": True},
)
print(f"{'Created' if created else 'Found'} group: {group.name}")

# 2. Create Tenant
tenant, created = Tenant.objects.get_or_create(
    slug=TENANT_SLUG,
    defaults={
        "name": "Load Test Tenant",
        "group": group,
        "is_active": True,
        "settings": {},
    },
)
print(f"{'Created' if created else 'Found'} tenant: {tenant.slug}")

# 3. Create Department
dept, created = Department.objects.get_or_create(
    name="Load Test Department",
    tenant=tenant,
    defaults={"is_active": True},
)
print(f"{'Created' if created else 'Found'} department: {dept.name}")

# 4. Create Shift
shift, created = Shift.objects.get_or_create(
    name="Load Test Shift",
    tenant=tenant,
    defaults={
        "start_time": time(8, 0),
        "end_time": time(17, 0),
        "grace_period_minutes": 15,
        "is_night_shift": False,
        "is_active": True,
    },
)
print(f"{'Created' if created else 'Found'} shift: {shift.name} (ID: {shift.id})")

# 5. Create Attendance Policy
policy, created = AttendancePolicy.objects.get_or_create(
    name="Load Test Policy",
    tenant=tenant,
    defaults={
        "require_selfie": False,  # Disable for load testing
        "require_liveness": False,
        "require_face_match": False,
        "require_gps": True,
        "detect_fake_gps": False,
        "require_geofence": True,
        "require_wifi": False,
        "require_device_registration": False,
        "prevent_duplicate": True,
        "enforce_shift_timing": False,
        "detect_clock_tampering": False,
        "allow_offline": True,
        "is_active": True,
    },
)
print(f"{'Created' if created else 'Found'} policy: {policy.name}")

# 6. Create Geofence (Riyadh office)
geofence, created = Geofence.objects.get_or_create(
    name="Load Test Office",
    tenant=tenant,
    defaults={
        "latitude": 24.7136,
        "longitude": 46.6753,
        "radius_meters": 500,
        "is_active": True,
    },
)
print(f"{'Created' if created else 'Found'} geofence: {geofence.name}")

# 7. Create test users and employees
created_count = 0
existing_count = 0

for i in range(1, USER_COUNT + 1):
    email = f"loadtest_user_{i}@test.com"
    user, user_created = User.objects.get_or_create(
        email=email,
        defaults={
            "first_name": f"LoadTest",
            "last_name": f"User{i}",
            "role": "EMPLOYEE",
            "is_active": True,
        },
    )
    if user_created:
        user.set_password(USER_PASSWORD)
        user.save()

    emp, emp_created = Employee.objects.get_or_create(
        user=user,
        tenant=tenant,
        defaults={
            "employee_id": f"LT{i:04d}",
            "department": dept,
            "designation": "Load Test Employee",
            "date_of_joining": date(2024, 1, 1),
            "is_active": True,
        },
    )

    if user_created:
        created_count += 1
    else:
        existing_count += 1

    if i % 100 == 0:
        print(f"  Processed {i}/{USER_COUNT} users...")

print(f"\nUsers: {created_count} created, {existing_count} already existed")
print(f"\n=== Seed complete ===")
print(f"Tenant slug: {TENANT_SLUG}")
print(f"Shift ID: {shift.id}")
print(f"Users: loadtest_user_1@test.com ... loadtest_user_{USER_COUNT}@test.com")
print(f"Password: {USER_PASSWORD}")
