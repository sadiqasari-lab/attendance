import {useState, useCallback} from 'react';
import Geolocation from '@react-native-community/geolocation';
import {Platform, PermissionsAndroid} from 'react-native';
import {GPS_CONFIG} from '@/utils/constants';

interface LocationData {
  latitude: number;
  longitude: number;
  accuracy: number;
  isMockLocation: boolean;
}

interface UseLocationReturn {
  location: LocationData | null;
  isLoading: boolean;
  error: string | null;
  getCurrentLocation: () => Promise<LocationData>;
}

export function useLocation(): UseLocationReturn {
  const [location, setLocation] = useState<LocationData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const requestPermission = async (): Promise<boolean> => {
    if (Platform.OS === 'android') {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
        {
          title: 'Location Permission',
          message:
            'Inspire Attendance needs access to your location for attendance verification.',
          buttonPositive: 'Allow',
          buttonNegative: 'Deny',
        },
      );
      return granted === PermissionsAndroid.RESULTS.GRANTED;
    }
    return true; // iOS handles via Info.plist
  };

  const getCurrentLocation = useCallback(async (): Promise<LocationData> => {
    setIsLoading(true);
    setError(null);

    const hasPermission = await requestPermission();
    if (!hasPermission) {
      setIsLoading(false);
      const err = 'Location permission denied';
      setError(err);
      throw new Error(err);
    }

    return new Promise((resolve, reject) => {
      Geolocation.getCurrentPosition(
        position => {
          const data: LocationData = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy || 0,
            isMockLocation: false, // Checked separately via device security
          };
          setLocation(data);
          setIsLoading(false);
          resolve(data);
        },
        err => {
          let message = 'Failed to get location';
          switch (err.code) {
            case 1:
              message = 'Location permission denied';
              break;
            case 2:
              message = 'Location unavailable. Please enable GPS.';
              break;
            case 3:
              message = 'Location request timed out';
              break;
          }
          setError(message);
          setIsLoading(false);
          reject(new Error(message));
        },
        {
          enableHighAccuracy: GPS_CONFIG.HIGH_ACCURACY,
          timeout: GPS_CONFIG.TIMEOUT_MS,
          maximumAge: GPS_CONFIG.MAX_AGE_MS,
        },
      );
    });
  }, []);

  return {location, isLoading, error, getCurrentLocation};
}
