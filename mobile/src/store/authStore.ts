import {create} from 'zustand';
import type {User} from '@/types';
import {authService} from '@/services/auth.service';

interface AuthState {
  user: User | null;
  tenantSlug: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  tenantSlug: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,

  login: async (email: string, password: string) => {
    set({isLoading: true, error: null});
    try {
      const {user} = await authService.login({email, password});
      const slug = await authService.getTenantSlug();
      set({
        user,
        tenantSlug: slug,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (err: any) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        'Login failed. Please check your credentials.';
      set({error: message, isLoading: false});
      throw err;
    }
  },

  logout: async () => {
    await authService.logout();
    set({
      user: null,
      tenantSlug: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  },

  loadUser: async () => {
    set({isLoading: true});
    try {
      const isAuth = await authService.isAuthenticated();
      if (!isAuth) {
        set({isLoading: false, isAuthenticated: false});
        return;
      }
      const user = await authService.getProfile();
      const slug = await authService.getTenantSlug();
      set({
        user,
        tenantSlug: slug,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch {
      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },

  clearError: () => set({error: null}),
}));
