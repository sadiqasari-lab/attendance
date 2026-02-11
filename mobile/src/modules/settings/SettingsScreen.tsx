import React, {useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  Alert,
  TouchableOpacity,
} from 'react-native';
import {useNavigation} from '@react-navigation/native';
import {useAuthStore} from '@/store/authStore';
import {useDeviceSecurity} from '@/hooks/useDeviceSecurity';
import {useOfflineSync} from '@/hooks/useOfflineSync';
import {authService} from '@/services/auth.service';
import {Button} from '@/components/Button';

export function SettingsScreen() {
  const navigation = useNavigation<any>();
  const {user, logout} = useAuthStore();
  const {deviceId, isRegistered, isRooted} = useDeviceSecurity();
  const {pendingCount} = useOfflineSync();

  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [showPasswordForm, setShowPasswordForm] = useState(false);

  const handleChangePassword = async () => {
    if (!oldPassword || !newPassword) {
      Alert.alert('Validation', 'Please fill both password fields');
      return;
    }
    if (newPassword.length < 8) {
      Alert.alert('Validation', 'New password must be at least 8 characters');
      return;
    }

    setIsChangingPassword(true);
    try {
      await authService.changePassword(oldPassword, newPassword);
      Alert.alert('Success', 'Password changed successfully');
      setOldPassword('');
      setNewPassword('');
      setShowPasswordForm(false);
    } catch (err: any) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.old_password?.[0] ||
        'Failed to change password';
      Alert.alert('Error', message);
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to sign out?', [
      {text: 'Cancel', style: 'cancel'},
      {text: 'Sign Out', style: 'destructive', onPress: logout},
    ]);
  };

  const handleBiometricEnroll = () => {
    navigation.navigate('BiometricEnroll');
  };

  return (
    <ScrollView style={styles.container}>
      {/* Profile section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Profile</Text>
        <View style={styles.card}>
          <InfoRow label="Name" value={`${user?.first_name} ${user?.last_name}`} />
          <InfoRow label="Email" value={user?.email || ''} />
          <InfoRow label="Role" value={user?.role?.replace(/_/g, ' ') || ''} />
        </View>
      </View>

      {/* Device section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Device</Text>
        <View style={styles.card}>
          <InfoRow label="Device ID" value={deviceId?.slice(0, 12) + '...' || 'Unknown'} />
          <InfoRow label="Status" value={isRegistered ? 'Registered' : 'Not Registered'} />
          <InfoRow
            label="Security"
            value={isRooted ? 'Warning: Rooted' : 'Secure'}
            warning={isRooted}
          />
          <InfoRow
            label="Offline Queue"
            value={`${pendingCount} pending`}
          />
        </View>
      </View>

      {/* Biometric section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Biometric</Text>
        <View style={styles.card}>
          <InfoRow
            label="Status"
            value={
              user?.requires_biometric_enrollment
                ? 'Enrollment Required'
                : 'Enrolled'
            }
          />
          <Button
            title={
              user?.requires_biometric_enrollment
                ? 'Enroll Now'
                : 'Re-enroll'
            }
            onPress={handleBiometricEnroll}
            variant="secondary"
            style={styles.sectionButton}
          />
        </View>
      </View>

      {/* Password section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Security</Text>
        <View style={styles.card}>
          {!showPasswordForm ? (
            <TouchableOpacity onPress={() => setShowPasswordForm(true)}>
              <Text style={styles.linkText}>Change Password</Text>
            </TouchableOpacity>
          ) : (
            <View>
              <TextInput
                style={styles.input}
                placeholder="Current password"
                secureTextEntry
                value={oldPassword}
                onChangeText={setOldPassword}
              />
              <TextInput
                style={styles.input}
                placeholder="New password (min 8 characters)"
                secureTextEntry
                value={newPassword}
                onChangeText={setNewPassword}
              />
              <View style={styles.passwordActions}>
                <Button
                  title="Cancel"
                  onPress={() => {
                    setShowPasswordForm(false);
                    setOldPassword('');
                    setNewPassword('');
                  }}
                  variant="secondary"
                  style={styles.halfButton}
                />
                <Button
                  title="Update"
                  onPress={handleChangePassword}
                  loading={isChangingPassword}
                  style={styles.halfButton}
                />
              </View>
            </View>
          )}
        </View>
      </View>

      {/* Logout */}
      <Button
        title="Sign Out"
        onPress={handleLogout}
        variant="danger"
        style={styles.logoutButton}
      />

      <Text style={styles.version}>Inspire Attendance v1.0.0</Text>
    </ScrollView>
  );
}

function InfoRow({
  label,
  value,
  warning,
}: {
  label: string;
  value: string;
  warning?: boolean;
}) {
  return (
    <View style={infoStyles.row}>
      <Text style={infoStyles.label}>{label}</Text>
      <Text style={[infoStyles.value, warning && infoStyles.warning]}>
        {value}
      </Text>
    </View>
  );
}

const infoStyles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  label: {fontSize: 14, color: '#6B7280'},
  value: {fontSize: 14, fontWeight: '500', color: '#111827', maxWidth: '60%', textAlign: 'right'},
  warning: {color: '#DC2626'},
});

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#F9FAFB'},
  section: {paddingHorizontal: 16, marginTop: 24},
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#6B7280',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
    marginLeft: 4,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
  },
  sectionButton: {marginTop: 12},
  linkText: {
    fontSize: 15,
    color: '#2563EB',
    fontWeight: '500',
    paddingVertical: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 15,
    marginBottom: 10,
  },
  passwordActions: {flexDirection: 'row', gap: 10},
  halfButton: {flex: 1},
  logoutButton: {margin: 16, marginTop: 32},
  version: {
    textAlign: 'center',
    color: '#D1D5DB',
    fontSize: 12,
    marginBottom: 32,
    marginTop: 8,
  },
});
