import api from './api';
import {authService} from './auth.service';
import type {DeviceInfo} from '@/types';

async function getTenantPrefix(): Promise<string> {
  const slug = await authService.getTenantSlug();
  return slug ? `/${slug}` : '';
}

export const deviceService = {
  async register(deviceInfo: DeviceInfo): Promise<{id: string; status: string}> {
    const prefix = await getTenantPrefix();
    const response = await api.post(`${prefix}/devices/register/`, deviceInfo);
    return response.data;
  },

  async reportRootStatus(
    deviceId: string,
    isRooted: boolean,
  ): Promise<void> {
    const prefix = await getTenantPrefix();
    await api.post(`${prefix}/devices/root-detection/`, {
      device_id: deviceId,
      is_rooted: isRooted,
    });
  },

  async requestChange(
    reason: string,
    newDeviceInfo: DeviceInfo,
  ): Promise<{id: string}> {
    const prefix = await getTenantPrefix();
    const response = await api.post(`${prefix}/devices/change-requests/`, {
      reason,
      new_device: newDeviceInfo,
    });
    return response.data;
  },
};
