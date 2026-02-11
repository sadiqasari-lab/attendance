"""
Inspire Attendance System — Load Tests (Locust)

Target: 500 concurrent users with <500ms p95 response time and <1% error rate.

Usage:
    # Seed test data first
    cd backend && python manage.py shell < ../loadtests/seed_data.py

    # Run headless (500 users, ramp 50/s)
    cd loadtests
    locust -f locustfile.py --headless \
        -u 500 -r 50 --run-time 5m \
        --host http://localhost:8000 \
        --csv results

    # Run with web UI
    locust -f locustfile.py --host http://localhost:8000
"""

import json
import random
import time as time_module
from datetime import datetime, date

from locust import HttpUser, task, between, events, tag
from locust.exception import StopUser
import websocket

from config import (
    TENANT_SLUG,
    USER_COUNT,
    USER_PASSWORD,
    AUTH_LOGIN,
    AUTH_REFRESH,
    AUTH_PROFILE,
    ATTENDANCE_SHIFTS,
    ATTENDANCE_RECORDS,
    ATTENDANCE_CLOCK_IN,
    ATTENDANCE_CLOCK_OUT,
    ATTENDANCE_SUMMARY,
    DEVICES_REGISTER,
    OFFICE_LAT,
    OFFICE_LNG,
    GPS_ACCURACY,
    WS_MAP,
    P95_RESPONSE_TIME_MS,
    ERROR_RATE_THRESHOLD,
)

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def tenant_url(path: str) -> str:
    """Replace {slug} placeholder with tenant slug."""
    return path.replace("{slug}", TENANT_SLUG)


def jitter_coords(lat: float, lng: float, meters: int = 200) -> tuple:
    """Add random jitter to GPS coordinates within a radius."""
    # ~0.00001 degrees ≈ 1.1 meters
    offset = meters * 0.00001 / 1.1
    return (
        lat + random.uniform(-offset, offset),
        lng + random.uniform(-offset, offset),
    )


def fake_selfie_base64() -> str:
    """Return a minimal valid base64 string (1x1 white PNG) for selfie field."""
    return (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
        "nGP4z8BQDwAEgAF/pooBPQAAAABJRU5ErkJggg=="
    )


# ─────────────────────────────────────────────
# User class counter for unique user assignment
# ─────────────────────────────────────────────
_user_counter = 0


def next_user_index() -> int:
    global _user_counter
    _user_counter += 1
    idx = _user_counter % USER_COUNT
    return idx if idx > 0 else USER_COUNT


# ─────────────────────────────────────────────
# Main User Behavior
# ─────────────────────────────────────────────

class AttendanceUser(HttpUser):
    """
    Simulates an employee using the attendance system:
    1. Logs in
    2. Views shifts and dashboard
    3. Clocks in
    4. Checks attendance records
    5. Clocks out
    6. Views summary
    """

    wait_time = between(1, 5)

    # Track state
    access_token: str = ""
    refresh_token: str = ""
    user_email: str = ""
    user_index: int = 0
    shift_id: str = ""
    attendance_id: str = ""
    has_clocked_in: bool = False

    def on_start(self):
        """Authenticate on spawn."""
        self.user_index = next_user_index()
        self.user_email = f"loadtest_user_{self.user_index}@test.com"
        self._login()

    def _login(self):
        """Authenticate and store tokens."""
        with self.client.post(
            AUTH_LOGIN,
            json={"email": self.user_email, "password": USER_PASSWORD},
            name="POST /auth/login",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self.access_token = data.get("access", "")
                self.refresh_token = data.get("refresh", "")
                if not self.access_token:
                    resp.failure("No access token in response")
            else:
                resp.failure(f"Login failed: {resp.status_code}")
                raise StopUser()

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"}

    # ── Auth Tasks ──────────────────────────

    @tag("auth")
    @task(1)
    def refresh_token_task(self):
        """Refresh JWT access token."""
        with self.client.post(
            AUTH_REFRESH,
            json={"refresh": self.refresh_token},
            name="POST /auth/token/refresh",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self.access_token = data.get("access", self.access_token)
            else:
                # Token expired, re-login
                self._login()

    @tag("auth")
    @task(2)
    def get_profile(self):
        """Fetch user profile."""
        self.client.get(
            AUTH_PROFILE,
            headers=self._headers(),
            name="GET /auth/profile",
        )

    # ── Attendance Read Tasks ───────────────

    @tag("attendance", "read")
    @task(5)
    def list_shifts(self):
        """List available shifts."""
        url = tenant_url(ATTENDANCE_SHIFTS)
        with self.client.get(
            url,
            headers=self._headers(),
            name="GET /{tenant}/attendance/shifts",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results and not self.shift_id:
                    self.shift_id = results[0].get("id", "")
            elif resp.status_code == 401:
                self._login()

    @tag("attendance", "read")
    @task(4)
    def list_records(self):
        """List attendance records with date filtering."""
        url = tenant_url(ATTENDANCE_RECORDS)
        today = date.today().isoformat()
        self.client.get(
            url,
            headers=self._headers(),
            params={"start_date": today, "end_date": today},
            name="GET /{tenant}/attendance/records",
        )

    @tag("attendance", "read")
    @task(3)
    def get_summary(self):
        """Fetch attendance summary."""
        url = tenant_url(ATTENDANCE_SUMMARY)
        today = date.today().isoformat()
        first_of_month = date.today().replace(day=1).isoformat()
        self.client.get(
            url,
            headers=self._headers(),
            params={"start_date": first_of_month, "end_date": today},
            name="GET /{tenant}/attendance/summary",
        )

    # ── Clock In/Out Tasks ──────────────────

    @tag("attendance", "write")
    @task(3)
    def clock_in(self):
        """Clock in with selfie and GPS data."""
        if self.has_clocked_in or not self.shift_id:
            return

        lat, lng = jitter_coords(OFFICE_LAT, OFFICE_LNG)
        url = tenant_url(ATTENDANCE_CLOCK_IN)

        payload = {
            "shift_id": self.shift_id,
            "selfie": fake_selfie_base64(),
            "latitude": lat,
            "longitude": lng,
            "gps_accuracy": GPS_ACCURACY,
            "device_id": f"loadtest-device-{self.user_index}",
            "liveness_score": round(random.uniform(0.85, 0.99), 2),
            "face_match_score": round(random.uniform(0.80, 0.98), 2),
            "client_timestamp": datetime.now().isoformat(),
            "is_mock_location": False,
        }

        with self.client.post(
            url,
            json=payload,
            headers=self._headers(),
            name="POST /{tenant}/attendance/clock-in",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 201):
                data = resp.json()
                self.attendance_id = data.get("id", "")
                self.has_clocked_in = True
            elif resp.status_code == 422:
                # Validation error (e.g., duplicate) — not a failure
                resp.success()
                self.has_clocked_in = True
            elif resp.status_code == 401:
                self._login()

    @tag("attendance", "write")
    @task(2)
    def clock_out(self):
        """Clock out with selfie and GPS."""
        if not self.has_clocked_in or not self.attendance_id:
            return

        lat, lng = jitter_coords(OFFICE_LAT, OFFICE_LNG)
        url = tenant_url(ATTENDANCE_CLOCK_OUT)

        payload = {
            "attendance_id": self.attendance_id,
            "selfie": fake_selfie_base64(),
            "latitude": lat,
            "longitude": lng,
            "gps_accuracy": GPS_ACCURACY,
            "client_timestamp": datetime.now().isoformat(),
        }

        with self.client.post(
            url,
            json=payload,
            headers=self._headers(),
            name="POST /{tenant}/attendance/clock-out",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 201):
                self.has_clocked_in = False
                self.attendance_id = ""
            elif resp.status_code == 422:
                resp.success()
                self.has_clocked_in = False
            elif resp.status_code == 401:
                self._login()


# ─────────────────────────────────────────────
# WebSocket User (Map)
# ─────────────────────────────────────────────

class MapWebSocketUser(HttpUser):
    """
    Simulates employees connecting to the real-time attendance map WebSocket.
    ~10% of users will maintain a WebSocket connection.
    """

    wait_time = between(5, 15)
    weight = 1  # 1:10 ratio with AttendanceUser

    access_token: str = ""
    user_index: int = 0
    ws: websocket.WebSocket = None

    def on_start(self):
        self.user_index = next_user_index()
        email = f"loadtest_user_{self.user_index}@test.com"

        # Login to get token
        resp = self.client.post(
            AUTH_LOGIN,
            json={"email": email, "password": USER_PASSWORD},
            name="POST /auth/login (ws)",
        )
        if resp.status_code == 200:
            self.access_token = resp.json().get("access", "")
        else:
            raise StopUser()

        self._connect_ws()

    def _connect_ws(self):
        """Establish WebSocket connection to attendance map."""
        ws_url = WS_MAP.replace("{slug}", TENANT_SLUG)
        start = time_module.time()
        try:
            self.ws = websocket.create_connection(
                ws_url,
                header=[f"Authorization: Bearer {self.access_token}"],
                timeout=10,
            )
            elapsed = (time_module.time() - start) * 1000
            events.request.fire(
                request_type="WSConnect",
                name="WS /{tenant}/attendance/map",
                response_time=elapsed,
                response_length=0,
                exception=None,
                context={},
            )
        except Exception as e:
            elapsed = (time_module.time() - start) * 1000
            events.request.fire(
                request_type="WSConnect",
                name="WS /{tenant}/attendance/map",
                response_time=elapsed,
                response_length=0,
                exception=e,
                context={},
            )
            self.ws = None

    @task
    def receive_map_update(self):
        """Listen for WebSocket messages."""
        if not self.ws:
            return

        start = time_module.time()
        try:
            self.ws.settimeout(2)
            msg = self.ws.recv()
            elapsed = (time_module.time() - start) * 1000
            events.request.fire(
                request_type="WSRecv",
                name="WS recv map update",
                response_time=elapsed,
                response_length=len(msg) if msg else 0,
                exception=None,
                context={},
            )
        except websocket.WebSocketTimeoutException:
            # No message available — normal
            pass
        except Exception as e:
            elapsed = (time_module.time() - start) * 1000
            events.request.fire(
                request_type="WSRecv",
                name="WS recv map update",
                response_time=elapsed,
                response_length=0,
                exception=e,
                context={},
            )
            self.ws = None

    def on_stop(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass


# ─────────────────────────────────────────────
# Integration API User (HRIS pull)
# ─────────────────────────────────────────────

class IntegrationUser(HttpUser):
    """
    Simulates HRIS systems pulling attendance data.
    Low frequency, high-volume reads.
    """

    wait_time = between(10, 30)
    weight = 1  # Very few compared to employees

    def on_start(self):
        # Integration uses token auth, simulate with regular login for load testing
        email = f"loadtest_user_1@test.com"
        resp = self.client.post(
            AUTH_LOGIN,
            json={"email": email, "password": USER_PASSWORD},
            name="POST /auth/login (integration)",
        )
        if resp.status_code == 200:
            self.token = resp.json().get("access", "")
        else:
            raise StopUser()

    @tag("integration")
    @task
    def pull_attendance_logs(self):
        """HRIS pull endpoint for attendance logs."""
        today = date.today().isoformat()
        self.client.get(
            INTEGRATION_LOGS,
            headers={"Authorization": f"Bearer {self.token}"},
            params={"date": today, "page_size": 100},
            name="GET /integration/pull/attendance-logs",
        )


# ─────────────────────────────────────────────
# Event hooks for pass/fail reporting
# ─────────────────────────────────────────────

@events.quitting.add_listener
def check_results(environment, **kwargs):
    """Evaluate load test results against thresholds."""
    stats = environment.runner.stats

    # Check error rate
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    if total_requests > 0:
        error_rate = total_failures / total_requests
        if error_rate > ERROR_RATE_THRESHOLD:
            print(
                f"\n❌ FAIL: Error rate {error_rate:.2%} exceeds "
                f"threshold {ERROR_RATE_THRESHOLD:.2%}"
            )
            environment.process_exit_code = 1
        else:
            print(f"\n✅ PASS: Error rate {error_rate:.2%}")

    # Check p95 response time
    p95 = stats.total.get_response_time_percentile(0.95)
    if p95 and p95 > P95_RESPONSE_TIME_MS:
        print(
            f"❌ FAIL: P95 response time {p95:.0f}ms exceeds "
            f"threshold {P95_RESPONSE_TIME_MS}ms"
        )
        environment.process_exit_code = 1
    elif p95:
        print(f"✅ PASS: P95 response time {p95:.0f}ms")

    # Summary
    print(f"\n{'='*60}")
    print(f"Total requests: {total_requests}")
    print(f"Total failures: {total_failures}")
    print(f"Avg response time: {stats.total.avg_response_time:.0f}ms")
    print(f"Median response time: {stats.total.median_response_time}ms")
    if p95:
        print(f"P95 response time: {p95:.0f}ms")
    p99 = stats.total.get_response_time_percentile(0.99)
    if p99:
        print(f"P99 response time: {p99:.0f}ms")
    print(f"Requests/s: {stats.total.current_rps:.1f}")
    print(f"{'='*60}")
