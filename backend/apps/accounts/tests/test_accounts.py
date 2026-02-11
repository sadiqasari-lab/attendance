"""Tests for the accounts app."""
import pytest

from apps.accounts.models import Employee, User


class TestUserModel:
    @pytest.mark.django_db
    def test_create_user(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="TestPass123!",
            first_name="Test",
            last_name="User",
        )
        assert user.email == "test@example.com"
        assert user.check_password("TestPass123!")
        assert user.role == "EMPLOYEE"
        assert user.is_active is True
        assert user.is_staff is False

    @pytest.mark.django_db
    def test_create_superuser(self):
        user = User.objects.create_superuser(
            email="super@example.com",
            password="SuperPass123!",
        )
        assert user.role == "SUPER_ADMIN"
        assert user.is_staff is True
        assert user.is_superuser is True

    @pytest.mark.django_db
    def test_user_email_required(self):
        with pytest.raises(ValueError):
            User.objects.create_user(email="", password="pass")

    @pytest.mark.django_db
    def test_user_email_unique(self):
        User.objects.create_user(email="dup@example.com", password="Pass123!")
        with pytest.raises(Exception):
            User.objects.create_user(email="dup@example.com", password="Pass456!")

    @pytest.mark.django_db
    def test_full_name(self, employee_user):
        assert employee_user.full_name == "Ahmed Hassan"


class TestEmployeeModel:
    @pytest.mark.django_db
    def test_employee_creation(self, employee, tenant, employee_user):
        assert employee.tenant == tenant
        assert employee.user == employee_user
        assert employee.employee_id == "EMP001"

    @pytest.mark.django_db
    def test_employee_unique_per_tenant(self, employee, tenant, employee_user_b):
        """Same employee_id in same tenant should fail."""
        with pytest.raises(Exception):
            Employee.objects.create(
                tenant=tenant,
                user=employee_user_b,
                employee_id="EMP001",
            )

    @pytest.mark.django_db
    def test_employee_same_id_different_tenant(self, tenant_b, employee_user_b):
        """Same employee_id in different tenant should work."""
        emp = Employee.objects.create(
            tenant=tenant_b,
            user=employee_user_b,
            employee_id="EMP001",
        )
        assert emp.pk is not None


class TestAuthAPI:
    @pytest.mark.django_db
    def test_login_success(self, api_client, employee_user):
        response = api_client.post("/api/v1/auth/login/", {
            "email": "employee@arabinspire.cloud",
            "password": "Employee123!",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access" in data.get("data", data)

    @pytest.mark.django_db
    def test_login_failure(self, api_client, employee_user):
        response = api_client.post("/api/v1/auth/login/", {
            "email": "employee@arabinspire.cloud",
            "password": "WrongPassword!",
        })
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_profile_authenticated(self, authenticated_client, employee_user):
        response = authenticated_client.get("/api/v1/auth/profile/")
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_profile_unauthenticated(self, api_client):
        response = api_client.get("/api/v1/auth/profile/")
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_change_password(self, authenticated_client, employee_user):
        response = authenticated_client.post("/api/v1/auth/password/change/", {
            "old_password": "Employee123!",
            "new_password": "NewSecurePass123!",
            "new_password_confirm": "NewSecurePass123!",
        })
        assert response.status_code == 200
        employee_user.refresh_from_db()
        assert employee_user.check_password("NewSecurePass123!")
