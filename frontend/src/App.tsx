import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";

// Layout
import { AppLayout } from "@/components/layout/AppLayout";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";

// Modules
import { LoginPage } from "@/modules/auth/LoginPage";
import { DashboardPage } from "@/modules/dashboard/DashboardPage";
import { AttendancePage } from "@/modules/attendance/AttendancePage";
import { AttendanceMapPage } from "@/modules/map/AttendanceMapPage";
import { EmployeesPage } from "@/modules/admin/EmployeesPage";
import { ShiftsPage } from "@/modules/admin/ShiftsPage";
import { GeofencesPage } from "@/modules/admin/GeofencesPage";
import { DevicesPage } from "@/modules/admin/DevicesPage";
import { SettingsPage } from "@/modules/settings/SettingsPage";
import { ApprovalsPage } from "@/modules/approvals/ApprovalsPage";
import { OnboardingPage } from "@/modules/onboarding/OnboardingPage";
import { ReportsPage } from "@/modules/reports/ReportsPage";

function App() {
  const { isAuthenticated, loadProfile, tenant } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      loadProfile();
    }
  }, [isAuthenticated, loadProfile]);

  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<LoginPage />} />

        {/* Protected app routes */}
        <Route
          path="/:tenantSlug"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="attendance" element={<AttendancePage />} />
          <Route path="map" element={<AttendanceMapPage />} />
          <Route
            path="admin/employees"
            element={
              <ProtectedRoute allowedRoles={["SUPER_ADMIN", "TENANT_ADMIN", "MANAGER"]}>
                <EmployeesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="admin/shifts"
            element={
              <ProtectedRoute allowedRoles={["SUPER_ADMIN", "TENANT_ADMIN"]}>
                <ShiftsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="admin/geofences"
            element={
              <ProtectedRoute allowedRoles={["SUPER_ADMIN", "TENANT_ADMIN"]}>
                <GeofencesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="admin/devices"
            element={
              <ProtectedRoute allowedRoles={["SUPER_ADMIN", "TENANT_ADMIN", "MANAGER"]}>
                <DevicesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="approvals"
            element={
              <ProtectedRoute allowedRoles={["SUPER_ADMIN", "TENANT_ADMIN", "MANAGER"]}>
                <ApprovalsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="reports"
            element={
              <ProtectedRoute allowedRoles={["SUPER_ADMIN", "TENANT_ADMIN", "MANAGER"]}>
                <ReportsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="onboarding"
            element={
              <ProtectedRoute allowedRoles={["SUPER_ADMIN", "TENANT_ADMIN"]}>
                <OnboardingPage />
              </ProtectedRoute>
            }
          />
          <Route path="settings" element={<SettingsPage />} />
          <Route index element={<Navigate to="dashboard" replace />} />
        </Route>

        {/* Top-level onboarding (no tenant required) */}
        <Route
          path="/onboarding"
          element={
            <ProtectedRoute allowedRoles={["SUPER_ADMIN", "TENANT_ADMIN"]}>
              <OnboardingPage />
            </ProtectedRoute>
          }
        />

        {/* Root redirect */}
        <Route
          path="/"
          element={
            isAuthenticated ? (
              tenant?.slug ? (
                <Navigate to={`/${tenant.slug}/dashboard`} replace />
              ) : (
                <Navigate to="/onboarding" replace />
              )
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />

        {/* Unauthorized */}
        <Route
          path="/unauthorized"
          element={
            <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-900">
              <div className="text-center">
                <h1 className="text-4xl font-bold text-gray-900 dark:text-white">403</h1>
                <p className="mt-2 text-gray-500 dark:text-gray-400">
                  You do not have permission to access this page.
                </p>
              </div>
            </div>
          }
        />

        {/* 404 */}
        <Route
          path="*"
          element={
            <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-900">
              <div className="text-center">
                <h1 className="text-4xl font-bold text-gray-900 dark:text-white">404</h1>
                <p className="mt-2 text-gray-500 dark:text-gray-400">Page not found.</p>
              </div>
            </div>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
