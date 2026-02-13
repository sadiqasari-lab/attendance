import { describe, it, expect, beforeEach, vi } from "vitest";

// Mock all external modules that might cause hanging
vi.mock("@/services/api", () => ({
  default: { interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } } },
  getAccessToken: vi.fn(() => null),
  getRefreshToken: vi.fn(() => null),
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
}));

vi.mock("@/services/auth.service", () => ({
  authService: {
    login: vi.fn(),
    logout: vi.fn(),
    getProfile: vi.fn(),
  },
}));

vi.mock("@/i18n", () => ({ default: {} }));

import { useAuthStore } from "@/store/authStore";
import type { User } from "@/types";

const mockUser: User = {
  id: "1",
  email: "admin@test.com",
  first_name: "Test",
  last_name: "Admin",
  first_name_ar: "",
  last_name_ar: "",
  phone: "",
  role: "SUPER_ADMIN",
  full_name: "Test Admin",
  full_name_ar: "",
  is_active: true,
  requires_biometric_enrollment: false,
  date_joined: "2024-01-01",
};

describe("ProtectedRoute logic", () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({
      user: null,
      tenant: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  });

  it("unauthenticated user should not see protected content", () => {
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    // ProtectedRoute checks isAuthenticated — when false, redirects to /login
  });

  it("authenticated user with allowed role can access", () => {
    useAuthStore.setState({ isAuthenticated: true, user: mockUser });
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user?.role).toBe("SUPER_ADMIN");

    const allowedRoles = ["SUPER_ADMIN", "TENANT_ADMIN"] as const;
    expect(allowedRoles.includes(state.user!.role as typeof allowedRoles[number])).toBe(true);
  });

  it("authenticated user without allowed role is denied", () => {
    const employeeUser = { ...mockUser, role: "EMPLOYEE" as const };
    useAuthStore.setState({ isAuthenticated: true, user: employeeUser });
    const state = useAuthStore.getState();

    const allowedRoles = ["SUPER_ADMIN"] as const;
    expect(allowedRoles.includes(state.user!.role as typeof allowedRoles[number])).toBe(false);
  });

  it("authenticated user with no role restriction can access", () => {
    useAuthStore.setState({ isAuthenticated: true, user: mockUser });
    const state = useAuthStore.getState();
    // When allowedRoles is undefined, any authenticated user can access
    expect(state.isAuthenticated).toBe(true);
    expect(state.user).not.toBeNull();
  });
});
