import api from './api';
import {authService} from './auth.service';
import type {
  AttendanceRecord,
  AttendanceSummary,
  ClockInPayload,
  ClockOutPayload,
  OfflineAttendancePayload,
  PaginatedResponse,
  Shift,
} from '@/types';

async function getTenantPrefix(): Promise<string> {
  const slug = await authService.getTenantSlug();
  return slug ? `/${slug}` : '';
}

export const attendanceService = {
  async getShifts(): Promise<Shift[]> {
    const prefix = await getTenantPrefix();
    const response = await api.get<PaginatedResponse<Shift>>(
      `${prefix}/attendance/shifts/`,
    );
    return response.data.results;
  },

  async clockIn(payload: ClockInPayload): Promise<AttendanceRecord> {
    const prefix = await getTenantPrefix();
    const response = await api.post<AttendanceRecord>(
      `${prefix}/attendance/clock-in/`,
      payload,
    );
    return response.data;
  },

  async clockOut(payload: ClockOutPayload): Promise<AttendanceRecord> {
    const prefix = await getTenantPrefix();
    const response = await api.post<AttendanceRecord>(
      `${prefix}/attendance/clock-out/`,
      payload,
    );
    return response.data;
  },

  async syncOfflineRecord(
    payload: OfflineAttendancePayload,
  ): Promise<AttendanceRecord> {
    const prefix = await getTenantPrefix();
    const response = await api.post<AttendanceRecord>(
      `${prefix}/attendance/offline-sync/`,
      payload,
    );
    return response.data;
  },

  async getRecords(params?: {
    start_date?: string;
    end_date?: string;
    status?: string;
    page?: number;
  }): Promise<PaginatedResponse<AttendanceRecord>> {
    const prefix = await getTenantPrefix();
    const response = await api.get<PaginatedResponse<AttendanceRecord>>(
      `${prefix}/attendance/records/`,
      {params},
    );
    return response.data;
  },

  async getSummary(params: {
    start_date: string;
    end_date: string;
  }): Promise<AttendanceSummary> {
    const prefix = await getTenantPrefix();
    const response = await api.get<AttendanceSummary>(
      `${prefix}/attendance/summary/`,
      {params},
    );
    return response.data;
  },
};
