import { describe, it, expect, beforeEach } from "vitest";
import { useThemeStore } from "../themeStore";

describe("themeStore", () => {
  beforeEach(() => {
    localStorage.clear();
    // Reset to known state
    useThemeStore.setState({ theme: "light", language: "en" });
  });

  it("toggleTheme switches from light to dark", () => {
    useThemeStore.getState().toggleTheme();
    expect(useThemeStore.getState().theme).toBe("dark");
  });

  it("toggleTheme switches from dark to light", () => {
    useThemeStore.setState({ theme: "dark" });
    useThemeStore.getState().toggleTheme();
    expect(useThemeStore.getState().theme).toBe("light");
  });

  it("setTheme sets the theme directly", () => {
    useThemeStore.getState().setTheme("dark");
    expect(useThemeStore.getState().theme).toBe("dark");
    expect(localStorage.getItem("inspire_theme")).toBe("dark");
  });

  it("setLanguage changes the language", () => {
    useThemeStore.getState().setLanguage("ar");
    expect(useThemeStore.getState().language).toBe("ar");
    expect(localStorage.getItem("inspire_language")).toBe("ar");
  });

  it("setLanguage to ar sets RTL direction", () => {
    useThemeStore.getState().setLanguage("ar");
    expect(document.documentElement.dir).toBe("rtl");
    expect(document.documentElement.lang).toBe("ar");
  });

  it("setLanguage to en sets LTR direction", () => {
    useThemeStore.getState().setLanguage("en");
    expect(document.documentElement.dir).toBe("ltr");
    expect(document.documentElement.lang).toBe("en");
  });
});
