/**
 * Authentication state store using Zustand.
 */
import { create } from "zustand";
import type { TenantInfo, User } from "@/types";
import { authService } from "@/services/auth.service";
import { clearTokens, getAccessToken } from "@/services/api";

interface AuthState {
  user: User | null;
  tenant: TenantInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  loadProfile: () => Promise<void>;
  setTenant: (tenant: TenantInfo) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  tenant: JSON.parse(localStorage.getItem("inspire_tenant") || "null"),
  isAuthenticated: !!getAccessToken(),
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authService.login({ email, password });
      const responseData = response.data ?? (response as unknown as typeof response.data);
      set({
        user: responseData.user,
        tenant: responseData.tenant ?? null,
        isAuthenticated: true,
        isLoading: false,
      });
      if (responseData.tenant) {
        localStorage.setItem("inspire_tenant", JSON.stringify(responseData.tenant));
      }
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Login failed. Please check your credentials.";
      set({ error: msg, isLoading: false });
      throw err;
    }
  },

  logout: async () => {
    try {
      await authService.logout();
    } finally {
      clearTokens();
      localStorage.removeItem("inspire_tenant");
      set({ user: null, tenant: null, isAuthenticated: false });
    }
  },

  loadProfile: async () => {
    try {
      const user = await authService.getProfile();
      set({ user, isAuthenticated: true });
    } catch {
      set({ isAuthenticated: false, user: null });
    }
  },

  setTenant: (tenant) => {
    localStorage.setItem("inspire_tenant", JSON.stringify(tenant));
    set({ tenant });
  },

  clearError: () => set({ error: null }),
}));
