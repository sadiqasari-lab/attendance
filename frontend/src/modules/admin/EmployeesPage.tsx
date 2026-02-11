import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import { DataTable } from "@/components/common/DataTable";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import api from "@/services/api";
import type { Employee, PaginatedResponse } from "@/types";

export function EmployeesPage() {
  const { t } = useTranslation();
  const { tenantSlug } = useParams<{ tenantSlug: string }>();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tenantSlug) return;
    setLoading(true);
    api
      .get<PaginatedResponse<Employee>>(`/tenants/employees/?tenant_slug=${tenantSlug}`)
      .then((res) => setEmployees(res.data.results ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [tenantSlug]);

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
        <button className="btn-primary">{t("admin.employees.add")}</button>
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
    </div>
  );
}
