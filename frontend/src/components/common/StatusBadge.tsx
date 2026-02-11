import { useTranslation } from "react-i18next";
import type { AttendanceStatus } from "@/types";

const statusStyles: Record<AttendanceStatus, string> = {
  PRESENT: "badge-present",
  ABSENT: "badge-absent",
  LATE: "badge-late",
  EARLY_DEPARTURE: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
  HALF_DAY: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
  ON_LEAVE: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300",
};

const statusKeys: Record<AttendanceStatus, string> = {
  PRESENT: "attendance.present",
  ABSENT: "attendance.absent",
  LATE: "attendance.late",
  EARLY_DEPARTURE: "attendance.early_departure",
  HALF_DAY: "attendance.half_day",
  ON_LEAVE: "attendance.on_leave",
};

export function StatusBadge({ status }: { status: AttendanceStatus }) {
  const { t } = useTranslation();
  return (
    <span className={`badge ${statusStyles[status]}`}>
      {t(statusKeys[status])}
    </span>
  );
}
