/**
 * Reports service — fetch report data and trigger file exports.
 */
import api from "./api";

function tenantUrl(tenantSlug: string, path: string): string {
  return `/${tenantSlug}/attendance/${path}`;
}

export interface ReportParams {
  date_from?: string;
  date_to?: string;
  status?: string;
  department?: string;
  employee_id?: string;
  type?: "summary" | "detailed";
}

export const reportsService = {
  async getReport(tenantSlug: string, params: ReportParams) {
    const { data } = await api.get(tenantUrl(tenantSlug, "reports/"), { params });
    return data;
  },

  async exportExcel(tenantSlug: string, params: ReportParams) {
    const response = await api.get(tenantUrl(tenantSlug, "reports/export/excel/"), {
      params,
      responseType: "blob",
    });
    _downloadBlob(
      response.data,
      `attendance_report_${params.date_from}_to_${params.date_to}.xlsx`,
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    );
  },

  async exportPdf(tenantSlug: string, params: ReportParams) {
    const response = await api.get(tenantUrl(tenantSlug, "reports/export/pdf/"), {
      params,
      responseType: "blob",
    });
    _downloadBlob(
      response.data,
      `attendance_report_${params.date_from}_to_${params.date_to}.pdf`,
      "application/pdf"
    );
  },
};

function _downloadBlob(data: Blob, filename: string, mimeType: string) {
  const blob = new Blob([data], { type: mimeType });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
