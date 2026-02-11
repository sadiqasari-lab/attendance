export enum UserRole {
  SUPER_ADMIN = 'SUPER_ADMIN',
  TENANT_ADMIN = 'TENANT_ADMIN',
  MANAGER = 'MANAGER',
  EMPLOYEE = 'EMPLOYEE',
}

export enum DeviceType {
  COMPANY = 'COMPANY',
  BYOD = 'BYOD',
}

export enum DevicePlatform {
  ANDROID = 'ANDROID',
  IOS = 'IOS',
}

export enum AttendanceStatus {
  PRESENT = 'PRESENT',
  LATE = 'LATE',
  EARLY_DEPARTURE = 'EARLY_DEPARTURE',
  ABSENT = 'ABSENT',
  ON_LEAVE = 'ON_LEAVE',
  HOLIDAY = 'HOLIDAY',
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
  requires_biometric_enrollment: boolean;
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  settings: Record<string, unknown>;
}

export interface Employee {
  id: string;
  user: User;
  tenant: string;
  employee_id: string;
  department: string | null;
  designation: string;
  date_of_joining: string;
  is_active: boolean;
}

export interface Shift {
  id: string;
  name: string;
  start_time: string;
  end_time: string;
  grace_period_minutes: number;
  is_night_shift: boolean;
  is_active: boolean;
}

export interface Geofence {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  radius_meters: number;
  is_active: boolean;
}

export interface AttendanceRecord {
  id: string;
  employee: string;
  shift: string;
  date: string;
  clock_in_time: string | null;
  clock_out_time: string | null;
  status: AttendanceStatus;
  clock_in_latitude: number | null;
  clock_in_longitude: number | null;
  clock_out_latitude: number | null;
  clock_out_longitude: number | null;
  is_offline_record: boolean;
  validation_passed: boolean;
  validation_errors: Record<string, string>;
  duration_minutes: number | null;
}

export interface AttendanceSummary {
  total_days: number;
  present_days: number;
  late_days: number;
  absent_days: number;
  early_departures: number;
  average_hours: number;
}

export interface DeviceInfo {
  device_id: string;
  device_name: string;
  platform: DevicePlatform;
  os_version: string;
  app_version: string;
  is_rooted: boolean;
}

export interface BiometricTemplate {
  id: string;
  status: string;
  created_at: string;
  embedding_version: number;
}

export interface ClockInPayload {
  shift_id: string;
  selfie: string; // base64
  latitude: number;
  longitude: number;
  gps_accuracy: number;
  device_id: string;
  wifi_bssid?: string;
  wifi_ssid?: string;
  liveness_score: number;
  face_match_score: number;
  client_timestamp: string;
  is_mock_location: boolean;
}

export interface ClockOutPayload {
  attendance_id: string;
  selfie: string; // base64
  latitude: number;
  longitude: number;
  gps_accuracy: number;
  client_timestamp: string;
}

export interface OfflineAttendancePayload extends ClockInPayload {
  integrity_hash: string;
  recorded_at: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ValidationError {
  [field: string]: string[];
}

export type NavigationParamList = {
  Auth: undefined;
  Login: undefined;
  Main: undefined;
  Dashboard: undefined;
  ClockIn: {shiftId: string};
  ClockOut: {attendanceId: string};
  AttendanceHistory: undefined;
  BiometricEnroll: undefined;
  Settings: undefined;
  Camera: {
    mode: 'selfie' | 'biometric';
    onCapture: (uri: string, base64: string) => void;
  };
};
