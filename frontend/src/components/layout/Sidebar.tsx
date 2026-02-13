import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "@/store/authStore";
import {
  HomeIcon,
  ClockIcon,
  MapIcon,
  UsersIcon,
  CalendarIcon,
  MapPinIcon,
  DevicePhoneMobileIcon,
  CheckCircleIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  RocketLaunchIcon,
} from "@heroicons/react/24/outline";

interface NavItem {
  path: string;
  label: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  roles?: string[];
}

export function Sidebar() {
  const { t } = useTranslation();
  const { tenant, user } = useAuthStore();
  const slug = tenant?.slug;

  // If no tenant yet, the sidebar nav links can't work — show minimal sidebar
  if (!slug) {
    return (
      <aside className="fixed inset-y-0 start-0 z-30 flex w-64 flex-col border-e border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <div className="flex h-16 items-center gap-3 border-b border-gray-200 px-6 dark:border-gray-700">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-600 text-white font-bold text-sm">
            IA
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900 dark:text-white">
              {t("app.title")}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {t("app.subtitle")}
            </p>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto px-3 py-4">
          <ul className="space-y-1">
            <li>
              <NavLink
                to="/onboarding"
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-400"
                      : "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
                  }`
                }
              >
                <RocketLaunchIcon className="h-5 w-5 shrink-0" />
                {t("nav.onboarding")}
              </NavLink>
            </li>
          </ul>
        </nav>
      </aside>
    );
  }

  const navItems: NavItem[] = [
    { path: `/${slug}/dashboard`, label: t("nav.dashboard"), icon: HomeIcon },
    { path: `/${slug}/attendance`, label: t("nav.attendance"), icon: ClockIcon },
    { path: `/${slug}/map`, label: t("nav.map"), icon: MapIcon },
    {
      path: `/${slug}/admin/employees`,
      label: t("nav.employees"),
      icon: UsersIcon,
      roles: ["SUPER_ADMIN", "TENANT_ADMIN", "MANAGER"],
    },
    {
      path: `/${slug}/admin/shifts`,
      label: t("nav.shifts"),
      icon: CalendarIcon,
      roles: ["SUPER_ADMIN", "TENANT_ADMIN"],
    },
    {
      path: `/${slug}/admin/geofences`,
      label: t("nav.geofences"),
      icon: MapPinIcon,
      roles: ["SUPER_ADMIN", "TENANT_ADMIN"],
    },
    {
      path: `/${slug}/admin/devices`,
      label: t("nav.devices"),
      icon: DevicePhoneMobileIcon,
      roles: ["SUPER_ADMIN", "TENANT_ADMIN", "MANAGER"],
    },
    {
      path: `/${slug}/approvals`,
      label: t("nav.approvals"),
      icon: CheckCircleIcon,
      roles: ["SUPER_ADMIN", "TENANT_ADMIN", "MANAGER"],
    },
    {
      path: `/${slug}/reports`,
      label: t("nav.reports"),
      icon: ChartBarIcon,
      roles: ["SUPER_ADMIN", "TENANT_ADMIN", "MANAGER"],
    },
    {
      path: `/${slug}/onboarding`,
      label: t("nav.onboarding"),
      icon: RocketLaunchIcon,
      roles: ["SUPER_ADMIN", "TENANT_ADMIN"],
    },
    { path: `/${slug}/settings`, label: t("nav.settings"), icon: Cog6ToothIcon },
  ];

  const filteredItems = navItems.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role))
  );

  return (
    <aside className="fixed inset-y-0 start-0 z-30 flex w-64 flex-col border-e border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-gray-200 px-6 dark:border-gray-700">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-600 text-white font-bold text-sm">
          IA
        </div>
        <div>
          <p className="text-sm font-semibold text-gray-900 dark:text-white">
            {t("app.title")}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {tenant?.name ?? t("app.subtitle")}
          </p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-1">
          {filteredItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-400"
                      : "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
                  }`
                }
              >
                <item.icon className="h-5 w-5 shrink-0" />
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* User info */}
      <div className="border-t border-gray-200 px-4 py-3 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-xs font-medium text-primary-700 dark:bg-primary-900/30 dark:text-primary-400">
            {user?.first_name?.[0]}
            {user?.last_name?.[0]}
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-gray-900 dark:text-white">
              {user?.full_name}
            </p>
            <p className="truncate text-xs text-gray-500 dark:text-gray-400">
              {user?.role?.replace("_", " ")}
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
