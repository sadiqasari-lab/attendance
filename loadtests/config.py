"""Load test configuration for Inspire Attendance System."""

# Target host
HOST = "http://localhost:8000"

# Tenant used for load testing
TENANT_SLUG = "loadtest-tenant"

# Pre-seeded test users (email pattern: loadtest_user_{n}@test.com, password: LoadTest123!)
# The seed script creates these before running tests.
USER_COUNT = 500
USER_EMAIL_PATTERN = "loadtest_user_{n}@test.com"
USER_PASSWORD = "LoadTest123!"

# Pre-seeded shift ID (created by seed script)
SHIFT_ID = None  # Set dynamically after login

# API paths
AUTH_LOGIN = "/api/v1/auth/login/"
AUTH_REFRESH = "/api/v1/auth/token/refresh/"
AUTH_PROFILE = "/api/v1/auth/profile/"

ATTENDANCE_SHIFTS = "/{slug}/attendance/shifts/"
ATTENDANCE_RECORDS = "/{slug}/attendance/records/"
ATTENDANCE_CLOCK_IN = "/{slug}/attendance/clock-in/"
ATTENDANCE_CLOCK_OUT = "/{slug}/attendance/clock-out/"
ATTENDANCE_SUMMARY = "/{slug}/attendance/summary/"

DEVICES_REGISTER = "/{slug}/devices/register/"

INTEGRATION_LOGS = "/api/v1/integration/pull/attendance-logs/"

# WebSocket
WS_MAP = "ws://localhost:8000/ws/{slug}/attendance/map/"

# Fake GPS coordinates (Riyadh office area)
OFFICE_LAT = 24.7136
OFFICE_LNG = 46.6753
GPS_ACCURACY = 10.0

# Thresholds (for pass/fail criteria)
P95_RESPONSE_TIME_MS = 500  # 95th percentile under 500ms
ERROR_RATE_THRESHOLD = 0.01  # Less than 1% error rate
