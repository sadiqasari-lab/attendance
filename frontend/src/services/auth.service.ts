/**
 * Authentication service — login, logout, profile, password change.
 */
import type { LoginRequest, LoginResponse, User } from "@/types";
import api, { clearTokens, setTokens } from "./api";

export const authService = {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const { data } = await api.post<LoginResponse>("/auth/login/", credentials);
    const tokenData = data.data ?? (data as unknown as LoginResponse["data"]);
    setTokens(tokenData.access, tokenData.refresh);
    return data;
  },

  async logout(): Promise<void> {
    try {
      const refresh = localStorage.getItem("inspire_refresh_token");
      if (refresh) {
        await api.post("/auth/logout/", { refresh });
      }
    } finally {
      clearTokens();
    }
  },

  async getProfile(): Promise<User> {
    const { data } = await api.get("/auth/profile/");
    return data.data ?? data;
  },

  async updateProfile(payload: Partial<User>): Promise<User> {
    const { data } = await api.patch("/auth/profile/", payload);
    return data.data ?? data;
  },

  async changePassword(payload: {
    old_password: string;
    new_password: string;
    new_password_confirm: string;
  }): Promise<void> {
    await api.post("/auth/password/change/", payload);
  },
};
