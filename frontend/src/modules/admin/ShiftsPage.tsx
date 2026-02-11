import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import { DataTable } from "@/components/common/DataTable";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { attendanceService } from "@/services/attendance.service";
import type { Shift } from "@/types";

export function ShiftsPage() {
  const { t } = useTranslation();
  const { tenantSlug } = useParams<{ tenantSlug: string }>();
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tenantSlug) return;
    setLoading(true);
    attendanceService
      .getShifts(tenantSlug)
      .then((res) => setShifts(res.results ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [tenantSlug]);

  const columns = [
    { key: "name", header: t("admin.shifts.name") },
    { key: "start_time", header: t("admin.shifts.start") },
    { key: "end_time", header: t("admin.shifts.end") },
    {
      key: "grace_period_minutes",
      header: t("admin.shifts.grace"),
      render: (s: Shift) => `${s.grace_period_minutes} min`,
    },
    {
      key: "is_active",
      header: t("admin.employees.status"),
      render: (s: Shift) => (
        <span className={`badge ${s.is_active ? "badge-present" : "badge-absent"}`}>
          {s.is_active ? "Active" : "Inactive"}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          {t("admin.shifts.title")}
        </h2>
        <button className="btn-primary">{t("admin.shifts.add")}</button>
      </div>
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <LoadingSpinner className="py-12" />
        ) : (
          <DataTable columns={columns} data={shifts} keyExtractor={(s) => s.id} />
        )}
      </div>
    </div>
  );
}
