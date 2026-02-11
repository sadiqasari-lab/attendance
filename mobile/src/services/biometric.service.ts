import api from './api';
import {authService} from './auth.service';
import type {BiometricTemplate} from '@/types';

async function getTenantPrefix(): Promise<string> {
  const slug = await authService.getTenantSlug();
  return slug ? `/${slug}` : '';
}

export const biometricService = {
  async enroll(images: string[]): Promise<BiometricTemplate> {
    const prefix = await getTenantPrefix();
    const response = await api.post<BiometricTemplate>(
      `${prefix}/biometric/enroll/`,
      {images},
    );
    return response.data;
  },

  async verify(image: string): Promise<{match: boolean; score: number}> {
    const prefix = await getTenantPrefix();
    const response = await api.post<{match: boolean; score: number}>(
      `${prefix}/biometric/verify/`,
      {image},
    );
    return response.data;
  },

  async revoke(): Promise<void> {
    const prefix = await getTenantPrefix();
    await api.post(`${prefix}/biometric/revoke/`);
  },

  async deleteData(): Promise<void> {
    const prefix = await getTenantPrefix();
    await api.delete(`${prefix}/biometric/delete/`);
  },
};
