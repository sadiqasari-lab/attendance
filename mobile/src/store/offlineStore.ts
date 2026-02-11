import {create} from 'zustand';
import {secureStorage} from '@/utils/storage';
import {STORAGE_KEYS, OFFLINE_CONFIG} from '@/utils/constants';
import {attendanceService} from '@/services/attendance.service';
import type {OfflineAttendancePayload} from '@/types';

interface OfflineRecord {
  id: string;
  payload: OfflineAttendancePayload;
  createdAt: string;
  synced: boolean;
  syncError?: string;
}

interface OfflineState {
  queue: OfflineRecord[];
  isSyncing: boolean;
  lastSyncAt: string | null;

  addToQueue: (payload: OfflineAttendancePayload) => Promise<boolean>;
  syncAll: () => Promise<{synced: number; failed: number}>;
  loadQueue: () => Promise<void>;
  clearSynced: () => Promise<void>;
}

export const useOfflineStore = create<OfflineState>((set, get) => ({
  queue: [],
  isSyncing: false,
  lastSyncAt: null,

  addToQueue: async (payload) => {
    const {queue} = get();
    if (queue.length >= OFFLINE_CONFIG.MAX_QUEUE_SIZE) {
      return false;
    }

    const record: OfflineRecord = {
      id: `offline_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
      payload,
      createdAt: new Date().toISOString(),
      synced: false,
    };

    const updated = [...queue, record];
    set({queue: updated});
    await secureStorage.setObject(STORAGE_KEYS.OFFLINE_QUEUE, updated);
    return true;
  },

  syncAll: async () => {
    const {queue} = get();
    const pending = queue.filter(r => !r.synced);

    if (pending.length === 0) {
      return {synced: 0, failed: 0};
    }

    set({isSyncing: true});
    let synced = 0;
    let failed = 0;

    const updated = [...queue];

    for (const record of pending) {
      try {
        await attendanceService.syncOfflineRecord(record.payload);
        const idx = updated.findIndex(r => r.id === record.id);
        if (idx !== -1) {
          updated[idx] = {...updated[idx], synced: true};
        }
        synced++;
      } catch (err: any) {
        const idx = updated.findIndex(r => r.id === record.id);
        if (idx !== -1) {
          updated[idx] = {
            ...updated[idx],
            syncError:
              err.response?.data?.detail || 'Sync failed',
          };
        }
        failed++;
      }
    }

    set({
      queue: updated,
      isSyncing: false,
      lastSyncAt: new Date().toISOString(),
    });
    await secureStorage.setObject(STORAGE_KEYS.OFFLINE_QUEUE, updated);

    return {synced, failed};
  },

  loadQueue: async () => {
    const stored = await secureStorage.getObject<OfflineRecord[]>(
      STORAGE_KEYS.OFFLINE_QUEUE,
    );
    if (stored) {
      set({queue: stored});
    }
  },

  clearSynced: async () => {
    const {queue} = get();
    const remaining = queue.filter(r => !r.synced);
    set({queue: remaining});
    await secureStorage.setObject(STORAGE_KEYS.OFFLINE_QUEUE, remaining);
  },
}));
