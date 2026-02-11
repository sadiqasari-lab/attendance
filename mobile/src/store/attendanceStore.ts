import {create} from 'zustand';
import type {AttendanceRecord, AttendanceSummary, Shift} from '@/types';
import {attendanceService} from '@/services/attendance.service';

interface AttendanceState {
  shifts: Shift[];
  records: AttendanceRecord[];
  summary: AttendanceSummary | null;
  activeRecord: AttendanceRecord | null;
  isLoading: boolean;
  error: string | null;

  loadShifts: () => Promise<void>;
  loadRecords: (params?: {
    start_date?: string;
    end_date?: string;
  }) => Promise<void>;
  loadSummary: (startDate: string, endDate: string) => Promise<void>;
  setActiveRecord: (record: AttendanceRecord | null) => void;
  clearError: () => void;
}

export const useAttendanceStore = create<AttendanceState>((set) => ({
  shifts: [],
  records: [],
  summary: null,
  activeRecord: null,
  isLoading: false,
  error: null,

  loadShifts: async () => {
    set({isLoading: true, error: null});
    try {
      const shifts = await attendanceService.getShifts();
      set({shifts, isLoading: false});
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Failed to load shifts',
        isLoading: false,
      });
    }
  },

  loadRecords: async (params) => {
    set({isLoading: true, error: null});
    try {
      const data = await attendanceService.getRecords(params);
      set({records: data.results, isLoading: false});
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Failed to load records',
        isLoading: false,
      });
    }
  },

  loadSummary: async (startDate, endDate) => {
    set({isLoading: true, error: null});
    try {
      const summary = await attendanceService.getSummary({
        start_date: startDate,
        end_date: endDate,
      });
      set({summary, isLoading: false});
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Failed to load summary',
        isLoading: false,
      });
    }
  },

  setActiveRecord: (record) => set({activeRecord: record}),
  clearError: () => set({error: null}),
}));
