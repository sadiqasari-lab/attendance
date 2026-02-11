import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import { DataTable } from "@/components/common/DataTable";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import api from "@/services/api";
import type { DeviceRegistry, PaginatedResponse } from "@/types";

export function DevicesPage() {
  const { t } = useTranslation();
  const { tenantSlug } = useParams<{ tenantSlug: string }>();
  const [devices, setDevices] = useState<DeviceRegistry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tenantSlug) return;
    setLoading(true);
    api
      .get<PaginatedResponse<DeviceRegistry>>(`/${tenantSlug}/devices/list/`)
      .then((res) => setDevices(res.data.results ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [tenantSlug]);

  const handleAction = async (deviceId: string, action: "approve" | "revoke") => {
    if (!tenantSlug) return;
    await api.post(`/${tenantSlug}/devices/${deviceId}/approve/`, { action });
    // Reload
    const res = await api.get<PaginatedResponse<DeviceRegistry>>(
      `/${tenantSlug}/devices/list/`
    );
    setDevices(res.data.results ?? []);
  };

  const statusBadge = (status: string) => {
    const styles: Record<string, string> = {
      ACTIVE: "badge-present",
      PENDING: "badge-pending",
      REVOKED: "badge-absent",
      REPLACED: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300",
    };
    return <span className={`badge ${styles[status] ?? ""}`}>{status}</span>;
  };

  const columns = [
    { key: "employee_name", header: t("attendance.employee") },
    { key: "device_model", header: t("admin.devices.model") },
    { key: "platform", header: t("admin.devices.platform") },
    { key: "device_type", header: t("admin.devices.type") },
    {
      key: "status",
      header: t("admin.devices.status"),
      render: (d: DeviceRegistry) => statusBadge(d.status),
    },
    {
      key: "actions",
      header: t("common.actions"),
      render: (d: DeviceRegistry) =>
        d.status === "PENDING" ? (
          <div className="flex gap-2">
            <button
              onClick={() => handleAction(d.id, "approve")}
              className="text-xs text-green-600 hover:underline"
            >
              {t("admin.devices.approve")}
            </button>
            <button
              onClick={() => handleAction(d.id, "revoke")}
              className="text-xs text-red-600 hover:underline"
            >
              {t("admin.devices.revoke")}
            </button>
          </div>
        ) : d.status === "ACTIVE" ? (
          <button
            onClick={() => handleAction(d.id, "revoke")}
            className="text-xs text-red-600 hover:underline"
          >
            {t("admin.devices.revoke")}
          </button>
        ) : null,
    },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white">
        {t("admin.devices.title")}
      </h2>
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <LoadingSpinner className="py-12" />
        ) : (
          <DataTable columns={columns} data={devices} keyExtractor={(d) => d.id} />
        )}
      </div>
    </div>
  );
}
