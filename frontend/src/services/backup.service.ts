/**
 * Backup & Restore service.
 */
import api from "./api";

export interface BackupInfo {
  filename: string;
  size_bytes: number;
  size_display: string;
  created_at: string;
}

export const backupService = {
  async list(): Promise<BackupInfo[]> {
    const { data } = await api.get("/backups/");
    return data.data ?? [];
  },

  async create(): Promise<BackupInfo> {
    const { data } = await api.post("/backups/create/");
    return data.data;
  },

  async download(filename: string) {
    const response = await api.get(`/backups/${filename}/download/`, {
      responseType: "blob",
    });
    const blob = new Blob([response.data], { type: "application/gzip" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },

  async restore(file: File): Promise<string> {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await api.post("/backups/restore/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data.data?.detail ?? "Restored successfully.";
  },

  async restoreFromServer(filename: string): Promise<string> {
    const formData = new FormData();
    formData.append("filename", filename);
    const { data } = await api.post("/backups/restore/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data.data?.detail ?? "Restored successfully.";
  },

  async remove(filename: string): Promise<void> {
    await api.delete(`/backups/${filename}/`);
  },
};
