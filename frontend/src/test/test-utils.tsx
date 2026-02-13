/**
 * Test utilities — wraps render with providers needed by components.
 */
import { type ReactElement } from "react";
import { render, type RenderOptions } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { I18nextProvider } from "react-i18next";
import i18n from "i18next";
import { initReactI18next } from "react-i18next";

// Minimal i18n instance for tests
const testI18n = i18n.createInstance();
testI18n.use(initReactI18next).init({
  lng: "en",
  fallbackLng: "en",
  resources: {
    en: {
      translation: {
        "nav.dashboard": "Dashboard",
        "nav.attendance": "Attendance",
        "nav.reports": "Reports",
        "nav.map": "Live Map",
        "nav.employees": "Employees",
        "nav.shifts": "Shifts",
        "nav.geofences": "Geofences",
        "nav.devices": "Devices",
        "nav.approvals": "Approvals",
        "nav.settings": "Settings",
        "nav.onboarding": "Onboarding",
        "attendance.present": "Present",
        "attendance.absent": "Absent",
        "attendance.late": "Late",
        "attendance.early_departure": "Early Departure",
        "attendance.half_day": "Half Day",
        "attendance.on_leave": "On Leave",
      },
    },
  },
  interpolation: { escapeValue: false },
});

interface WrapperProps {
  children: React.ReactNode;
}

function AllProviders({ children }: WrapperProps) {
  return (
    <I18nextProvider i18n={testI18n}>
      <MemoryRouter>{children}</MemoryRouter>
    </I18nextProvider>
  );
}

function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, "wrapper"> & { route?: string }
) {
  const Wrapper = ({ children }: WrapperProps) => (
    <I18nextProvider i18n={testI18n}>
      <MemoryRouter initialEntries={[options?.route ?? "/"]}>
        {children}
      </MemoryRouter>
    </I18nextProvider>
  );

  return render(ui, { wrapper: Wrapper, ...options });
}

export { renderWithProviders as render, testI18n };
export { screen, waitFor, within, act } from "@testing-library/react";
export { default as userEvent } from "@testing-library/user-event";
