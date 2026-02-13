import { describe, it, expect, beforeEach } from "vitest";
import { getAccessToken, getRefreshToken, setTokens, clearTokens } from "../api";

describe("API token helpers", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("getAccessToken returns null when no token is stored", () => {
    expect(getAccessToken()).toBeNull();
  });

  it("getRefreshToken returns null when no token is stored", () => {
    expect(getRefreshToken()).toBeNull();
  });

  it("setTokens stores both access and refresh tokens", () => {
    setTokens("access-123", "refresh-456");
    expect(getAccessToken()).toBe("access-123");
    expect(getRefreshToken()).toBe("refresh-456");
  });

  it("clearTokens removes both tokens", () => {
    setTokens("a", "r");
    clearTokens();
    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
  });

  it("setTokens overwrites existing tokens", () => {
    setTokens("old-access", "old-refresh");
    setTokens("new-access", "new-refresh");
    expect(getAccessToken()).toBe("new-access");
    expect(getRefreshToken()).toBe("new-refresh");
  });
});
