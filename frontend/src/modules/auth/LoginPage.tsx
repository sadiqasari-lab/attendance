import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "@/store/authStore";
import { useThemeStore } from "@/store/themeStore";
import { SunIcon, MoonIcon, LanguageIcon } from "@heroicons/react/24/outline";

interface LoginForm {
  email: string;
  password: string;
}

export function LoginPage() {
  const { t, i18n } = useTranslation();
  const { login, isLoading, error, clearError } = useAuthStore();
  const { theme, toggleTheme, language, setLanguage } = useThemeStore();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname;

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>();

  const onSubmit = async (formData: LoginForm) => {
    clearError();
    try {
      await login(formData.email, formData.password);
      const tenant = useAuthStore.getState().tenant;
      navigate(from ?? `/${tenant?.slug ?? ""}/dashboard`, { replace: true });
    } catch {
      // Error handled by store
    }
  };

  const handleLanguageToggle = () => {
    const next = language === "en" ? "ar" : "en";
    setLanguage(next);
    i18n.changeLanguage(next);
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4 dark:bg-gray-900">
      {/* Top-right controls */}
      <div className="absolute end-4 top-4 flex gap-2">
        <button
          onClick={handleLanguageToggle}
          className="rounded-lg p-2 text-gray-500 hover:bg-gray-200 dark:text-gray-400 dark:hover:bg-gray-700"
        >
          <LanguageIcon className="h-5 w-5" />
        </button>
        <button
          onClick={toggleTheme}
          className="rounded-lg p-2 text-gray-500 hover:bg-gray-200 dark:text-gray-400 dark:hover:bg-gray-700"
        >
          {theme === "dark" ? (
            <SunIcon className="h-5 w-5" />
          ) : (
            <MoonIcon className="h-5 w-5" />
          )}
        </button>
      </div>

      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary-600 text-2xl font-bold text-white">
            IA
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {t("app.title")}
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {t("app.subtitle")}
          </p>
        </div>

        {/* Login Card */}
        <div className="card">
          <h2 className="mb-6 text-lg font-semibold text-gray-900 dark:text-white">
            {t("auth.login")}
          </h2>

          {error && (
            <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label
                htmlFor="email"
                className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                {t("auth.email")}
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                className="input-field"
                {...register("email", { required: true })}
              />
              {errors.email && (
                <p className="mt-1 text-xs text-red-600">Email is required</p>
              )}
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                {t("auth.password")}
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                className="input-field"
                {...register("password", { required: true })}
              />
              {errors.password && (
                <p className="mt-1 text-xs text-red-600">Password is required</p>
              )}
            </div>

            <button type="submit" disabled={isLoading} className="btn-primary w-full">
              {isLoading ? t("auth.logging_in") : t("auth.login_button")}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center text-xs text-gray-400">
          Arab Inspire Company &mdash; arabinspire.cloud
        </p>
      </div>
    </div>
  );
}
