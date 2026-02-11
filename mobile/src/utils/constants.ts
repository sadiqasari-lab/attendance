import {Platform} from 'react-native';

export const API_BASE_URL = __DEV__
  ? Platform.OS === 'android'
    ? 'http://10.0.2.2:8000/api/v1'
    : 'http://localhost:8000/api/v1'
  : 'https://attendance.arabinspire.com/api/v1';

export const WS_BASE_URL = __DEV__
  ? Platform.OS === 'android'
    ? 'ws://10.0.2.2:8000/ws'
    : 'ws://localhost:8000/ws'
  : 'wss://attendance.arabinspire.com/ws';

export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_DATA: 'user_data',
  TENANT_SLUG: 'tenant_slug',
  DEVICE_ID: 'device_id',
  OFFLINE_QUEUE: 'offline_queue',
  BIOMETRIC_ENROLLED: 'biometric_enrolled',
} as const;

export const GPS_CONFIG = {
  TIMEOUT_MS: 15000,
  MAX_AGE_MS: 5000,
  HIGH_ACCURACY: true,
};

export const BIOMETRIC_CONFIG = {
  MIN_QUALITY: 0.7,
  FACE_MATCH_THRESHOLD: 0.6,
  REQUIRED_ANGLES: 3,
  LIVENESS_ACTIONS: ['blink', 'turn_left', 'turn_right', 'smile'] as const,
};

export const OFFLINE_CONFIG = {
  MAX_QUEUE_SIZE: 50,
  SYNC_INTERVAL_MS: 30000,
  MAX_OFFLINE_PER_SHIFT: 1,
};

export const APP_CONFIG = {
  APP_NAME: 'Inspire Attendance',
  VERSION: '1.0.0',
  MIN_ANDROID_SDK: 24,
};
