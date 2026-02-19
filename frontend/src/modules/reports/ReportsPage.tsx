import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import {
  ArrowDownTrayIcon,
  DocumentTextIcon,
  TableCellsIcon,
  FunnelIcon,
} from "@heroicons/react/24/outline";
import { reportsService, type ReportParams } from "@/services/reports.service";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";

type ReportType = "summary" | "detailed";

export function ReportsPage() {
  const { t } = useTranslation();
  const { tenantSlug } = useParams<{ tenantSlug: string }>();

  const today = new Date().toISOString().split("T")[0];
  const thirtyDaysAgo = new Date(Date.now() - 30 * 86400000).toISOString().split("T")[0];

  const [dateFrom, setDateFrom] = useState(thirtyDaysAgo);
  const [dateTo, setDateTo] = useState(today);
  const [statusFilter, setStatusFilter] = useState("");
  const [reportType, setReportType] = useState<ReportType>("summary");
  const [data, setData] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState<"" | "excel" | "pdf">("");

  const params: ReportParams = {
    date_from: dateFrom,
    date_to: dateTo,
    ...(statusFilter && { status: statusFilter }),
    type: reportType,
  };

  const fetchReport = useCallback(async () => {
    if (!tenantSlug) return;
    setLoading(true);
    try {
      const res = await reportsService.getReport(tenantSlug, params);
      setData(res.data ?? []);
    } catch {
      setData([]);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantSlug, dateFrom, dateTo, statusFilter, reportType]);

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  const handleExportExcel = async () => {
    if (!tenantSlug) return;
    setExporting("excel");
    try {
      await reportsService.exportExcel(tenantSlug, params);
    } catch {
      // silently fail
    } finally {
      setExporting("");
    }
  };

  const handleExportPdf = async () => {
    if (!tenantSlug) return;
    setExporting("pdf");
    try {
      await reportsService.exportPdf(tenantSlug, params);
    } catch {
      // silently fail
    } finally {
      setExporting("");
    }
  };

  const summaryHeaders = [
    t("reports.employee_id"),
    t("reports.employee_name"),
    t("reports.department"),
    t("reports.total_days"),
    t("attendance.present"),
    t("attendance.absent"),
    t("attendance.late"),
    t("attendance.early_departure"),
    t("attendance.on_leave"),
    t("reports.total_hours"),
    t("reports.avg_hours"),
  ];

  const detailedHeaders = [
    t("attendance.date"),
    t("reports.employee_id"),
    t("reports.employee_name"),
    t("reports.department"),
    t("attendance.shift"),
    t("attendance.clock_in"),
    t("attendance.clock_out"),
    t("attendance.status"),
    t("attendance.duration"),
  ];

  const headers = reportType === "summary" ? summaryHeaders : detailedHeaders;

  const renderRow = (row: Record<string, unknown>, idx: number) => {
    if (reportType === "summary") {
      return (
        <tr key={idx} className="border-b border-gray-100 dark:border-gray-700">
          <td className="px-3 py-2 text-gray-900 dark:text-white">{String(row.employee_id ?? "")}</td>
          <td className="px-3 py-2 font-medium text-gray-900 dark:text-white">{String(row.employee_name ?? "")}</td>
          <td className="px-3 py-2 text-gray-500 dark:text-gray-400">{String(row.department ?? "")}</td>
          <td className="px-3 py-2 text-center">{String(row.total_days ?? 0)}</td>
          <td className="px-3 py-2 text-center text-green-600">{String(row.present ?? 0)}</td>
          <td className="px-3 py-2 text-center text-red-600">{String(row.absent ?? 0)}</td>
          <td className="px-3 py-2 text-center text-yellow-600">{String(row.late ?? 0)}</td>
          <td className="px-3 py-2 text-center text-orange-600">{String(row.early_departure ?? 0)}</td>
          <td className="px-3 py-2 text-center text-blue-600">{String(row.on_leave ?? 0)}</td>
          <td className="px-3 py-2 text-center">{String(row.total_hours ?? 0)}</td>
          <td className="px-3 py-2 text-center">{String(row.avg_hours ?? 0)}</td>
        </tr>
      );
    }
    return (
      <tr key={idx} className="border-b border-gray-100 dark:border-gray-700">
        <td className="px-3 py-2 text-gray-900 dark:text-white">{String(row.date ?? "")}</td>
        <td className="px-3 py-2">{String(row.employee_id ?? "")}</td>
        <td className="px-3 py-2 font-medium text-gray-900 dark:text-white">{String(row.employee_name ?? "")}</td>
        <td className="px-3 py-2 text-gray-500 dark:text-gray-400">{String(row.department ?? "")}</td>
        <td className="px-3 py-2">{String(row.shift ?? "")}</td>
        <td className="px-3 py-2">{String(row.clock_in ?? "")}</td>
        <td className="px-3 py-2">{String(row.clock_out ?? "")}</td>
        <td className="px-3 py-2">
          <StatusBadge status={String(row.status ?? "")} />
        </td>
        <td className="px-3 py-2">{String(row.duration ?? "")}</td>
      </tr>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          {t("reports.title")}
        </h2>
        <div className="flex gap-2">
          <button
            onClick={handleExportExcel}
            disabled={!!exporting || data.length === 0}
            className="btn-secondary flex items-center gap-1.5 text-sm disabled:opacity-50"
          >
            <TableCellsIcon className="h-4 w-4" />
            {exporting === "excel" ? t("common.loading") : t("reports.export_excel")}
          </button>
          <button
            onClick={handleExportPdf}
            disabled={!!exporting || data.length === 0}
            className="btn-primary flex items-center gap-1.5 text-sm disabled:opacity-50"
          >
            <DocumentTextIcon className="h-4 w-4" />
            {exporting === "pdf" ? t("common.loading") : t("reports.export_pdf")}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <FunnelIcon className="h-5 w-5 text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
            {t("reports.filters")}
          </h3>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
              {t("reports.date_from")}
            </label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="input-field w-full"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
              {t("reports.date_to")}
            </label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="input-field w-full"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
              {t("attendance.status")}
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input-field w-full"
            >
              <option value="">{t("approvals.all")}</option>
              <option value="PRESENT">{t("attendance.present")}</option>
              <option value="ABSENT">{t("attendance.absent")}</option>
              <option value="LATE">{t("attendance.late")}</option>
              <option value="EARLY_DEPARTURE">{t("attendance.early_departure")}</option>
              <option value="HALF_DAY">{t("attendance.half_day")}</option>
              <option value="ON_LEAVE">{t("attendance.on_leave")}</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
              {t("reports.report_type")}
            </label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value as ReportType)}
              className="input-field w-full"
            >
              <option value="summary">{t("reports.type_summary")}</option>
              <option value="detailed">{t("reports.type_detailed")}</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <LoadingSpinner className="py-24" />
      ) : data.length === 0 ? (
        <div className="card py-16 text-center">
          <ArrowDownTrayIcon className="mx-auto h-12 w-12 text-gray-300 dark:text-gray-600" />
          <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">
            {t("reports.no_data")}
          </p>
        </div>
      ) : (
        <div className="card overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-sm">
            <thead>
              <tr className="text-start text-xs uppercase text-gray-500 dark:text-gray-400">
                {headers.map((h) => (
                  <th key={h} className="px-3 py-2">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>{data.map((row, idx) => renderRow(row, idx))}</tbody>
          </table>
          <div className="mt-4 text-xs text-gray-400 dark:text-gray-500">
            {t("reports.showing_records", { count: data.length })}
          </div>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    PRESENT: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    ABSENT: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
    LATE: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
    EARLY_DEPARTURE: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
    HALF_DAY: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
    ON_LEAVE: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
  };
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${colors[status] ?? "bg-gray-100 text-gray-800"}`}>
      {status.replace("_", " ")}
    </span>
  );
}
