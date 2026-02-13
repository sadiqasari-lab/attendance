import { describe, it, expect, beforeEach, vi } from "vitest";
import { useAuthStore } from "../authStore";

// Mock the auth service
vi.mock("@/services/auth.service", () => ({
  authService: {
    login: vi.fn(),
    logout: vi.fn(),
    getProfile: vi.fn(),
  },
}));

// Mock the api module
vi.mock("@/services/api", () => ({
  default: {},
  getAccessToken: vi.fn(() => null),
  getRefreshToken: vi.fn(() => null),
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
}));

describe("authStore", () => {
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

  it("has correct initial state", () => {
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it("setTenant stores tenant in state and localStorage", () => {
    const tenant = { id: "t1", name: "Acme", slug: "acme" };
    useAuthStore.getState().setTenant(tenant);

    const state = useAuthStore.getState();
    expect(state.tenant).toEqual(tenant);
    expect(localStorage.getItem("inspire_tenant")).toBe(JSON.stringify(tenant));
  });

  it("clearError clears the error state", () => {
    useAuthStore.setState({ error: "Something went wrong" });
    expect(useAuthStore.getState().error).toBe("Something went wrong");

    useAuthStore.getState().clearError();
    expect(useAuthStore.getState().error).toBeNull();
  });

  it("logout clears all auth state", async () => {
    useAuthStore.setState({
      user: { id: "1", email: "a@b.com" } as never,
      tenant: { id: "t1", name: "T", slug: "t" },
      isAuthenticated: true,
    });

    await useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.tenant).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(localStorage.getItem("inspire_tenant")).toBeNull();
  });
});
