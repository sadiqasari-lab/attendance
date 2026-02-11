/**
 * Attendance service — records, shifts, policies, geofences, corrections, summary.
 */
import type {
  ApiResponse,
  AttendancePolicy,
  AttendanceRecord,
  AttendanceSummary,
  CorrectionRequest,
  Geofence,
  PaginatedResponse,
  Shift,
} from "@/types";
import api from "./api";

function tenantUrl(tenantSlug: string, path: string): string {
  return `/${tenantSlug}/attendance/${path}`;
}

export const attendanceService = {
  // --- Shifts ---
  async getShifts(tenantSlug: string): Promise<PaginatedResponse<Shift>> {
    const { data } = await api.get(tenantUrl(tenantSlug, "shifts/"));
    return data;
  },
  async createShift(tenantSlug: string, payload: Partial<Shift>): Promise<Shift> {
    const { data } = await api.post(tenantUrl(tenantSlug, "shifts/"), payload);
    return data;
  },
  async updateShift(tenantSlug: string, id: string, payload: Partial<Shift>): Promise<Shift> {
    const { data } = await api.patch(tenantUrl(tenantSlug, `shifts/${id}/`), payload);
    return data;
  },
  async deleteShift(tenantSlug: string, id: string): Promise<void> {
    await api.delete(tenantUrl(tenantSlug, `shifts/${id}/`));
  },

  // --- Policies ---
  async getPolicies(tenantSlug: string): Promise<PaginatedResponse<AttendancePolicy>> {
    const { data } = await api.get(tenantUrl(tenantSlug, "policies/"));
    return data;
  },
  async createPolicy(tenantSlug: string, payload: Partial<AttendancePolicy>): Promise<AttendancePolicy> {
    const { data } = await api.post(tenantUrl(tenantSlug, "policies/"), payload);
    return data;
  },

  // --- Geofences ---
  async getGeofences(tenantSlug: string): Promise<PaginatedResponse<Geofence>> {
    const { data } = await api.get(tenantUrl(tenantSlug, "geofences/"));
    return data;
  },
  async createGeofence(tenantSlug: string, payload: Partial<Geofence>): Promise<Geofence> {
    const { data } = await api.post(tenantUrl(tenantSlug, "geofences/"), payload);
    return data;
  },
  async updateGeofence(tenantSlug: string, id: string, payload: Partial<Geofence>): Promise<Geofence> {
    const { data } = await api.patch(tenantUrl(tenantSlug, `geofences/${id}/`), payload);
    return data;
  },
  async deleteGeofence(tenantSlug: string, id: string): Promise<void> {
    await api.delete(tenantUrl(tenantSlug, `geofences/${id}/`));
  },

  // --- Records ---
  async getRecords(
    tenantSlug: string,
    params?: Record<string, string>
  ): Promise<PaginatedResponse<AttendanceRecord>> {
    const { data } = await api.get(tenantUrl(tenantSlug, "records/"), { params });
    return data;
  },

  // --- Summary ---
  async getSummary(
    tenantSlug: string,
    params?: Record<string, string>
  ): Promise<ApiResponse<AttendanceSummary[]>> {
    const { data } = await api.get(tenantUrl(tenantSlug, "summary/"), { params });
    return data;
  },

  // --- Corrections ---
  async getCorrections(tenantSlug: string): Promise<PaginatedResponse<CorrectionRequest>> {
    const { data } = await api.get(tenantUrl(tenantSlug, "corrections/"));
    return data;
  },
  async createCorrection(tenantSlug: string, payload: Partial<CorrectionRequest>): Promise<CorrectionRequest> {
    const { data } = await api.post(tenantUrl(tenantSlug, "corrections/"), payload);
    return data;
  },
};
