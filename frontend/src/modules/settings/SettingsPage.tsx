import { useCallback, useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "@/store/authStore";
import { useThemeStore } from "@/store/themeStore";
import { authService } from "@/services/auth.service";
import { backupService, type BackupInfo } from "@/services/backup.service";
import {
  ArrowDownTrayIcon,
  ArrowUpTrayIcon,
  TrashIcon,
  ServerStackIcon,
  ShieldCheckIcon,
} from "@heroicons/react/24/outline";

interface PasswordForm {
  old_password: string;
  new_password: string;
  new_password_confirm: string;
}

export function SettingsPage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuthStore();
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

  // --- Backup state ---
  const isAdmin = user?.role === "SUPER_ADMIN";
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [backupLoading, setBackupLoading] = useState(false);
  const [backupCreating, setBackupCreating] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [backupMsg, setBackupMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadBackups = useCallback(async () => {
    if (!isAdmin) return;
    setBackupLoading(true);
    try {
      const list = await backupService.list();
      setBackups(list);
    } catch {
      // ignore
    } finally {
      setBackupLoading(false);
    }
  }, [isAdmin]);

  useEffect(() => {
    loadBackups();
  }, [loadBackups]);

  const handleCreateBackup = async () => {
    setBackupCreating(true);
    setBackupMsg(null);
    try {
      await backupService.create();
      setBackupMsg({ type: "success", text: t("settings.backup_created") });
      loadBackups();
    } catch {
      setBackupMsg({ type: "error", text: t("common.error") });
    } finally {
      setBackupCreating(false);
    }
  };

  const handleDownloadBackup = async (filename: string) => {
    try {
      await backupService.download(filename);
    } catch {
      // ignore
    }
  };

  const handleDeleteBackup = async (filename: string) => {
    try {
      await backupService.remove(filename);
      setBackups(backups.filter((b) => b.filename !== filename));
    } catch {
      // ignore
    }
  };

  const handleRestoreFromServer = async (filename: string) => {
    if (!confirm(t("settings.restore_confirm"))) return;
    setRestoring(true);
    setBackupMsg(null);
    try {
      await backupService.restoreFromServer(filename);
      setBackupMsg({ type: "success", text: t("settings.restore_success") });
    } catch {
      setBackupMsg({ type: "error", text: t("common.error") });
    } finally {
      setRestoring(false);
    }
  };

  const handleRestoreFromFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!confirm(t("settings.restore_confirm"))) {
      e.target.value = "";
      return;
    }
    setRestoring(true);
    setBackupMsg(null);
    try {
      await backupService.restore(file);
      setBackupMsg({ type: "success", text: t("settings.restore_success") });
      loadBackups();
    } catch {
      setBackupMsg({ type: "error", text: t("common.error") });
    } finally {
      setRestoring(false);
      e.target.value = "";
    }
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

      {/* Backup & Restore — Super Admin only */}
      {isAdmin && (
        <div className="card space-y-4">
          <div className="flex items-center gap-2">
            <ServerStackIcon className="h-5 w-5 text-gray-500 dark:text-gray-400" />
            <h3 className="text-base font-semibold text-gray-900 dark:text-white">
              {t("settings.backup_restore")}
            </h3>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {t("settings.backup_desc")}
          </p>

          {backupMsg && (
            <div
              className={`rounded-lg px-4 py-2 text-sm ${
                backupMsg.type === "success"
                  ? "bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400"
                  : "bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400"
              }`}
            >
              {backupMsg.text}
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleCreateBackup}
              disabled={backupCreating}
              className="btn-primary flex items-center gap-1.5 text-sm disabled:opacity-50"
            >
              <ShieldCheckIcon className="h-4 w-4" />
              {backupCreating ? t("common.loading") : t("settings.create_backup")}
            </button>
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={restoring}
              className="btn-secondary flex items-center gap-1.5 text-sm disabled:opacity-50"
            >
              <ArrowUpTrayIcon className="h-4 w-4" />
              {restoring ? t("common.loading") : t("settings.restore_from_file")}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json,.json.gz,.gz"
              onChange={handleRestoreFromFile}
              className="hidden"
            />
          </div>

          {/* Backup list */}
          {backupLoading ? (
            <p className="text-sm text-gray-400">{t("common.loading")}</p>
          ) : backups.length === 0 ? (
            <p className="py-4 text-center text-sm text-gray-400">
              {t("settings.no_backups")}
            </p>
          ) : (
            <div className="divide-y divide-gray-200 rounded-lg border border-gray-200 dark:divide-gray-700 dark:border-gray-700">
              {backups.map((b) => (
                <div
                  key={b.filename}
                  className="flex items-center justify-between px-4 py-3"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-gray-900 dark:text-white">
                      {b.filename}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {b.size_display} &middot; {new Date(b.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleDownloadBackup(b.filename)}
                      className="rounded p-1.5 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
                      title={t("settings.download")}
                    >
                      <ArrowDownTrayIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleRestoreFromServer(b.filename)}
                      disabled={restoring}
                      className="rounded p-1.5 text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/20 disabled:opacity-50"
                      title={t("settings.restore")}
                    >
                      <ArrowUpTrayIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteBackup(b.filename)}
                      className="rounded p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
                      title={t("common.delete")}
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
