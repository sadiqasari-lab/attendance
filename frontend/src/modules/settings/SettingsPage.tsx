import { useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "@/store/authStore";
import { useThemeStore } from "@/store/themeStore";
import { authService } from "@/services/auth.service";

interface PasswordForm {
  old_password: string;
  new_password: string;
  new_password_confirm: string;
}

export function SettingsPage() {
  const { t, i18n } = useTranslation();
  const { user, loadProfile } = useAuthStore();
  const { theme, setTheme, language, setLanguage } = useThemeStore();
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PasswordForm>();

  const onPasswordChange = async (data: PasswordForm) => {
    setSuccessMsg("");
    setErrorMsg("");
    if (data.new_password !== data.new_password_confirm) {
      setErrorMsg("Passwords do not match");
      return;
    }
    try {
      await authService.changePassword(data);
      setSuccessMsg(t("common.success"));
      reset();
    } catch {
      setErrorMsg(t("common.error"));
    }
  };

  const handleLanguageChange = (lang: "en" | "ar") => {
    setLanguage(lang);
    i18n.changeLanguage(lang);
  };

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white">
        {t("settings.title")}
      </h2>

      {/* Profile Section */}
      <div className="card space-y-4">
        <h3 className="text-base font-semibold text-gray-900 dark:text-white">
          {t("settings.profile")}
        </h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-500 dark:text-gray-400">Name</p>
            <p className="font-medium text-gray-900 dark:text-white">
              {user?.full_name}
            </p>
          </div>
          <div>
            <p className="text-gray-500 dark:text-gray-400">Email</p>
            <p className="font-medium text-gray-900 dark:text-white">{user?.email}</p>
          </div>
          <div>
            <p className="text-gray-500 dark:text-gray-400">Role</p>
            <p className="font-medium text-gray-900 dark:text-white">
              {user?.role?.replace("_", " ")}
            </p>
          </div>
          <div>
            <p className="text-gray-500 dark:text-gray-400">Phone</p>
            <p className="font-medium text-gray-900 dark:text-white">
              {user?.phone || "-"}
            </p>
          </div>
        </div>
      </div>

      {/* Theme & Language */}
      <div className="card space-y-4">
        <h3 className="text-base font-semibold text-gray-900 dark:text-white">
          {t("settings.theme")} & {t("settings.language")}
        </h3>
        <div className="flex flex-wrap gap-4">
          <div>
            <label className="mb-1 block text-sm text-gray-500 dark:text-gray-400">
              {t("settings.theme")}
            </label>
            <select
              value={theme}
              onChange={(e) => setTheme(e.target.value as "light" | "dark")}
              className="input-field w-40"
            >
              <option value="light">{t("settings.light_mode")}</option>
              <option value="dark">{t("settings.dark_mode")}</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm text-gray-500 dark:text-gray-400">
              {t("settings.language")}
            </label>
            <select
              value={language}
              onChange={(e) => handleLanguageChange(e.target.value as "en" | "ar")}
              className="input-field w-40"
            >
              <option value="en">English</option>
              <option value="ar">العربية</option>
            </select>
          </div>
        </div>
      </div>

      {/* Password Change */}
      <div className="card space-y-4">
        <h3 className="text-base font-semibold text-gray-900 dark:text-white">
          {t("settings.change_password")}
        </h3>

        {successMsg && (
          <div className="rounded-lg bg-green-50 px-4 py-2 text-sm text-green-700 dark:bg-green-900/20 dark:text-green-400">
            {successMsg}
          </div>
        )}
        {errorMsg && (
          <div className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit(onPasswordChange)} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Current Password
            </label>
            <input
              type="password"
              className="input-field"
              {...register("old_password", { required: true })}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              New Password
            </label>
            <input
              type="password"
              className="input-field"
              {...register("new_password", { required: true, minLength: 10 })}
            />
            {errors.new_password && (
              <p className="mt-1 text-xs text-red-600">
                Minimum 10 characters required
              </p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Confirm New Password
            </label>
            <input
              type="password"
              className="input-field"
              {...register("new_password_confirm", { required: true })}
            />
          </div>
          <button type="submit" className="btn-primary">
            {t("settings.save")}
          </button>
        </form>
      </div>
    </div>
  );
}
