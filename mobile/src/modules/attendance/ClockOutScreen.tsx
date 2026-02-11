import React, {useState} from 'react';
import {View, Text, StyleSheet, ScrollView, Image, Alert} from 'react-native';
import {useNavigation, useRoute, RouteProp} from '@react-navigation/native';
import {useLocation} from '@/hooks/useLocation';
import {useCamera} from '@/hooks/useCamera';
import {attendanceService} from '@/services/attendance.service';
import {Button} from '@/components/Button';
import {getCurrentTimestamp} from '@/utils/helpers';
import type {NavigationParamList} from '@/types';

type ClockOutRoute = RouteProp<NavigationParamList, 'ClockOut'>;

export function ClockOutScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<ClockOutRoute>();
  const {attendanceId} = route.params;

  const {getCurrentLocation} = useLocation();
  const {captureSelfie, isCapturing} = useCamera();

  const [selfieUri, setSelfieUri] = useState<string | null>(null);
  const [selfieBase64, setSelfieBase64] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleCaptureSelfie = async () => {
    try {
      const result = await captureSelfie();
      setSelfieUri(result.uri);
      setSelfieBase64(result.base64);
    } catch (err: any) {
      Alert.alert('Camera Error', err.message);
    }
  };

  const handleClockOut = async () => {
    if (!selfieBase64) return;

    setIsSubmitting(true);
    try {
      const location = await getCurrentLocation();

      await attendanceService.clockOut({
        attendance_id: attendanceId,
        selfie: selfieBase64,
        latitude: location.latitude,
        longitude: location.longitude,
        gps_accuracy: location.accuracy,
        client_timestamp: getCurrentTimestamp(),
      });

      Alert.alert('Success', 'Clock-out recorded successfully', [
        {text: 'OK', onPress: () => navigation.goBack()},
      ]);
    } catch (err: any) {
      const message =
        err.response?.data?.detail || err.message || 'Clock-out failed';
      Alert.alert('Error', message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Clock Out</Text>
        <Text style={styles.subtitle}>
          Take a selfie to confirm your departure
        </Text>

        {selfieUri ? (
          <View style={styles.preview}>
            <Image source={{uri: selfieUri}} style={styles.selfieImage} />
            <View style={styles.buttonRow}>
              <Button
                title="Retake"
                onPress={() => {
                  setSelfieUri(null);
                  setSelfieBase64(null);
                }}
                variant="secondary"
                style={styles.halfButton}
              />
              <Button
                title="Confirm Clock Out"
                onPress={handleClockOut}
                loading={isSubmitting}
                variant="danger"
                style={styles.halfButton}
              />
            </View>
          </View>
        ) : (
          <View style={styles.captureSection}>
            <View style={styles.selfieFrame}>
              <Text style={styles.frameText}>Tap to capture</Text>
            </View>
            <Button
              title="Take Selfie"
              onPress={handleCaptureSelfie}
              loading={isCapturing}
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
  subtitle: {fontSize: 14, color: '#6B7280', marginTop: 4, marginBottom: 24},
  captureSection: {alignItems: 'center'},
  selfieFrame: {
    width: 280,
    height: 280,
    borderRadius: 140,
    backgroundColor: '#E5E7EB',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
    borderWidth: 3,
    borderColor: '#DC2626',
    borderStyle: 'dashed',
  },
  frameText: {fontSize: 14, color: '#9CA3AF'},
  preview: {alignItems: 'center'},
  selfieImage: {
    width: 200,
    height: 200,
    borderRadius: 100,
    marginBottom: 24,
  },
  buttonRow: {flexDirection: 'row', width: '100%', gap: 12},
  halfButton: {flex: 1},
});
