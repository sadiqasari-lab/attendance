import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { DataTable } from "@/components/common/DataTable";
import api from "@/services/api";
import type { Tenant, Group, Department, PaginatedResponse } from "@/types";
import {
  BuildingOffice2Icon,
  BuildingOfficeIcon,
  PlusIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";

type Tab = "groups" | "tenants" | "departments";

export function TenantSetupPage() {
  const { t } = useTranslation();
  const { tenantSlug } = useParams<{ tenantSlug: string }>();

  const [activeTab, setActiveTab] = useState<Tab>("tenants");
  const [loading, setLoading] = useState(true);

  // Data
  const [groups, setGroups] = useState<Group[]>([]);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);

  // Modals
  const [showGroupModal, setShowGroupModal] = useState(false);
  const [showTenantModal, setShowTenantModal] = useState(false);
  const [showDeptModal, setShowDeptModal] = useState(false);

  // Forms
  const [groupForm, setGroupForm] = useState({ name: "", name_ar: "", description: "" });
  const [tenantForm, setTenantForm] = useState({
    name: "", name_ar: "", slug: "", group: "", description: "",
    city: "", country: "SA", phone: "", email: "", timezone: "Asia/Riyadh",
  });
  const [deptForm, setDeptForm] = useState({ name: "", name_ar: "", description: "" });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, [tenantSlug]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [groupRes, tenantRes, deptRes] = await Promise.all([
        api.get<PaginatedResponse<Group>>("/tenants/groups/").catch(() => ({ data: { results: [] } })),
        api.get<PaginatedResponse<Tenant>>("/tenants/tenants/").catch(() => ({ data: { results: [] } })),
        api.get<PaginatedResponse<Department>>(`/tenants/departments/?tenant_slug=${tenantSlug}`).catch(() => ({ data: { results: [] } })),
      ]);
      setGroups(groupRes.data.results ?? []);
      setTenants(tenantRes.data.results ?? []);
      setDepartments(deptRes.data.results ?? []);
    } finally {
      setLoading(false);
    }
  };

  // --- Group CRUD ---
  const handleAddGroup = async () => {
    if (!groupForm.name) return;
    setSaving(true);
    try {
      const { data } = await api.post("/tenants/groups/", groupForm);
      setGroups([...groups, data]);
      setGroupForm({ name: "", name_ar: "", description: "" });
      setShowGroupModal(false);
    } catch (err) {
      console.error("Failed to add group:", err);
    } finally {
      setSaving(false);
    }
  };

  // --- Tenant CRUD ---
  const handleAddTenant = async () => {
    if (!tenantForm.name || !tenantForm.slug) return;
    setSaving(true);
    try {
      const { data } = await api.post("/tenants/tenants/", tenantForm);
      setTenants([...tenants, data]);
      setTenantForm({ name: "", name_ar: "", slug: "", group: "", description: "", city: "", country: "SA", phone: "", email: "", timezone: "Asia/Riyadh" });
      setShowTenantModal(false);
    } catch (err) {
      console.error("Failed to add tenant:", err);
    } finally {
      setSaving(false);
    }
  };

  // --- Department CRUD ---
  const handleAddDept = async () => {
    if (!deptForm.name || !tenantSlug) return;
    setSaving(true);
    try {
      const { data } = await api.post("/tenants/departments/", {
        ...deptForm,
        tenant_slug: tenantSlug,
      });
      const dept = data.data ?? data;
      setDepartments([...departments, dept]);
      setDeptForm({ name: "", name_ar: "", description: "" });
      setShowDeptModal(false);
    } catch (err) {
      console.error("Failed to add department:", err);
    } finally {
      setSaving(false);
    }
  };

  const groupColumns = [
    { key: "name", header: "Name" },
    { key: "name_ar", header: "Name (Arabic)" },
    { key: "description", header: "Description" },
    {
      key: "is_active", header: "Status",
      render: (g: Group) => (
        <span className={`badge ${g.is_active ? "badge-present" : "badge-absent"}`}>
          {g.is_active ? "Active" : "Inactive"}
        </span>
      ),
    },
  ];

  const tenantColumns = [
    { key: "name", header: "Name" },
    { key: "slug", header: "Slug" },
    { key: "city", header: "City" },
    { key: "country", header: "Country" },
    { key: "timezone", header: "Timezone" },
    {
      key: "is_active", header: "Status",
      render: (t: Tenant) => (
        <span className={`badge ${t.is_active ? "badge-present" : "badge-absent"}`}>
          {t.is_active ? "Active" : "Inactive"}
        </span>
      ),
    },
  ];

  const deptColumns = [
    { key: "name", header: "Name" },
    { key: "name_ar", header: "Name (Arabic)" },
    {
      key: "is_active", header: "Status",
      render: (d: Department) => (
        <span className={`badge ${d.is_active ? "badge-present" : "badge-absent"}`}>
          {d.is_active ? "Active" : "Inactive"}
        </span>
      ),
    },
  ];

  const tabs: { id: Tab; label: string; icon: React.ComponentType<React.SVGProps<SVGSVGElement>> }[] = [
    { id: "groups", label: "Groups", icon: BuildingOffice2Icon },
    { id: "tenants", label: "Tenants", icon: BuildingOfficeIcon },
    { id: "departments", label: "Departments", icon: BuildingOffice2Icon },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          Tenant Setup
        </h2>
        <button
          className="btn-primary flex items-center gap-1"
          onClick={() => {
            if (activeTab === "groups") setShowGroupModal(true);
            else if (activeTab === "tenants") setShowTenantModal(true);
            else setShowDeptModal(true);
          }}
        >
          <PlusIcon className="h-4 w-4" />
          Add {activeTab === "groups" ? "Group" : activeTab === "tenants" ? "Tenant" : "Department"}
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? "border-primary-600 text-primary-600 dark:text-primary-400"
                  : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400"
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <LoadingSpinner className="py-12" />
        ) : activeTab === "groups" ? (
          <DataTable columns={groupColumns} data={groups} keyExtractor={(g) => g.id} emptyMessage="No groups configured. Create your first group." />
        ) : activeTab === "tenants" ? (
          <DataTable columns={tenantColumns} data={tenants} keyExtractor={(t) => t.id} emptyMessage="No tenants configured. Create your first tenant." />
        ) : (
          <DataTable columns={deptColumns} data={departments} keyExtractor={(d) => d.id} emptyMessage="No departments configured. Create your first department." />
        )}
      </div>

      {/* Group Modal */}
      {showGroupModal && (
        <Modal title="Add Group" onClose={() => setShowGroupModal(false)}>
          <div className="space-y-4">
            <Input label="Group Name" value={groupForm.name} onChange={(v) => setGroupForm({ ...groupForm, name: v })} />
            <Input label="Group Name (Arabic)" value={groupForm.name_ar} onChange={(v) => setGroupForm({ ...groupForm, name_ar: v })} dir="rtl" />
            <Input label="Description" value={groupForm.description} onChange={(v) => setGroupForm({ ...groupForm, description: v })} />
            <button onClick={handleAddGroup} disabled={saving || !groupForm.name} className="btn-primary w-full">
              {saving ? t("common.loading") : "Add Group"}
            </button>
          </div>
        </Modal>
      )}

      {/* Tenant Modal */}
      {showTenantModal && (
        <Modal title="Add Tenant" onClose={() => setShowTenantModal(false)}>
          <div className="space-y-4">
            <Input label="Tenant Name" value={tenantForm.name} onChange={(v) => setTenantForm({ ...tenantForm, name: v })} />
            <Input label="Name (Arabic)" value={tenantForm.name_ar} onChange={(v) => setTenantForm({ ...tenantForm, name_ar: v })} dir="rtl" />
            <Input label="Slug (URL-safe)" value={tenantForm.slug} onChange={(v) => setTenantForm({ ...tenantForm, slug: v.toLowerCase().replace(/[^a-z0-9-]/g, "") })} />
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Group</label>
              <select className="input w-full" value={tenantForm.group} onChange={(e) => setTenantForm({ ...tenantForm, group: e.target.value })}>
                <option value="">-- Select Group --</option>
                {groups.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
              </select>
            </div>
            <Input label="City" value={tenantForm.city} onChange={(v) => setTenantForm({ ...tenantForm, city: v })} />
            <Input label="Email" value={tenantForm.email} onChange={(v) => setTenantForm({ ...tenantForm, email: v })} />
            <Input label="Phone" value={tenantForm.phone} onChange={(v) => setTenantForm({ ...tenantForm, phone: v })} />
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Timezone</label>
              <select className="input w-full" value={tenantForm.timezone} onChange={(e) => setTenantForm({ ...tenantForm, timezone: e.target.value })}>
                <option value="Asia/Riyadh">Asia/Riyadh (UTC+3)</option>
                <option value="Asia/Dubai">Asia/Dubai (UTC+4)</option>
                <option value="Asia/Karachi">Asia/Karachi (UTC+5)</option>
                <option value="Europe/London">Europe/London (UTC+0)</option>
                <option value="America/New_York">America/New_York (UTC-5)</option>
              </select>
            </div>
            <button onClick={handleAddTenant} disabled={saving || !tenantForm.name || !tenantForm.slug} className="btn-primary w-full">
              {saving ? t("common.loading") : "Add Tenant"}
            </button>
          </div>
        </Modal>
      )}

      {/* Department Modal */}
      {showDeptModal && (
        <Modal title="Add Department" onClose={() => setShowDeptModal(false)}>
          <div className="space-y-4">
            <Input label="Department Name" value={deptForm.name} onChange={(v) => setDeptForm({ ...deptForm, name: v })} />
            <Input label="Name (Arabic)" value={deptForm.name_ar} onChange={(v) => setDeptForm({ ...deptForm, name_ar: v })} dir="rtl" />
            <Input label="Description" value={deptForm.description} onChange={(v) => setDeptForm({ ...deptForm, description: v })} />
            <button onClick={handleAddDept} disabled={saving || !deptForm.name} className="btn-primary w-full">
              {saving ? t("common.loading") : "Add Department"}
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}

// --- Helper Components ---
function Modal({ title, children, onClose }: { title: string; children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">{title}</h3>
          <button onClick={onClose} className="rounded p-1 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700">
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

function Input({ label, value, onChange, dir }: { label: string; value: string; onChange: (v: string) => void; dir?: string }) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">{label}</label>
      <input type="text" value={value} onChange={(e) => onChange(e.target.value)} className="input w-full" dir={dir} />
    </div>
  );
}
