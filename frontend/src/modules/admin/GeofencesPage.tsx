import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import { DataTable } from "@/components/common/DataTable";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { attendanceService } from "@/services/attendance.service";
import type { Geofence } from "@/types";

export function GeofencesPage() {
  const { t } = useTranslation();
  const { tenantSlug } = useParams<{ tenantSlug: string }>();
  const [geofences, setGeofences] = useState<Geofence[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tenantSlug) return;
    setLoading(true);
    attendanceService
      .getGeofences(tenantSlug)
      .then((res) => setGeofences(res.results ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [tenantSlug]);

  const columns = [
    { key: "name", header: t("admin.geofences.name") },
    {
      key: "latitude",
      header: t("admin.geofences.lat"),
      render: (g: Geofence) => Number(g.latitude).toFixed(5),
    },
    {
      key: "longitude",
      header: t("admin.geofences.lng"),
      render: (g: Geofence) => Number(g.longitude).toFixed(5),
    },
    {
      key: "radius_meters",
      header: t("admin.geofences.radius"),
      render: (g: Geofence) => `${g.radius_meters}m`,
    },
    {
      key: "is_active",
      header: t("admin.employees.status"),
      render: (g: Geofence) => (
        <span className={`badge ${g.is_active ? "badge-present" : "badge-absent"}`}>
          {g.is_active ? "Active" : "Inactive"}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          {t("admin.geofences.title")}
        </h2>
        <button className="btn-primary">{t("admin.geofences.add")}</button>
      </div>
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <LoadingSpinner className="py-12" />
        ) : (
          <DataTable columns={columns} data={geofences} keyExtractor={(g) => g.id} />
        )}
      </div>
    </div>
  );
}
