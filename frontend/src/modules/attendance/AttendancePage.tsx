import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import { attendanceService } from "@/services/attendance.service";
import { DataTable } from "@/components/common/DataTable";
import { StatusBadge } from "@/components/common/StatusBadge";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import type { AttendanceRecord, AttendanceStatus } from "@/types";
import { format } from "date-fns";

export function AttendancePage() {
  const { t } = useTranslation();
  const { tenantSlug } = useParams<{ tenantSlug: string }>();
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const fetchRecords = useCallback(async () => {
    if (!tenantSlug) return;
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (statusFilter) params.status = statusFilter;

      const res = await attendanceService.getRecords(tenantSlug, params);
      setRecords(res.results ?? []);
    } catch {
      // Handle silently
    } finally {
      setLoading(false);
    }
  }, [tenantSlug, dateFrom, dateTo, statusFilter]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  const columns = [
    {
      key: "date",
      header: t("attendance.date"),
      render: (r: AttendanceRecord) => r.date,
    },
    {
      key: "employee",
      header: t("attendance.employee"),
      render: (r: AttendanceRecord) =>
        r.employee_detail?.user?.full_name ?? r.employee_detail?.employee_id ?? "-",
    },
    {
      key: "shift_name",
      header: t("attendance.shift"),
    },
    {
      key: "clock_in_time",
      header: t("attendance.clock_in"),
      render: (r: AttendanceRecord) =>
        r.clock_in_time ? format(new Date(r.clock_in_time), "HH:mm:ss") : "-",
    },
    {
      key: "clock_out_time",
      header: t("attendance.clock_out"),
      render: (r: AttendanceRecord) =>
        r.clock_out_time ? format(new Date(r.clock_out_time), "HH:mm:ss") : "-",
    },
    {
      key: "status",
      header: t("attendance.status"),
      render: (r: AttendanceRecord) => <StatusBadge status={r.status} />,
    },
    {
      key: "duration_hours",
      header: t("attendance.duration"),
      render: (r: AttendanceRecord) =>
        r.duration_hours != null ? `${r.duration_hours.toFixed(1)}h` : "-",
    },
    {
      key: "is_validated",
      header: t("attendance.validated"),
      render: (r: AttendanceRecord) => (
        <span
          className={`badge ${
            r.is_validated ? "badge-present" : "badge-absent"
          }`}
        >
          {r.is_validated ? "Yes" : "No"}
        </span>
      ),
    },
  ];

  const statuses: AttendanceStatus[] = [
    "PRESENT", "ABSENT", "LATE", "EARLY_DEPARTURE", "HALF_DAY", "ON_LEAVE",
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          {t("attendance.title")}
        </h2>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-wrap gap-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
              {t("attendance.filter_by_date")}
            </label>
            <div className="flex gap-2">
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="input-field w-40"
              />
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="input-field w-40"
              />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
              {t("attendance.filter_by_status")}
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input-field w-44"
            >
              <option value="">All</option>
              {statuses.map((s) => (
                <option key={s} value={s}>
                  {t(`attendance.${s.toLowerCase()}`)}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Records Table */}
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <LoadingSpinner className="py-12" />
        ) : (
          <DataTable
            columns={columns}
            data={records}
            keyExtractor={(r) => r.id}
            emptyMessage={t("attendance.no_records")}
          />
        )}
      </div>
    </div>
  );
}
