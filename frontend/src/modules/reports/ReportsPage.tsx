import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { DataTable } from "@/components/common/DataTable";
import { attendanceService } from "@/services/attendance.service";
import type { AttendanceSummary } from "@/types";
import {
  ArrowDownTrayIcon,
  FunnelIcon,
} from "@heroicons/react/24/outline";

export function ReportsPage() {
  const { t } = useTranslation();
  const { tenantSlug } = useParams<{ tenantSlug: string }>();

  const [loading, setLoading] = useState(true);
  const [summaries, setSummaries] = useState<AttendanceSummary[]>([]);

  // Date filters
  const today = new Date();
  const monthStart = new Date(today.getFullYear(), today.getMonth(), 1);
  const [dateFrom, setDateFrom] = useState(monthStart.toISOString().split("T")[0]);
  const [dateTo, setDateTo] = useState(today.toISOString().split("T")[0]);

  useEffect(() => {
    if (!tenantSlug) return;
    loadData();
  }, [tenantSlug, dateFrom, dateTo]);

  const loadData = async () => {
    if (!tenantSlug) return;
    setLoading(true);
    try {
      const res = await attendanceService.getSummary(tenantSlug, {
        date_from: dateFrom,
        date_to: dateTo,
      });
      const data = res.data ?? res;
      setSummaries(Array.isArray(data) ? data : []);
    } catch {
      setSummaries([]);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = () => {
    if (summaries.length === 0) return;

    const headers = [
      "Employee", "Total Days", "Present", "Absent", "Late",
      "Early Departure", "Half Day", "Leave", "Total Hours", "Avg Hours/Day",
    ];
    const rows = summaries.map((s) => [
      s.employee_name,
      s.total_days,
      s.present_count,
      s.absent_count,
      s.late_count,
      s.early_departure_count,
      s.half_day_count,
      s.leave_count,
      s.total_hours?.toFixed(1) ?? "0",
      s.avg_hours_per_day?.toFixed(1) ?? "0",
    ]);

    const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `attendance-report-${dateFrom}-to-${dateTo}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Totals
  const totalPresent = summaries.reduce((sum, s) => sum + (s.present_count ?? 0), 0);
  const totalAbsent = summaries.reduce((sum, s) => sum + (s.absent_count ?? 0), 0);
  const totalLate = summaries.reduce((sum, s) => sum + (s.late_count ?? 0), 0);
  const totalHours = summaries.reduce((sum, s) => sum + (s.total_hours ?? 0), 0);

  const columns = [
    {
      key: "employee_name", header: t("attendance.employee"),
      render: (s: AttendanceSummary) => (
        <span className="font-medium text-gray-900 dark:text-white">{s.employee_name}</span>
      ),
    },
    { key: "total_days", header: "Total Days" },
    {
      key: "present_count", header: t("attendance.present"),
      render: (s: AttendanceSummary) => (
        <span className="font-medium text-green-600 dark:text-green-400">{s.present_count}</span>
      ),
    },
    {
      key: "absent_count", header: t("attendance.absent"),
      render: (s: AttendanceSummary) => (
        <span className="font-medium text-red-600 dark:text-red-400">{s.absent_count}</span>
      ),
    },
    {
      key: "late_count", header: t("attendance.late"),
      render: (s: AttendanceSummary) => (
        <span className="font-medium text-yellow-600 dark:text-yellow-400">{s.late_count}</span>
      ),
    },
    { key: "early_departure_count", header: t("attendance.early_departure") },
    { key: "half_day_count", header: t("attendance.half_day") },
    { key: "leave_count", header: t("attendance.on_leave") },
    {
      key: "total_hours", header: "Total Hours",
      render: (s: AttendanceSummary) => `${(s.total_hours ?? 0).toFixed(1)}h`,
    },
    {
      key: "avg_hours_per_day", header: "Avg Hours/Day",
      render: (s: AttendanceSummary) => `${(s.avg_hours_per_day ?? 0).toFixed(1)}h`,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          {t("nav.reports")}
        </h2>
        <button
          onClick={handleExportCSV}
          disabled={summaries.length === 0}
          className="btn-secondary flex items-center gap-1 disabled:opacity-50"
        >
          <ArrowDownTrayIcon className="h-4 w-4" />
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap items-end gap-4">
          <FunnelIcon className="h-5 w-5 text-gray-400" />
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
              From
            </label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="input"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
              To
            </label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="input"
            />
          </div>
          <button onClick={loadData} className="btn-primary">
            Apply
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">{totalPresent}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Total Present</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-red-600 dark:text-red-400">{totalAbsent}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Total Absent</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{totalLate}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Total Late</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{totalHours.toFixed(0)}h</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Total Hours</p>
        </div>
      </div>

      {/* Data Table */}
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <LoadingSpinner className="py-12" />
        ) : (
          <DataTable
            columns={columns}
            data={summaries}
            keyExtractor={(s) => s.employee_id}
            emptyMessage="No attendance data found for the selected period."
          />
        )}
      </div>

      <p className="text-xs text-gray-400 dark:text-gray-500">
        Report period: {dateFrom} to {dateTo} | {summaries.length} employee(s)
      </p>
    </div>
  );
}
