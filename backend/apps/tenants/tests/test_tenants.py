"""Tests for the tenants app."""
import pytest

from apps.tenants.models import Department, Group, Tenant


class TestGroupModel:
    @pytest.mark.django_db
    def test_group_creation(self, group):
        assert group.name == "Arab Inspire Company"
        assert str(group) == "Arab Inspire Company"


class TestTenantModel:
    @pytest.mark.django_db
    def test_tenant_creation(self, tenant):
        assert tenant.slug == "abuwaleed"
        assert tenant.is_active is True
        assert tenant.group is not None

    @pytest.mark.django_db
    def test_tenant_slug_unique(self, tenant, group):
        with pytest.raises(Exception):
            Tenant.objects.create(
                group=group,
                name="Duplicate Slug",
                slug="abuwaleed",
            )

    @pytest.mark.django_db
    def test_tenant_str(self, tenant):
        assert str(tenant) == "Abu Waleed Tea Franchise"


class TestDepartmentModel:
    @pytest.mark.django_db
    def test_department_creation(self, department, tenant):
        assert department.tenant == tenant
        assert department.name == "Operations"

    @pytest.mark.django_db
    def test_department_tenant_isolation(self, department, tenant_b):
        depts = Department.objects.filter(tenant=tenant_b)
        assert depts.count() == 0


class TestTenantIsolation:
    @pytest.mark.django_db
    def test_tenants_have_separate_data(self, tenant, tenant_b):
        dept_a = Department.objects.create(tenant=tenant, name="Dept A")
        dept_b = Department.objects.create(tenant=tenant_b, name="Dept B")

        tenant_a_depts = Department.objects.filter(tenant=tenant)
        tenant_b_depts = Department.objects.filter(tenant=tenant_b)

        assert tenant_a_depts.count() >= 1
        assert tenant_b_depts.count() == 1
        assert dept_a not in tenant_b_depts
        assert dept_b not in tenant_a_depts


class TestTenantAPI:
    @pytest.mark.django_db
    def test_list_tenants_unauthenticated(self, api_client):
        response = api_client.get("/api/v1/tenants/")
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_list_tenants_as_admin(self, admin_client, tenant, tenant_b):
        response = admin_client.get("/api/v1/tenants/")
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_retrieve_tenant(self, admin_client, tenant):
        response = admin_client.get(f"/api/v1/tenants/{tenant.pk}/")
        assert response.status_code == 200
