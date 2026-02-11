import {useState, useCallback} from 'react';
import {Platform, PermissionsAndroid} from 'react-native';
import {launchCamera, CameraOptions, Asset} from 'react-native-image-picker';

interface CaptureResult {
  uri: string;
  base64: string;
  width: number;
  height: number;
}

interface UseCameraReturn {
  isCapturing: boolean;
  error: string | null;
  captureSelfie: () => Promise<CaptureResult>;
}

export function useCamera(): UseCameraReturn {
  const [isCapturing, setIsCapturing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const requestPermission = async (): Promise<boolean> => {
    if (Platform.OS === 'android') {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.CAMERA,
        {
          title: 'Camera Permission',
          message:
            'Inspire Attendance needs camera access for selfie verification.',
          buttonPositive: 'Allow',
          buttonNegative: 'Deny',
        },
      );
      return granted === PermissionsAndroid.RESULTS.GRANTED;
    }
    return true;
  };

  const captureSelfie = useCallback(async (): Promise<CaptureResult> => {
    setIsCapturing(true);
    setError(null);

    const hasPermission = await requestPermission();
    if (!hasPermission) {
      setIsCapturing(false);
      throw new Error('Camera permission denied');
    }

    const options: CameraOptions = {
      mediaType: 'photo',
      cameraType: 'front',
      includeBase64: true,
      quality: 0.8,
      maxWidth: 640,
      maxHeight: 640,
      saveToPhotos: false,
    };

    return new Promise((resolve, reject) => {
      launchCamera(options, response => {
        setIsCapturing(false);

        if (response.didCancel) {
          const msg = 'Camera cancelled';
          setError(msg);
          reject(new Error(msg));
          return;
        }

        if (response.errorCode) {
          const msg = response.errorMessage || 'Camera error';
          setError(msg);
          reject(new Error(msg));
          return;
        }

        const asset: Asset | undefined = response.assets?.[0];
        if (!asset?.uri || !asset?.base64) {
          const msg = 'Failed to capture image';
          setError(msg);
          reject(new Error(msg));
          return;
        }

        resolve({
          uri: asset.uri,
          base64: asset.base64,
          width: asset.width || 640,
          height: asset.height || 640,
        });
      });
    });
  }, []);

  return {isCapturing, error, captureSelfie};
}
