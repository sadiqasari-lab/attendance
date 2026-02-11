/**
 * Theme and language store — Dark/Light mode + RTL Arabic support.
 */
import { create } from "zustand";

type Theme = "light" | "dark";
type Language = "en" | "ar";

interface ThemeState {
  theme: Theme;
  language: Language;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
  setLanguage: (lang: Language) => void;
}

function getInitialTheme(): Theme {
  const stored = localStorage.getItem("inspire_theme") as Theme | null;
  if (stored) return stored;
  if (window.matchMedia("(prefers-color-scheme: dark)").matches) return "dark";
  return "light";
}

function getInitialLanguage(): Language {
  return (localStorage.getItem("inspire_language") as Language) ?? "en";
}

function applyTheme(theme: Theme): void {
  document.documentElement.classList.toggle("dark", theme === "dark");
  localStorage.setItem("inspire_theme", theme);
}

function applyLanguage(lang: Language): void {
  document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
  document.documentElement.lang = lang;
  localStorage.setItem("inspire_language", lang);
}

// Apply on load
const initialTheme = getInitialTheme();
const initialLanguage = getInitialLanguage();
applyTheme(initialTheme);
applyLanguage(initialLanguage);

export const useThemeStore = create<ThemeState>((set) => ({
  theme: initialTheme,
  language: initialLanguage,

  toggleTheme: () =>
    set((state) => {
      const next = state.theme === "light" ? "dark" : "light";
      applyTheme(next);
      return { theme: next };
    }),

  setTheme: (theme) => {
    applyTheme(theme);
    set({ theme });
  },

  setLanguage: (language) => {
    applyLanguage(language);
    set({ language });
  },
}));
