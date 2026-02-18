import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import { XMarkIcon } from "@heroicons/react/24/outline";
import { DataTable } from "@/components/common/DataTable";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import api from "@/services/api";
import type { Department, Employee, PaginatedResponse } from "@/types";

interface AddEmployeeForm {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone: string;
  employee_id: string;
  department: string;
  designation: string;
  date_of_joining: string;
}

const emptyForm: AddEmployeeForm = {
  email: "",
  password: "",
  first_name: "",
  last_name: "",
  phone: "",
  employee_id: "",
  department: "",
  designation: "",
  date_of_joining: "",
};

export function EmployeesPage() {
  const { t } = useTranslation();
  const { tenantSlug } = useParams<{ tenantSlug: string }>();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<AddEmployeeForm>(emptyForm);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const fetchEmployees = () => {
    if (!tenantSlug) return;
    setLoading(true);
    api
      .get<PaginatedResponse<Employee>>(`/tenants/employees/?tenant_slug=${tenantSlug}`)
      .then((res) => setEmployees(res.data.results ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchEmployees();
  }, [tenantSlug]);

  useEffect(() => {
    if (!tenantSlug) return;
    api
      .get<PaginatedResponse<Department>>(`/tenants/departments/?tenant_slug=${tenantSlug}`)
      .then((res) => setDepartments(res.data.results ?? []))
      .catch(() => {});
  }, [tenantSlug]);

  const handleOpen = () => {
    setForm(emptyForm);
    setError("");
    setShowModal(true);
  };

  const handleSubmit = async () => {
    if (!form.email || !form.password || !form.employee_id) return;
    setSubmitting(true);
    setError("");
    try {
      await api.post("/tenants/employees/", {
        ...form,
        department: form.department || null,
        date_of_joining: form.date_of_joining || null,
        tenant_slug: tenantSlug,
      });
      setShowModal(false);
      fetchEmployees();
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: Record<string, unknown> } };
      const data = axiosErr.response?.data;
      if (data) {
        const messages = Object.entries(data)
          .filter(([k]) => k !== "success")
          .map(([, v]) => (Array.isArray(v) ? v.join(", ") : String(v)))
          .join(" ");
        setError(messages || t("common.error"));
      } else {
        setError(t("common.error"));
      }
    } finally {
      setSubmitting(false);
    }
  };

  const setField = (key: keyof AddEmployeeForm, value: string) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const columns = [
    {
      key: "employee_id",
      header: t("admin.employees.id"),
    },
    {
      key: "name",
      header: t("admin.employees.name"),
      render: (e: Employee) => e.user?.full_name ?? "-",
    },
    {
      key: "department_name",
      header: t("admin.employees.department"),
      render: (e: Employee) => e.department_name ?? "-",
    },
    {
      key: "designation",
      header: t("admin.employees.designation"),
    },
    {
      key: "is_active",
      header: t("admin.employees.status"),
      render: (e: Employee) => (
        <span className={`badge ${e.is_active ? "badge-present" : "badge-absent"}`}>
          {e.is_active ? "Active" : "Inactive"}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          {t("admin.employees.title")}
        </h2>
        <button className="btn-primary" onClick={handleOpen}>
          {t("admin.employees.add")}
        </button>
      </div>

      <div className="card p-0 overflow-hidden">
        {loading ? (
          <LoadingSpinner className="py-12" />
        ) : (
          <DataTable
            columns={columns}
            data={employees}
            keyExtractor={(e) => e.id}
          />
        )}
      </div>

      {/* -------- Add Employee Modal -------- */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                {t("admin.employees.add")}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="rounded p-1 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>

            {error && (
              <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-400">
                {error}
              </div>
            )}

            <div className="space-y-4">
              {/* Employee ID */}
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t("admin.employees.id")} *
                </label>
                <input
                  type="text"
                  value={form.employee_id}
                  onChange={(e) => setField("employee_id", e.target.value)}
                  className="input w-full"
                  placeholder="EMP-001"
                />
              </div>

              {/* Email */}
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t("admin.employees.email")} *
                </label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setField("email", e.target.value)}
                  className="input w-full"
                  placeholder="employee@company.com"
                />
              </div>

              {/* Password */}
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t("admin.employees.password")} *
                </label>
                <input
                  type="password"
                  value={form.password}
                  onChange={(e) => setField("password", e.target.value)}
                  className="input w-full"
                />
              </div>

              {/* First Name / Last Name */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t("admin.employees.first_name")}
                  </label>
                  <input
                    type="text"
                    value={form.first_name}
                    onChange={(e) => setField("first_name", e.target.value)}
                    className="input w-full"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t("admin.employees.last_name")}
                  </label>
                  <input
                    type="text"
                    value={form.last_name}
                    onChange={(e) => setField("last_name", e.target.value)}
                    className="input w-full"
                  />
                </div>
              </div>

              {/* Phone */}
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t("admin.employees.phone")}
                </label>
                <input
                  type="text"
                  value={form.phone}
                  onChange={(e) => setField("phone", e.target.value)}
                  className="input w-full"
                />
              </div>

              {/* Department */}
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t("admin.employees.department")}
                </label>
                <select
                  value={form.department}
                  onChange={(e) => setField("department", e.target.value)}
                  className="input w-full"
                >
                  <option value="">—</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Designation */}
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t("admin.employees.designation")}
                </label>
                <input
                  type="text"
                  value={form.designation}
                  onChange={(e) => setField("designation", e.target.value)}
                  className="input w-full"
                />
              </div>

              {/* Date of Joining */}
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t("admin.employees.date_of_joining")}
                </label>
                <input
                  type="date"
                  value={form.date_of_joining}
                  onChange={(e) => setField("date_of_joining", e.target.value)}
                  className="input w-full"
                />
              </div>

              {/* Actions */}
              <div className="flex gap-2 pt-2">
                <button
                  onClick={() => setShowModal(false)}
                  className="btn-secondary flex-1"
                >
                  {t("common.cancel")}
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={submitting || !form.email || !form.password || !form.employee_id}
                  className="btn-primary flex-1"
                >
                  {submitting ? t("common.loading") : t("common.save")}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
