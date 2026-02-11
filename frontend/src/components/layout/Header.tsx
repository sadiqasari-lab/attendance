import { useTranslation } from "react-i18next";
import { useAuthStore } from "@/store/authStore";
import { useThemeStore } from "@/store/themeStore";
import {
  SunIcon,
  MoonIcon,
  LanguageIcon,
  ArrowRightOnRectangleIcon,
} from "@heroicons/react/24/outline";

export function Header() {
  const { t, i18n } = useTranslation();
  const { logout, user } = useAuthStore();
  const { theme, toggleTheme, language, setLanguage } = useThemeStore();

  const handleLanguageToggle = () => {
    const next = language === "en" ? "ar" : "en";
    setLanguage(next);
    i18n.changeLanguage(next);
  };

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-gray-200 bg-white/80 px-6 backdrop-blur dark:border-gray-700 dark:bg-gray-800/80">
      <div>
        <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
          {t("app.title")}
        </h1>
      </div>

      <div className="flex items-center gap-2">
        {/* Language toggle */}
        <button
          onClick={handleLanguageToggle}
          className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
          title={t("settings.language")}
        >
          <LanguageIcon className="h-5 w-5" />
        </button>

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
          title={theme === "dark" ? t("settings.light_mode") : t("settings.dark_mode")}
        >
          {theme === "dark" ? (
            <SunIcon className="h-5 w-5" />
          ) : (
            <MoonIcon className="h-5 w-5" />
          )}
        </button>

        {/* Logout */}
        <button
          onClick={() => logout()}
          className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
        >
          <ArrowRightOnRectangleIcon className="h-5 w-5" />
          <span className="hidden sm:inline">{t("nav.logout")}</span>
        </button>
      </div>
    </header>
  );
}
