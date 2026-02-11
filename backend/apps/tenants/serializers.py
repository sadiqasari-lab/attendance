"""DRF serializers for the tenants app."""
from rest_framework import serializers

from apps.tenants.models import Department, Group, Tenant


# ---------------------------------------------------------------------------
# Group
# ---------------------------------------------------------------------------
class GroupSerializer(serializers.ModelSerializer):
    """Serializer for the Group (parent company) model."""

    tenant_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "name_ar",
            "description",
            "is_active",
            "tenant_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_tenant_count(self, obj):
        return obj.tenants.filter(is_deleted=False).count()


# ---------------------------------------------------------------------------
# Tenant
# ---------------------------------------------------------------------------
class TenantSerializer(serializers.ModelSerializer):
    """Serializer for the Tenant (child company / branch) model.

    Includes nested read-only group information on retrieval.
    """

    group_detail = GroupSerializer(source="group", read_only=True)

    class Meta:
        model = Tenant
        fields = [
            "id",
            "group",
            "group_detail",
            "name",
            "name_ar",
            "slug",
            "description",
            "address",
            "city",
            "country",
            "phone",
            "email",
            "timezone",
            "is_active",
            "logo",
            "settings",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_slug(self, value):
        """Ensure the slug is lowercase and URL-safe."""
        value = value.lower().strip()
        if not value:
            raise serializers.ValidationError("Slug must not be empty.")
        return value

    def validate_email(self, value):
        """Normalise email to lowercase."""
        if value:
            return value.lower().strip()
        return value

    def validate_timezone(self, value):
        """Basic validation that the timezone string is non-empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Timezone must not be empty.")
        return value.strip()


# ---------------------------------------------------------------------------
# Department
# ---------------------------------------------------------------------------
class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for the Department model (tenant-scoped)."""

    children = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Department
        fields = [
            "id",
            "tenant",
            "name",
            "name_ar",
            "description",
            "is_active",
            "parent",
            "children",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "tenant", "created_at", "updated_at"]

    def get_children(self, obj):
        """Return immediate child departments."""
        children_qs = obj.children.filter(is_deleted=False).order_by("name")
        return DepartmentSerializer(children_qs, many=True).data

    def validate_parent(self, value):
        """Prevent a department from being its own parent."""
        if value and self.instance and value.pk == self.instance.pk:
            raise serializers.ValidationError(
                "A department cannot be its own parent."
            )
        return value

    def validate(self, attrs):
        """Ensure the parent department belongs to the same tenant."""
        parent = attrs.get("parent")
        tenant = self.context.get("tenant") or attrs.get("tenant")

        if parent and tenant and parent.tenant_id != tenant.pk:
            raise serializers.ValidationError(
                {"parent": "Parent department must belong to the same tenant."}
            )
        return attrs
