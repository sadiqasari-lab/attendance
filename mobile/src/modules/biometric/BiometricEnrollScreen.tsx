import React, {useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  Alert,
} from 'react-native';
import {useNavigation} from '@react-navigation/native';
import {useCamera} from '@/hooks/useCamera';
import {biometricService} from '@/services/biometric.service';
import {Button} from '@/components/Button';
import {BIOMETRIC_CONFIG} from '@/utils/constants';
import {secureStorage} from '@/utils/storage';
import {STORAGE_KEYS} from '@/utils/constants';

const ANGLE_INSTRUCTIONS = [
  'Look straight at the camera',
  'Turn your head slightly to the left',
  'Turn your head slightly to the right',
];

export function BiometricEnrollScreen() {
  const navigation = useNavigation<any>();
  const {captureSelfie, isCapturing} = useCamera();

  const [captures, setCaptures] = useState<
    Array<{uri: string; base64: string}>
  >([]);
  const [isEnrolling, setIsEnrolling] = useState(false);
  const currentStep = captures.length;
  const totalSteps = BIOMETRIC_CONFIG.REQUIRED_ANGLES;
  const isComplete = currentStep >= totalSteps;

  const handleCapture = async () => {
    try {
      const result = await captureSelfie();
      setCaptures(prev => [...prev, {uri: result.uri, base64: result.base64}]);
    } catch (err: any) {
      Alert.alert('Camera Error', err.message);
    }
  };

  const handleRemoveLast = () => {
    setCaptures(prev => prev.slice(0, -1));
  };

  const handleEnroll = async () => {
    if (!isComplete) return;

    setIsEnrolling(true);
    try {
      const images = captures.map(c => c.base64);
      await biometricService.enroll(images);
      await secureStorage.set(STORAGE_KEYS.BIOMETRIC_ENROLLED, 'true');

      Alert.alert(
        'Enrollment Complete',
        'Your biometric profile has been created successfully.',
        [{text: 'OK', onPress: () => navigation.goBack()}],
      );
    } catch (err: any) {
      const message =
        err.response?.data?.detail || 'Biometric enrollment failed';
      Alert.alert('Enrollment Failed', message);
    } finally {
      setIsEnrolling(false);
    }
  };

  const handleReset = () => {
    setCaptures([]);
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Biometric Enrollment</Text>
        <Text style={styles.subtitle}>
          We need {totalSteps} photos from different angles to create your
          biometric profile.
        </Text>

        {/* Progress */}
        <View style={styles.progressBar}>
          {Array.from({length: totalSteps}).map((_, i) => (
            <View
              key={i}
              style={[
                styles.progressDot,
                i < currentStep && styles.progressDotComplete,
                i === currentStep && styles.progressDotCurrent,
              ]}
            />
          ))}
        </View>
        <Text style={styles.progressText}>
          {currentStep} of {totalSteps} photos captured
        </Text>

        {/* Captured images preview */}
        {captures.length > 0 && (
          <View style={styles.previewRow}>
            {captures.map((cap, i) => (
              <View key={i} style={styles.previewItem}>
                <Image source={{uri: cap.uri}} style={styles.previewImage} />
                <Text style={styles.previewLabel}>Angle {i + 1}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Current instruction */}
        {!isComplete && (
          <View style={styles.instructionCard}>
            <Text style={styles.instructionStep}>
              Step {currentStep + 1}
            </Text>
            <Text style={styles.instructionText}>
              {ANGLE_INSTRUCTIONS[currentStep] || 'Capture another angle'}
            </Text>

            <View style={styles.captureFrame}>
              <Text style={styles.captureHint}>Position your face</Text>
            </View>

            <Button
              title={`Capture Photo ${currentStep + 1}`}
              onPress={handleCapture}
              loading={isCapturing}
            />

            {captures.length > 0 && (
              <Button
                title="Retake Last"
                onPress={handleRemoveLast}
                variant="secondary"
                style={styles.retakeButton}
              />
            )}
          </View>
        )}

        {/* Enrollment action */}
        {isComplete && (
          <View style={styles.enrollSection}>
            <Text style={styles.enrollReady}>
              All photos captured! Ready to enroll.
            </Text>
            <Button
              title="Complete Enrollment"
              onPress={handleEnroll}
              loading={isEnrolling}
              style={styles.enrollButton}
            />
            <Button
              title="Start Over"
              onPress={handleReset}
              variant="secondary"
              style={styles.retakeButton}
            />
          </View>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#F9FAFB'},
  content: {padding: 24},
  title: {fontSize: 24, fontWeight: '700', color: '#111827'},
  subtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
    marginBottom: 24,
    lineHeight: 20,
  },
  progressBar: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 12,
    marginBottom: 8,
  },
  progressDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#E5E7EB',
  },
  progressDotComplete: {
    backgroundColor: '#10B981',
  },
  progressDotCurrent: {
    backgroundColor: '#2563EB',
    width: 14,
    height: 14,
    borderRadius: 7,
  },
  progressText: {
    textAlign: 'center',
    fontSize: 13,
    color: '#6B7280',
    marginBottom: 24,
  },
  previewRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 12,
    marginBottom: 24,
  },
  previewItem: {alignItems: 'center'},
  previewImage: {
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 2,
    borderColor: '#10B981',
  },
  previewLabel: {
    fontSize: 11,
    color: '#6B7280',
    marginTop: 4,
  },
  instructionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 24,
    alignItems: 'center',
  },
  instructionStep: {
    fontSize: 13,
    fontWeight: '600',
    color: '#2563EB',
    marginBottom: 4,
  },
  instructionText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#111827',
    marginBottom: 24,
    textAlign: 'center',
  },
  captureFrame: {
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: '#F3F4F6',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
    borderWidth: 3,
    borderColor: '#2563EB',
    borderStyle: 'dashed',
  },
  captureHint: {fontSize: 13, color: '#9CA3AF'},
  retakeButton: {marginTop: 12},
  enrollSection: {alignItems: 'center'},
  enrollReady: {
    fontSize: 16,
    fontWeight: '600',
    color: '#10B981',
    marginBottom: 20,
    textAlign: 'center',
  },
  enrollButton: {width: '100%'},
});
