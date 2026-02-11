import {useEffect, useRef, useCallback} from 'react';
import NetInfo from '@react-native-community/netinfo';
import {useOfflineStore} from '@/store/offlineStore';
import {OFFLINE_CONFIG} from '@/utils/constants';

interface UseOfflineSyncReturn {
  isOnline: boolean;
  pendingCount: number;
  isSyncing: boolean;
  syncNow: () => Promise<{synced: number; failed: number}>;
}

export function useOfflineSync(): UseOfflineSyncReturn {
  const isOnlineRef = useRef(true);
  const syncIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const {queue, isSyncing, syncAll, loadQueue, clearSynced} =
    useOfflineStore();

  const pendingCount = queue.filter(r => !r.synced).length;

  const syncNow = useCallback(async () => {
    const result = await syncAll();
    if (result.synced > 0) {
      await clearSynced();
    }
    return result;
  }, [syncAll, clearSynced]);

  useEffect(() => {
    loadQueue();

    const unsubscribe = NetInfo.addEventListener(state => {
      const wasOffline = !isOnlineRef.current;
      isOnlineRef.current = !!state.isConnected;

      // Auto-sync when coming back online
      if (wasOffline && state.isConnected && pendingCount > 0) {
        syncNow();
      }
    });

    // Periodic sync attempt
    syncIntervalRef.current = setInterval(() => {
      if (isOnlineRef.current && pendingCount > 0) {
        syncNow();
      }
    }, OFFLINE_CONFIG.SYNC_INTERVAL_MS);

    return () => {
      unsubscribe();
      if (syncIntervalRef.current) {
        clearInterval(syncIntervalRef.current);
      }
    };
  }, [loadQueue, syncNow, pendingCount]);

  return {
    isOnline: isOnlineRef.current,
    pendingCount,
    isSyncing,
    syncNow,
  };
}
