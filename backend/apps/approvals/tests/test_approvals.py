"""Tests for the approvals app — model, serializers, and API workflow."""
import pytest
from django.utils import timezone
from rest_framework import status

from apps.accounts.models import Employee, User
from apps.approvals.models import ApprovalRequest
from apps.core.models import AuditLog


# ── Model tests ──────────────────────────────────────────


class TestApprovalRequestModel:
    @pytest.mark.django_db
    def test_create_approval_request(self, tenant, employee):
        request = ApprovalRequest.objects.create(
            tenant=tenant,
            requester=employee,
            request_type=ApprovalRequest.RequestType.LEAVE_REQUEST,
            title="Annual Leave",
            description="Requesting 5 days off",
            priority=ApprovalRequest.Priority.MEDIUM,
        )
        assert request.status == "PENDING"
        assert request.reviewed_by is None
        assert request.reviewed_at is None
        assert str(request).startswith("[Leave Request]")

    @pytest.mark.django_db
    def test_default_status_is_pending(self, tenant, employee):
        request = ApprovalRequest.objects.create(
            tenant=tenant,
            requester=employee,
            request_type=ApprovalRequest.RequestType.ATTENDANCE_CORRECTION,
            title="Clock-in correction",
            description="Forgot to clock in",
        )
        assert request.status == ApprovalRequest.Status.PENDING

    @pytest.mark.django_db
    def test_metadata_stores_json(self, tenant, employee):
        meta = {"original_clock_in": "08:00", "requested_clock_in": "07:45"}
        request = ApprovalRequest.objects.create(
            tenant=tenant,
            requester=employee,
            request_type=ApprovalRequest.RequestType.ATTENDANCE_CORRECTION,
            title="Correction",
            description="Fix time",
            metadata=meta,
        )
        request.refresh_from_db()
        assert request.metadata == meta

    @pytest.mark.django_db
    def test_soft_delete(self, tenant, employee):
        request = ApprovalRequest.objects.create(
            tenant=tenant,
            requester=employee,
            request_type=ApprovalRequest.RequestType.DEVICE_CHANGE,
            title="New phone",
            description="Switched to new device",
        )
        request.soft_delete()
        assert request.is_deleted is True
        assert request.deleted_at is not None
        assert ApprovalRequest.active_objects.filter(pk=request.pk).count() == 0

    @pytest.mark.django_db
    def test_request_type_choices(self):
        choices = dict(ApprovalRequest.RequestType.choices)
        assert "ATTENDANCE_CORRECTION" in choices
        assert "DEVICE_CHANGE" in choices
        assert "LEAVE_REQUEST" in choices

    @pytest.mark.django_db
    def test_priority_choices(self):
        choices = dict(ApprovalRequest.Priority.choices)
        assert "LOW" in choices
        assert "MEDIUM" in choices
        assert "HIGH" in choices
        assert "URGENT" in choices


# ── API tests ────────────────────────────────────────────


@pytest.fixture
def manager_user(db):
    return User.objects.create_user(
        email="manager@arabinspire.cloud",
        password="Manager123!",
        first_name="Khalid",
        last_name="Manager",
        role="MANAGER",
    )


@pytest.fixture
def manager_employee(db, tenant, manager_user):
    return Employee.objects.create(
        tenant=tenant,
        user=manager_user,
        employee_id="MGR001",
        designation="Manager",
        is_active=True,
    )


@pytest.fixture
def approval_request(db, tenant, employee, employee_user):
    return ApprovalRequest.objects.create(
        tenant=tenant,
        requester=employee,
        request_type=ApprovalRequest.RequestType.LEAVE_REQUEST,
        title="Vacation Request",
        description="Taking a week off",
        priority=ApprovalRequest.Priority.HIGH,
        created_by=employee_user,
    )


@pytest.fixture
def manager_client(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    return api_client


class TestApprovalRequestAPI:
    """API-level tests for the approval workflow."""

    @pytest.mark.django_db
    def test_list_requires_authentication(self, api_client, tenant):
        resp = api_client.get(
            "/api/approvals/",
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_employee_can_list_approvals(
        self, authenticated_client, tenant, employee, approval_request
    ):
        resp = authenticated_client.get(
            "/api/approvals/",
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert resp.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_employee_can_create_approval(
        self, authenticated_client, tenant, employee
    ):
        resp = authenticated_client.post(
            "/api/approvals/",
            data={
                "request_type": "LEAVE_REQUEST",
                "title": "Sick Leave",
                "description": "Feeling unwell",
                "priority": "HIGH",
                "metadata": {},
            },
            format="json",
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert resp.status_code in (
            status.HTTP_201_CREATED,
            status.HTTP_200_OK,
        )

    @pytest.mark.django_db
    def test_manager_can_approve(
        self, manager_client, tenant, manager_employee, approval_request
    ):
        resp = manager_client.post(
            f"/api/approvals/{approval_request.pk}/approve/",
            data={"review_notes": "Approved — enjoy your vacation!"},
            format="json",
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert resp.status_code == status.HTTP_200_OK
        approval_request.refresh_from_db()
        assert approval_request.status == "APPROVED"

    @pytest.mark.django_db
    def test_manager_can_reject(
        self, manager_client, tenant, manager_employee, approval_request
    ):
        resp = manager_client.post(
            f"/api/approvals/{approval_request.pk}/reject/",
            data={"review_notes": "Insufficient notice period."},
            format="json",
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert resp.status_code == status.HTTP_200_OK
        approval_request.refresh_from_db()
        assert approval_request.status == "REJECTED"

    @pytest.mark.django_db
    def test_cannot_approve_non_pending(
        self, manager_client, tenant, manager_employee, approval_request
    ):
        approval_request.status = ApprovalRequest.Status.APPROVED
        approval_request.save(update_fields=["status"])

        resp = manager_client.post(
            f"/api/approvals/{approval_request.pk}/approve/",
            data={},
            format="json",
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_cannot_reject_non_pending(
        self, manager_client, tenant, manager_employee, approval_request
    ):
        approval_request.status = ApprovalRequest.Status.REJECTED
        approval_request.save(update_fields=["status"])

        resp = manager_client.post(
            f"/api/approvals/{approval_request.pk}/reject/",
            data={},
            format="json",
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_owner_can_cancel(
        self, authenticated_client, tenant, employee, approval_request
    ):
        resp = authenticated_client.post(
            f"/api/approvals/{approval_request.pk}/cancel/",
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert resp.status_code == status.HTTP_200_OK
        approval_request.refresh_from_db()
        assert approval_request.status == "CANCELLED"

    @pytest.mark.django_db
    def test_non_owner_cannot_cancel(
        self, tenant, employee_b, approval_request, api_client
    ):
        api_client.force_authenticate(user=employee_b.user)
        resp = api_client.post(
            f"/api/approvals/{approval_request.pk}/cancel/",
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        # Should be 403 because the employee doesn't belong to this tenant
        assert resp.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )

    @pytest.mark.django_db
    def test_pending_count_endpoint(
        self, authenticated_client, tenant, employee, approval_request
    ):
        resp = authenticated_client.get(
            "/api/approvals/pending-count/",
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert resp.status_code == status.HTTP_200_OK
        assert "pending_count" in resp.data

    @pytest.mark.django_db
    def test_approval_creates_audit_log(
        self, manager_client, tenant, manager_employee, approval_request
    ):
        initial_count = AuditLog.objects.count()
        manager_client.post(
            f"/api/approvals/{approval_request.pk}/approve/",
            data={"review_notes": "Looks good"},
            format="json",
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert AuditLog.objects.count() > initial_count
