// ======================================================
// Inspire Attendance System — Shared TypeScript Types
// ======================================================

// --- Auth / User ---
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  first_name_ar: string;
  last_name_ar: string;
  phone: string;
  role: UserRole;
  full_name: string;
  full_name_ar: string;
  is_active: boolean;
  requires_biometric_enrollment: boolean;
  date_joined: string;
}

export type UserRole = "SUPER_ADMIN" | "TENANT_ADMIN" | "MANAGER" | "EMPLOYEE";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  data: {
    access: string;
    refresh: string;
    user: User;
    tenant?: TenantInfo;
  };
}

export interface TenantInfo {
  id: string;
  name: string;
  slug: string;
}

// --- Tenant ---
export interface Tenant {
  id: string;
  group: string;
  name: string;
  name_ar: string;
  slug: string;
  description: string;
  city: string;
  country: string;
  phone: string;
  email: string;
  timezone: string;
  is_active: boolean;
  created_at: string;
}

export interface Group {
  id: string;
  name: string;
  name_ar: string;
  is_active: boolean;
}

export interface Department {
  id: string;
  tenant: string;
  name: string;
  name_ar: string;
  is_active: boolean;
  parent: string | null;
}

// --- Employee ---
export interface Employee {
  id: string;
  user: User;
  employee_id: string;
  tenant: string;
  department: string | null;
  department_name?: string;
  designation: string;
  designation_ar: string;
  date_of_joining: string | null;
  is_active: boolean;
  created_at: string;
}

// --- Attendance ---
export interface Shift {
  id: string;
  name: string;
  name_ar: string;
  start_time: string;
  end_time: string;
  grace_period_minutes: number;
  is_overnight: boolean;
  is_active: boolean;
}

export interface AttendancePolicy {
  id: string;
  name: string;
  name_ar: string;
  require_selfie: boolean;
  require_liveness: boolean;
  require_gps: boolean;
  require_geofence: boolean;
  require_wifi: boolean;
  require_device_registered: boolean;
  max_offline_per_shift: number;
  allow_early_clockin_minutes: number;
  allow_late_clockout_minutes: number;
}

export interface Geofence {
  id: string;
  name: string;
  name_ar: string;
  latitude: number;
  longitude: number;
  radius_meters: number;
  is_active: boolean;
  description: string;
}

export type AttendanceStatus =
  | "PRESENT"
  | "ABSENT"
  | "LATE"
  | "EARLY_DEPARTURE"
  | "HALF_DAY"
  | "ON_LEAVE";

export interface AttendanceRecord {
  id: string;
  employee: string;
  employee_detail?: Employee;
  shift: string;
  shift_name: string;
  date: string;
  clock_in_time: string | null;
  clock_out_time: string | null;
  status: AttendanceStatus;
  clock_in_latitude: number | null;
  clock_in_longitude: number | null;
  clock_out_latitude: number | null;
  clock_out_longitude: number | null;
  is_offline_record: boolean;
  is_validated: boolean;
  validation_errors: string[];
  liveness_passed: boolean;
  face_match_score: number | null;
  gps_accuracy: number | null;
  geofence_valid: boolean;
  wifi_valid: boolean;
  device_valid: boolean;
  clock_skew_detected: boolean;
  duration_hours: number | null;
  notes: string;
  created_at: string;
}

export interface AttendanceSummary {
  employee_id: string;
  employee_name: string;
  date_from: string;
  date_to: string;
  total_days: number;
  present_count: number;
  absent_count: number;
  late_count: number;
  early_departure_count: number;
  half_day_count: number;
  leave_count: number;
  total_hours: number;
  avg_hours_per_day: number;
}

export interface CorrectionRequest {
  id: string;
  attendance_record: string;
  employee: string;
  reason: string;
  requested_clock_in: string | null;
  requested_clock_out: string | null;
  status: "PENDING" | "APPROVED" | "REJECTED";
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_notes: string;
  created_at: string;
}

// --- Device ---
export interface DeviceRegistry {
  id: string;
  employee: string;
  employee_name: string;
  device_type: "COMPANY" | "BYOD";
  platform: "ANDROID" | "IOS";
  device_identifier: string;
  device_model: string;
  device_manufacturer: string;
  os_version: string;
  status: "ACTIVE" | "PENDING" | "REVOKED" | "REPLACED";
  is_rooted: boolean;
  registered_at: string;
}

// --- Biometric ---
export interface BiometricTemplate {
  id: string;
  employee: string;
  employee_name: string;
  embedding_version: number;
  num_images_used: number;
  status: "ACTIVE" | "REVOKED" | "EXPIRED";
  quality_score: number | null;
  enrolled_at: string;
}

// --- Project ---
export interface Project {
  id: string;
  name: string;
  name_ar: string;
  description: string;
  location_name: string;
  latitude: number | null;
  longitude: number | null;
  geofence: string | null;
  status: "PLANNING" | "ACTIVE" | "COMPLETED" | "ON_HOLD";
  is_active: boolean;
  assignment_count: number;
}

// --- Map ---
export interface MapAttendanceEvent {
  event: "clock_in" | "clock_out";
  employee_id: string;
  employee_name: string;
  latitude: string;
  longitude: string;
  timestamp: string;
  status: AttendanceStatus;
}

// --- Pagination ---
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
}

// --- Approvals ---
export type ApprovalRequestType = "ATTENDANCE_CORRECTION" | "DEVICE_CHANGE" | "LEAVE_REQUEST";
export type ApprovalStatus = "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED";
export type ApprovalPriority = "LOW" | "MEDIUM" | "HIGH" | "URGENT";

export interface ApprovalRequest {
  id: string;
  tenant: string;
  request_type: ApprovalRequestType;
  request_type_display: string;
  requester: string;
  requester_name: string;
  requester_employee_id: string;
  status: ApprovalStatus;
  status_display: string;
  title: string;
  description: string;
  metadata: Record<string, unknown>;
  reviewed_by: string | null;
  reviewer_name: string | null;
  reviewed_at: string | null;
  review_notes: string;
  priority: ApprovalPriority;
  priority_display: string;
  created_at: string;
  updated_at: string;
  created_by: string;
}

// --- Audit ---
export interface AuditLog {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  user: string | null;
  details: Record<string, unknown>;
  ip_address: string;
  created_at: string;
}
