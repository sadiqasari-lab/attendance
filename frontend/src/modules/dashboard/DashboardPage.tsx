import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import {
  UsersIcon,
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon,
} from "@heroicons/react/24/outline";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar, Doughnut } from "react-chartjs-2";
import { StatCard } from "@/components/common/StatCard";
import { attendanceService } from "@/services/attendance.service";
import type { AttendanceSummary } from "@/types";

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend);

export function DashboardPage() {
  const { t } = useTranslation();
  const { tenantSlug } = useParams<{ tenantSlug: string }>();
  const [summary, setSummary] = useState<AttendanceSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tenantSlug) return;
    setLoading(true);
    attendanceService
      .getSummary(tenantSlug)
      .then((res) => setSummary(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [tenantSlug]);

  // Aggregate stats
  const totals = summary.reduce(
    (acc, s) => ({
      employees: acc.employees + 1,
      present: acc.present + s.present_count,
      late: acc.late + s.late_count,
      absent: acc.absent + s.absent_count,
      hours: acc.hours + s.total_hours,
    }),
    { employees: 0, present: 0, late: 0, absent: 0, hours: 0 }
  );

  const donutData = {
    labels: [
      t("attendance.present"),
      t("attendance.late"),
      t("attendance.absent"),
    ],
    datasets: [
      {
        data: [totals.present, totals.late, totals.absent],
        backgroundColor: ["#22c55e", "#eab308", "#ef4444"],
        borderWidth: 0,
      },
    ],
  };

  const barData = {
    labels: summary.slice(0, 10).map((s) => s.employee_name.split(" ")[0]),
    datasets: [
      {
        label: t("attendance.present"),
        data: summary.slice(0, 10).map((s) => s.present_count),
        backgroundColor: "#22c55e",
      },
      {
        label: t("attendance.late"),
        data: summary.slice(0, 10).map((s) => s.late_count),
        backgroundColor: "#eab308",
      },
      {
        label: t("attendance.absent"),
        data: summary.slice(0, 10).map((s) => s.absent_count),
        backgroundColor: "#ef4444",
      },
    ],
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white">
        {t("dashboard.title")}
      </h2>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title={t("dashboard.total_employees")}
          value={totals.employees}
          icon={<UsersIcon className="h-6 w-6 text-primary-600" />}
        />
        <StatCard
          title={t("dashboard.present_today")}
          value={totals.present}
          icon={<CheckCircleIcon className="h-6 w-6 text-green-600" />}
          changeType="positive"
        />
        <StatCard
          title={t("dashboard.late_today")}
          value={totals.late}
          icon={<ClockIcon className="h-6 w-6 text-yellow-600" />}
          changeType="negative"
        />
        <StatCard
          title={t("dashboard.absent_today")}
          value={totals.absent}
          icon={<XCircleIcon className="h-6 w-6 text-red-600" />}
          changeType="negative"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card">
          <h3 className="mb-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
            {t("dashboard.attendance_overview")}
          </h3>
          <div className="mx-auto max-w-xs">
            <Doughnut
              data={donutData}
              options={{ responsive: true, plugins: { legend: { position: "bottom" } } }}
            />
          </div>
        </div>

        <div className="card">
          <h3 className="mb-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
            {t("dashboard.weekly_trend")}
          </h3>
          <Bar
            data={barData}
            options={{
              responsive: true,
              plugins: { legend: { position: "top" } },
              scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true } },
            }}
          />
        </div>
      </div>

      {/* Summary Table */}
      {summary.length > 0 && (
        <div className="card overflow-x-auto">
          <h3 className="mb-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
            {t("dashboard.recent_activity")}
          </h3>
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-sm">
            <thead>
              <tr className="text-start text-xs uppercase text-gray-500 dark:text-gray-400">
                <th className="px-3 py-2">{t("attendance.employee")}</th>
                <th className="px-3 py-2">{t("attendance.present")}</th>
                <th className="px-3 py-2">{t("attendance.late")}</th>
                <th className="px-3 py-2">{t("attendance.absent")}</th>
                <th className="px-3 py-2">{t("attendance.duration")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {summary.slice(0, 10).map((s) => (
                <tr key={s.employee_id}>
                  <td className="px-3 py-2 font-medium text-gray-900 dark:text-white">
                    {s.employee_name}
                  </td>
                  <td className="px-3 py-2 text-green-600">{s.present_count}</td>
                  <td className="px-3 py-2 text-yellow-600">{s.late_count}</td>
                  <td className="px-3 py-2 text-red-600">{s.absent_count}</td>
                  <td className="px-3 py-2">{s.total_hours.toFixed(1)}h</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
