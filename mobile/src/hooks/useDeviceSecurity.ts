import {useState, useEffect, useCallback} from 'react';
import DeviceInfo from 'react-native-device-info';
import {Platform} from 'react-native';
import {secureStorage} from '@/utils/storage';
import {STORAGE_KEYS} from '@/utils/constants';
import {deviceService} from '@/services/device.service';
import type {DeviceInfo as DeviceInfoType, DevicePlatform} from '@/types';

interface DeviceSecurityState {
  deviceId: string | null;
  isRooted: boolean;
  isRegistered: boolean;
  isChecking: boolean;
  error: string | null;
}

interface UseDeviceSecurityReturn extends DeviceSecurityState {
  checkSecurity: () => Promise<void>;
  registerDevice: () => Promise<void>;
  getDeviceInfo: () => Promise<DeviceInfoType>;
}

export function useDeviceSecurity(): UseDeviceSecurityReturn {
  const [state, setState] = useState<DeviceSecurityState>({
    deviceId: null,
    isRooted: false,
    isRegistered: false,
    isChecking: true,
    error: null,
  });

  const getDeviceInfo = useCallback(async (): Promise<DeviceInfoType> => {
    const [uniqueId, deviceName, systemVersion] = await Promise.all([
      DeviceInfo.getUniqueId(),
      DeviceInfo.getDeviceName(),
      DeviceInfo.getSystemVersion(),
    ]);

    const isEmulator = await DeviceInfo.isEmulator();
    const version = DeviceInfo.getVersion();

    return {
      device_id: uniqueId,
      device_name: deviceName,
      platform: (Platform.OS === 'ios' ? 'IOS' : 'ANDROID') as DevicePlatform,
      os_version: systemVersion,
      app_version: version,
      is_rooted: isEmulator, // Emulators treated as rooted in production
    };
  }, []);

  const checkSecurity = useCallback(async () => {
    setState(prev => ({...prev, isChecking: true, error: null}));

    try {
      const uniqueId = await DeviceInfo.getUniqueId();
      const isRooted = __DEV__ ? false : await DeviceInfo.isEmulator();

      const storedDeviceId = await secureStorage.get(STORAGE_KEYS.DEVICE_ID);
      const isRegistered = storedDeviceId === uniqueId;

      setState({
        deviceId: uniqueId,
        isRooted,
        isRegistered,
        isChecking: false,
        error: isRooted ? 'Device appears to be rooted or an emulator' : null,
      });

      if (isRooted) {
        await deviceService.reportRootStatus(uniqueId, true);
      }
    } catch (err: any) {
      setState(prev => ({
        ...prev,
        isChecking: false,
        error: 'Failed to check device security',
      }));
    }
  }, []);

  const registerDevice = useCallback(async () => {
    setState(prev => ({...prev, isChecking: true, error: null}));

    try {
      const info = await getDeviceInfo();
      await deviceService.register(info);
      await secureStorage.set(STORAGE_KEYS.DEVICE_ID, info.device_id);

      setState(prev => ({
        ...prev,
        deviceId: info.device_id,
        isRegistered: true,
        isChecking: false,
      }));
    } catch (err: any) {
      const message =
        err.response?.data?.detail || 'Failed to register device';
      setState(prev => ({
        ...prev,
        isChecking: false,
        error: message,
      }));
      throw new Error(message);
    }
  }, [getDeviceInfo]);

  useEffect(() => {
    checkSecurity();
  }, [checkSecurity]);

  return {
    ...state,
    checkSecurity,
    registerDevice,
    getDeviceInfo,
  };
}
