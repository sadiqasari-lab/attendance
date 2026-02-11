import api from './api';
import {secureStorage} from '@/utils/storage';
import {STORAGE_KEYS} from '@/utils/constants';
import type {AuthTokens, LoginPayload, User} from '@/types';

export const authService = {
  async login(payload: LoginPayload): Promise<{tokens: AuthTokens; user: User}> {
    const response = await api.post('/auth/login/', payload);
    const {access, refresh, user} = response.data;

    await secureStorage.set(STORAGE_KEYS.ACCESS_TOKEN, access);
    await secureStorage.set(STORAGE_KEYS.REFRESH_TOKEN, refresh);
    await secureStorage.setObject(STORAGE_KEYS.USER_DATA, user);

    if (user.tenant_slug) {
      await secureStorage.set(STORAGE_KEYS.TENANT_SLUG, user.tenant_slug);
    }

    return {tokens: {access, refresh}, user};
  },

  async logout(): Promise<void> {
    try {
      const refresh = await secureStorage.get(STORAGE_KEYS.REFRESH_TOKEN);
      if (refresh) {
        await api.post('/auth/logout/', {refresh});
      }
    } catch {
      // Ignore logout API errors
    } finally {
      await secureStorage.remove(STORAGE_KEYS.ACCESS_TOKEN);
      await secureStorage.remove(STORAGE_KEYS.REFRESH_TOKEN);
      await secureStorage.remove(STORAGE_KEYS.USER_DATA);
      await secureStorage.remove(STORAGE_KEYS.TENANT_SLUG);
    }
  },

  async getProfile(): Promise<User> {
    const response = await api.get('/auth/profile/');
    return response.data;
  },

  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await api.post('/auth/password/change/', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },

  async getStoredUser(): Promise<User | null> {
    return secureStorage.getObject<User>(STORAGE_KEYS.USER_DATA);
  },

  async isAuthenticated(): Promise<boolean> {
    const token = await secureStorage.get(STORAGE_KEYS.ACCESS_TOKEN);
    return !!token;
  },

  async getTenantSlug(): Promise<string | null> {
    return secureStorage.get(STORAGE_KEYS.TENANT_SLUG);
  },
};
