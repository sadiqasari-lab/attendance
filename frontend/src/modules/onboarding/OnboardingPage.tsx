import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { attendanceService } from "@/services/attendance.service";
import { tenantService } from "@/services/tenant.service";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import type { Department, Geofence, Shift } from "@/types";
import {
  BuildingOffice2Icon,
  UsersIcon,
  ClockIcon,
  MapPinIcon,
  CheckIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  PlusIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";

const TOTAL_STEPS = 5;

interface CompanyInfo {
  name: string;
  name_ar: string;
  email: string;
  phone: string;
  timezone: string;
  country: string;
  city: string;
}

export function OnboardingPage() {
  const { t } = useTranslation();
  const { tenantSlug } = useParams<{ tenantSlug: string }>();
  const navigate = useNavigate();
  const { tenant } = useAuthStore();
  const effectiveSlug = tenantSlug || tenant?.slug;

  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [completed, setCompleted] = useState(false);

  // Step 1: Company Info
  const [companyInfo, setCompanyInfo] = useState<CompanyInfo>({
    name: "",
    name_ar: "",
    email: "",
    phone: "",
    timezone: "Asia/Riyadh",
    country: "SA",
    city: "",
  });

  // Step 2: Departments
  const [departments, setDepartments] = useState<Department[]>([]);
  const [newDept, setNewDept] = useState({ name: "", name_ar: "" });

  // Step 3: Shifts
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [newShift, setNewShift] = useState({
    name: "",
    name_ar: "",
    start_time: "08:00",
    end_time: "17:00",
    grace_period_minutes: 15,
  });

  // Step 4: Geofences
  const [geofences, setGeofences] = useState<Geofence[]>([]);
  const [newGeofence, setNewGeofence] = useState({
    name: "",
    name_ar: "",
    latitude: 24.7136,
    longitude: 46.6753,
    radius_meters: 200,
  });

  // Load existing data
  useEffect(() => {
    if (!effectiveSlug) {
      // No tenant yet — this is a fresh setup, skip loading and go straight to form
      setLoading(false);
      return;
    }

    const loadData = async () => {
      setLoading(true);
      try {
        // Load tenant info
        if (tenant) {
          setCompanyInfo({
            name: tenant.name ?? "",
            name_ar: "",
            email: "",
            phone: "",
            timezone: "Asia/Riyadh",
            country: "SA",
            city: "",
          });
        }

        // Load existing departments
        try {
          const deptRes = await tenantService.getDepartments(effectiveSlug);
          setDepartments(deptRes.results ?? []);
        } catch {
          // no departments yet
        }

        // Load existing shifts
        try {
          const shiftRes = await attendanceService.getShifts(effectiveSlug);
          setShifts(shiftRes.results ?? []);
        } catch {
          // no shifts yet
        }

        // Load existing geofences
        try {
          const geoRes = await attendanceService.getGeofences(effectiveSlug);
          setGeofences(geoRes.results ?? []);
        } catch {
          // no geofences yet
        }
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [effectiveSlug, tenant]);

  // Step actions
  const handleAddDepartment = async () => {
    if (!effectiveSlug || !newDept.name) return;
    setSaving(true);
    try {
      // Use a direct API call to create department
      const { default: api } = await import("@/services/api");
      const { data } = await api.post(`/tenants/departments/`, {
        name: newDept.name,
        name_ar: newDept.name_ar,
        tenant_slug: effectiveSlug,
      });
      setDepartments([...departments, data.data ?? data]);
      setNewDept({ name: "", name_ar: "" });
    } catch {
      // try alternative approach
      try {
        const { default: api } = await import("@/services/api");
        const { data } = await api.post(`/${effectiveSlug}/attendance/departments/`, {
          name: newDept.name,
          name_ar: newDept.name_ar,
        });
        setDepartments([...departments, data.data ?? data]);
        setNewDept({ name: "", name_ar: "" });
      } catch {
        // silently fail
      }
    } finally {
      setSaving(false);
    }
  };

  const handleAddShift = async () => {
    if (!effectiveSlug || !newShift.name) return;
    setSaving(true);
    try {
      const result = await attendanceService.createShift(effectiveSlug!, {
        name: newShift.name,
        name_ar: newShift.name_ar,
        start_time: newShift.start_time,
        end_time: newShift.end_time,
        grace_period_minutes: newShift.grace_period_minutes,
      } as Partial<Shift>);
      setShifts([...shifts, result]);
      setNewShift({
        name: "",
        name_ar: "",
        start_time: "08:00",
        end_time: "17:00",
        grace_period_minutes: 15,
      });
    } catch {
      // silently fail
    } finally {
      setSaving(false);
    }
  };

  const handleAddGeofence = async () => {
    if (!effectiveSlug || !newGeofence.name) return;
    setSaving(true);
    try {
      const result = await attendanceService.createGeofence(effectiveSlug!, {
        name: newGeofence.name,
        name_ar: newGeofence.name_ar,
        latitude: newGeofence.latitude,
        longitude: newGeofence.longitude,
        radius_meters: newGeofence.radius_meters,
      } as Partial<Geofence>);
      setGeofences([...geofences, result]);
      setNewGeofence({
        name: "",
        name_ar: "",
        latitude: 24.7136,
        longitude: 46.6753,
        radius_meters: 200,
      });
    } catch {
      // silently fail
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteShift = async (id: string) => {
    if (!effectiveSlug) return;
    try {
      await attendanceService.deleteShift(effectiveSlug!, id);
      setShifts(shifts.filter((s) => s.id !== id));
    } catch {
      // silently fail
    }
  };

  const handleDeleteGeofence = async (id: string) => {
    if (!effectiveSlug) return;
    try {
      await attendanceService.deleteGeofence(effectiveSlug!, id);
      setGeofences(geofences.filter((g) => g.id !== id));
    } catch {
      // silently fail
    }
  };

  const handleFinish = () => {
    setCompleted(true);
  };

  if (loading) {
    return <LoadingSpinner className="py-24" />;
  }

  if (completed) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
        <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
          <CheckIcon className="h-10 w-10 text-green-600 dark:text-green-400" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t("onboarding.completed")}
        </h2>
        <p className="mt-2 max-w-md text-gray-500 dark:text-gray-400">
          {t("onboarding.completed_desc")}
        </p>
        <button
          onClick={() => {
            const slug = effectiveSlug || useAuthStore.getState().tenant?.slug;
            navigate(slug ? `/${slug}/dashboard` : "/", { replace: true });
          }}
          className="btn-primary mt-6"
        >
          {t("onboarding.go_dashboard")}
        </button>
      </div>
    );
  }

  const stepIcons: React.ComponentType<React.SVGProps<SVGSVGElement>>[] = [
    BuildingOffice2Icon,
    UsersIcon,
    ClockIcon,
    MapPinIcon,
    CheckIcon,
  ];

  const stepTitles = [
    t("onboarding.step1_title"),
    t("onboarding.step2_title"),
    t("onboarding.step3_title"),
    t("onboarding.step4_title"),
    t("onboarding.step5_title"),
  ];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t("onboarding.welcome")}
        </h2>
        <p className="mt-1 text-gray-500 dark:text-gray-400">
          {t("onboarding.welcome_desc")}
        </p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center justify-center gap-2">
        {Array.from({ length: TOTAL_STEPS }, (_, i) => {
          const step = i + 1;
          const StepIcon = stepIcons[i];
          const isActive = step === currentStep;
          const isDone = step < currentStep;
          return (
            <div key={step} className="flex items-center gap-2">
              <button
                onClick={() => setCurrentStep(step)}
                className={`flex h-10 w-10 items-center justify-center rounded-full border-2 transition-colors ${
                  isActive
                    ? "border-primary-600 bg-primary-600 text-white"
                    : isDone
                    ? "border-green-500 bg-green-500 text-white"
                    : "border-gray-300 bg-white text-gray-400 dark:border-gray-600 dark:bg-gray-800"
                }`}
                title={stepTitles[i]}
              >
                {isDone ? (
                  <CheckIcon className="h-5 w-5" />
                ) : StepIcon ? (
                  <StepIcon className="h-5 w-5" />
                ) : null}
              </button>
              {step < TOTAL_STEPS && (
                <div
                  className={`h-0.5 w-8 ${
                    isDone ? "bg-green-500" : "bg-gray-300 dark:bg-gray-600"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>

      <p className="text-center text-sm text-gray-500 dark:text-gray-400">
        {t("onboarding.step")} {currentStep} {t("onboarding.of")} {TOTAL_STEPS} — {stepTitles[currentStep - 1]}
      </p>

      {/* Step content */}
      <div className="card p-6">
        {/* ===== Step 1: Company Info ===== */}
        {currentStep === 1 && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">{t("onboarding.step1_desc")}</p>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t("onboarding.company_name")}
                </label>
                <input
                  type="text"
                  value={companyInfo.name}
                  onChange={(e) => setCompanyInfo({ ...companyInfo, name: e.target.value })}
                  className="input w-full"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t("onboarding.company_name_ar")}
                </label>
                <input
                  type="text"
                  value={companyInfo.name_ar}
                  onChange={(e) => setCompanyInfo({ ...companyInfo, name_ar: e.target.value })}
                  className="input w-full"
                  dir="rtl"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t("onboarding.company_email")}
                </label>
                <input
                  type="email"
                  value={companyInfo.email}
                  onChange={(e) => setCompanyInfo({ ...companyInfo, email: e.target.value })}
                  className="input w-full"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t("onboarding.company_phone")}
                </label>
                <input
                  type="tel"
                  value={companyInfo.phone}
                  onChange={(e) => setCompanyInfo({ ...companyInfo, phone: e.target.value })}
                  className="input w-full"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t("onboarding.timezone")}
                </label>
                <select
                  value={companyInfo.timezone}
                  onChange={(e) => setCompanyInfo({ ...companyInfo, timezone: e.target.value })}
                  className="input w-full"
                >
                  <option value="Asia/Riyadh">Asia/Riyadh (UTC+3)</option>
                  <option value="Asia/Dubai">Asia/Dubai (UTC+4)</option>
                  <option value="Asia/Karachi">Asia/Karachi (UTC+5)</option>
                  <option value="Asia/Kolkata">Asia/Kolkata (UTC+5:30)</option>
                  <option value="Europe/London">Europe/London (UTC+0)</option>
                  <option value="America/New_York">America/New_York (UTC-5)</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t("onboarding.country")}
                </label>
                <select
                  value={companyInfo.country}
                  onChange={(e) => setCompanyInfo({ ...companyInfo, country: e.target.value })}
                  className="input w-full"
                >
                  <option value="SA">Saudi Arabia</option>
                  <option value="AE">United Arab Emirates</option>
                  <option value="KW">Kuwait</option>
                  <option value="BH">Bahrain</option>
                  <option value="OM">Oman</option>
                  <option value="QA">Qatar</option>
                  <option value="EG">Egypt</option>
                  <option value="JO">Jordan</option>
                  <option value="PK">Pakistan</option>
                  <option value="IN">India</option>
                </select>
              </div>
              <div className="sm:col-span-2">
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t("onboarding.city")}
                </label>
                <input
                  type="text"
                  value={companyInfo.city}
                  onChange={(e) => setCompanyInfo({ ...companyInfo, city: e.target.value })}
                  className="input w-full"
                />
              </div>
            </div>
          </div>
        )}

        {/* ===== Step 2: Departments ===== */}
        {currentStep === 2 && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">{t("onboarding.step2_desc")}</p>

            {/* Existing departments */}
            {departments.length > 0 ? (
              <div className="divide-y divide-gray-200 rounded-lg border border-gray-200 dark:divide-gray-700 dark:border-gray-700">
                {departments.map((dept) => (
                  <div key={dept.id} className="flex items-center justify-between px-4 py-3">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{dept.name}</p>
                      {dept.name_ar && (
                        <p className="text-sm text-gray-500 dark:text-gray-400" dir="rtl">
                          {dept.name_ar}
                        </p>
                      )}
                    </div>
                    <span className="badge bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                      {dept.is_active ? "Active" : "Inactive"}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="py-6 text-center text-sm text-gray-400">{t("onboarding.no_departments")}</p>
            )}

            {/* Add department form */}
            <div className="rounded-lg border border-dashed border-gray-300 p-4 dark:border-gray-600">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                    {t("onboarding.department_name")}
                  </label>
                  <input
                    type="text"
                    value={newDept.name}
                    onChange={(e) => setNewDept({ ...newDept, name: e.target.value })}
                    className="input w-full"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                    {t("onboarding.department_name_ar")}
                  </label>
                  <input
                    type="text"
                    value={newDept.name_ar}
                    onChange={(e) => setNewDept({ ...newDept, name_ar: e.target.value })}
                    className="input w-full"
                    dir="rtl"
                  />
                </div>
              </div>
              <button
                onClick={handleAddDepartment}
                disabled={saving || !newDept.name}
                className="btn-primary mt-3 flex items-center gap-1"
              >
                <PlusIcon className="h-4 w-4" />
                {saving ? t("common.loading") : t("onboarding.add_department")}
              </button>
            </div>
          </div>
        )}

        {/* ===== Step 3: Shifts ===== */}
        {currentStep === 3 && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">{t("onboarding.step3_desc")}</p>

            {shifts.length > 0 ? (
              <div className="divide-y divide-gray-200 rounded-lg border border-gray-200 dark:divide-gray-700 dark:border-gray-700">
                {shifts.map((shift) => (
                  <div key={shift.id} className="flex items-center justify-between px-4 py-3">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{shift.name}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {shift.start_time} - {shift.end_time} (Grace: {shift.grace_period_minutes}min)
                      </p>
                    </div>
                    <button
                      onClick={() => handleDeleteShift(shift.id)}
                      className="rounded p-1 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="py-6 text-center text-sm text-gray-400">{t("onboarding.no_shifts")}</p>
            )}

            <div className="rounded-lg border border-dashed border-gray-300 p-4 dark:border-gray-600">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                    {t("onboarding.shift_name")}
                  </label>
                  <input
                    type="text"
                    value={newShift.name}
                    onChange={(e) => setNewShift({ ...newShift, name: e.target.value })}
                    className="input w-full"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                    {t("onboarding.shift_start")}
                  </label>
                  <input
                    type="time"
                    value={newShift.start_time}
                    onChange={(e) => setNewShift({ ...newShift, start_time: e.target.value })}
                    className="input w-full"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                    {t("onboarding.shift_end")}
                  </label>
                  <input
                    type="time"
                    value={newShift.end_time}
                    onChange={(e) => setNewShift({ ...newShift, end_time: e.target.value })}
                    className="input w-full"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                    {t("onboarding.shift_grace")}
                  </label>
                  <input
                    type="number"
                    value={newShift.grace_period_minutes}
                    onChange={(e) =>
                      setNewShift({ ...newShift, grace_period_minutes: parseInt(e.target.value) || 0 })
                    }
                    className="input w-full"
                    min={0}
                  />
                </div>
              </div>
              <button
                onClick={handleAddShift}
                disabled={saving || !newShift.name}
                className="btn-primary mt-3 flex items-center gap-1"
              >
                <PlusIcon className="h-4 w-4" />
                {saving ? t("common.loading") : t("onboarding.add_shift")}
              </button>
            </div>
          </div>
        )}

        {/* ===== Step 4: Geofences ===== */}
        {currentStep === 4 && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">{t("onboarding.step4_desc")}</p>

            {geofences.length > 0 ? (
              <div className="divide-y divide-gray-200 rounded-lg border border-gray-200 dark:divide-gray-700 dark:border-gray-700">
                {geofences.map((geo) => (
                  <div key={geo.id} className="flex items-center justify-between px-4 py-3">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{geo.name}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {geo.latitude}, {geo.longitude} (Radius: {geo.radius_meters}m)
                      </p>
                    </div>
                    <button
                      onClick={() => handleDeleteGeofence(geo.id)}
                      className="rounded p-1 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="py-6 text-center text-sm text-gray-400">{t("onboarding.no_geofences")}</p>
            )}

            <div className="rounded-lg border border-dashed border-gray-300 p-4 dark:border-gray-600">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                    {t("onboarding.geofence_name")}
                  </label>
                  <input
                    type="text"
                    value={newGeofence.name}
                    onChange={(e) => setNewGeofence({ ...newGeofence, name: e.target.value })}
                    className="input w-full"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                    {t("onboarding.geofence_lat")}
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    value={newGeofence.latitude}
                    onChange={(e) =>
                      setNewGeofence({ ...newGeofence, latitude: parseFloat(e.target.value) || 0 })
                    }
                    className="input w-full"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                    {t("onboarding.geofence_lng")}
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    value={newGeofence.longitude}
                    onChange={(e) =>
                      setNewGeofence({ ...newGeofence, longitude: parseFloat(e.target.value) || 0 })
                    }
                    className="input w-full"
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                    {t("onboarding.geofence_radius")}
                  </label>
                  <input
                    type="number"
                    value={newGeofence.radius_meters}
                    onChange={(e) =>
                      setNewGeofence({ ...newGeofence, radius_meters: parseInt(e.target.value) || 100 })
                    }
                    className="input w-full"
                    min={50}
                  />
                </div>
              </div>
              <button
                onClick={handleAddGeofence}
                disabled={saving || !newGeofence.name}
                className="btn-primary mt-3 flex items-center gap-1"
              >
                <PlusIcon className="h-4 w-4" />
                {saving ? t("common.loading") : t("onboarding.add_geofence")}
              </button>
            </div>
          </div>
        )}

        {/* ===== Step 5: Review & Finish ===== */}
        {currentStep === 5 && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">{t("onboarding.step5_desc")}</p>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="rounded-lg bg-blue-50 p-4 text-center dark:bg-blue-900/20">
                <UsersIcon className="mx-auto h-8 w-8 text-blue-600 dark:text-blue-400" />
                <p className="mt-2 text-2xl font-bold text-blue-700 dark:text-blue-300">
                  {departments.length}
                </p>
                <p className="text-sm text-blue-600 dark:text-blue-400">
                  {t("onboarding.summary_departments")} {t("onboarding.summary_configured")}
                </p>
              </div>
              <div className="rounded-lg bg-green-50 p-4 text-center dark:bg-green-900/20">
                <ClockIcon className="mx-auto h-8 w-8 text-green-600 dark:text-green-400" />
                <p className="mt-2 text-2xl font-bold text-green-700 dark:text-green-300">
                  {shifts.length}
                </p>
                <p className="text-sm text-green-600 dark:text-green-400">
                  {t("onboarding.summary_shifts")} {t("onboarding.summary_configured")}
                </p>
              </div>
              <div className="rounded-lg bg-purple-50 p-4 text-center dark:bg-purple-900/20">
                <MapPinIcon className="mx-auto h-8 w-8 text-purple-600 dark:text-purple-400" />
                <p className="mt-2 text-2xl font-bold text-purple-700 dark:text-purple-300">
                  {geofences.length}
                </p>
                <p className="text-sm text-purple-600 dark:text-purple-400">
                  {t("onboarding.summary_geofences")} {t("onboarding.summary_configured")}
                </p>
              </div>
            </div>

            {/* Company info summary */}
            <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
              <h4 className="mb-2 font-medium text-gray-900 dark:text-white">
                {t("onboarding.step1_title")}
              </h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <span className="text-gray-500 dark:text-gray-400">{t("onboarding.company_name")}:</span>
                <span className="text-gray-900 dark:text-white">{companyInfo.name || "—"}</span>
                <span className="text-gray-500 dark:text-gray-400">{t("onboarding.company_email")}:</span>
                <span className="text-gray-900 dark:text-white">{companyInfo.email || "—"}</span>
                <span className="text-gray-500 dark:text-gray-400">{t("onboarding.timezone")}:</span>
                <span className="text-gray-900 dark:text-white">{companyInfo.timezone}</span>
                <span className="text-gray-500 dark:text-gray-400">{t("onboarding.country")}:</span>
                <span className="text-gray-900 dark:text-white">{companyInfo.country}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Navigation buttons */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
          disabled={currentStep === 1}
          className="btn-secondary flex items-center gap-1 disabled:opacity-50"
        >
          <ArrowLeftIcon className="h-4 w-4" />
          {t("onboarding.previous")}
        </button>

        {currentStep < TOTAL_STEPS ? (
          <button
            onClick={() => setCurrentStep(currentStep + 1)}
            className="btn-primary flex items-center gap-1"
          >
            {t("onboarding.next")}
            <ArrowRightIcon className="h-4 w-4" />
          </button>
        ) : (
          <button onClick={handleFinish} className="btn-primary flex items-center gap-1">
            <CheckIcon className="h-4 w-4" />
            {t("onboarding.finish")}
          </button>
        )}
      </div>
    </div>
  );
}
