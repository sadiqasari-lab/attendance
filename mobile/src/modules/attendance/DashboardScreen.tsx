import React, {useEffect, useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
} from 'react-native';
import {useNavigation} from '@react-navigation/native';
import {useAuthStore} from '@/store/authStore';
import {useAttendanceStore} from '@/store/attendanceStore';
import {useOfflineSync} from '@/hooks/useOfflineSync';
import {Button} from '@/components/Button';
import {StatusBadge} from '@/components/StatusBadge';
import {formatDate, formatTime, formatDuration} from '@/utils/helpers';

export function DashboardScreen() {
  const navigation = useNavigation<any>();
  const {user} = useAuthStore();
  const {shifts, records, summary, activeRecord, loadShifts, loadRecords, loadSummary} =
    useAttendanceStore();
  const {pendingCount, isSyncing, syncNow} = useOfflineSync();
  const [refreshing, setRefreshing] = useState(false);

  const today = formatDate(new Date());

  useEffect(() => {
    loadShifts();
    loadRecords({start_date: today, end_date: today});
    loadSummary(today, today);
  }, [loadShifts, loadRecords, loadSummary, today]);

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([
      loadShifts(),
      loadRecords({start_date: today, end_date: today}),
      loadSummary(today, today),
    ]);
    setRefreshing(false);
  };

  const todayRecord = records.find(r => r.date === today);

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }>
      <View style={styles.header}>
        <Text style={styles.greeting}>
          Hello, {user?.first_name || 'Employee'}
        </Text>
        <Text style={styles.date}>{new Date().toLocaleDateString('en-US', {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric',
        })}</Text>
      </View>

      {/* Offline sync banner */}
      {pendingCount > 0 && (
        <View style={styles.offlineBanner}>
          <Text style={styles.offlineText}>
            {pendingCount} offline record{pendingCount > 1 ? 's' : ''} pending sync
          </Text>
          <Button
            title={isSyncing ? 'Syncing...' : 'Sync Now'}
            onPress={syncNow}
            loading={isSyncing}
            variant="secondary"
            style={styles.syncButton}
          />
        </View>
      )}

      {/* Today's status card */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Today's Attendance</Text>
        {todayRecord ? (
          <View>
            <View style={styles.statusRow}>
              <StatusBadge status={todayRecord.status} />
              {todayRecord.duration_minutes && (
                <Text style={styles.duration}>
                  {formatDuration(todayRecord.duration_minutes)}
                </Text>
              )}
            </View>
            <View style={styles.timeRow}>
              <View>
                <Text style={styles.timeLabel}>Clock In</Text>
                <Text style={styles.timeValue}>
                  {todayRecord.clock_in_time
                    ? formatTime(todayRecord.clock_in_time)
                    : '--:--'}
                </Text>
              </View>
              <View>
                <Text style={styles.timeLabel}>Clock Out</Text>
                <Text style={styles.timeValue}>
                  {todayRecord.clock_out_time
                    ? formatTime(todayRecord.clock_out_time)
                    : '--:--'}
                </Text>
              </View>
            </View>
          </View>
        ) : (
          <Text style={styles.noRecord}>No attendance recorded yet</Text>
        )}
      </View>

      {/* Action buttons */}
      <View style={styles.actions}>
        {!todayRecord?.clock_in_time && shifts.length > 0 && (
          <Button
            title="Clock In"
            onPress={() =>
              navigation.navigate('ClockIn', {shiftId: shifts[0].id})
            }
            style={styles.actionButton}
          />
        )}
        {todayRecord?.clock_in_time && !todayRecord?.clock_out_time && (
          <Button
            title="Clock Out"
            onPress={() =>
              navigation.navigate('ClockOut', {
                attendanceId: todayRecord.id,
              })
            }
            variant="secondary"
            style={styles.actionButton}
          />
        )}
      </View>

      {/* Summary stats */}
      {summary && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>This Period</Text>
          <View style={styles.statsGrid}>
            <View style={styles.stat}>
              <Text style={styles.statValue}>{summary.present_days}</Text>
              <Text style={styles.statLabel}>Present</Text>
            </View>
            <View style={styles.stat}>
              <Text style={[styles.statValue, {color: '#F59E0B'}]}>
                {summary.late_days}
              </Text>
              <Text style={styles.statLabel}>Late</Text>
            </View>
            <View style={styles.stat}>
              <Text style={[styles.statValue, {color: '#EF4444'}]}>
                {summary.absent_days}
              </Text>
              <Text style={styles.statLabel}>Absent</Text>
            </View>
            <View style={styles.stat}>
              <Text style={[styles.statValue, {color: '#8B5CF6'}]}>
                {summary.average_hours.toFixed(1)}h
              </Text>
              <Text style={styles.statLabel}>Avg Hours</Text>
            </View>
          </View>
        </View>
      )}

      <Button
        title="View History"
        onPress={() => navigation.navigate('AttendanceHistory')}
        variant="secondary"
        style={styles.historyButton}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    padding: 24,
    paddingBottom: 16,
  },
  greeting: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
  },
  date: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  offlineBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FEF3C7',
    marginHorizontal: 16,
    marginBottom: 16,
    padding: 12,
    borderRadius: 10,
  },
  offlineText: {
    fontSize: 13,
    color: '#92400E',
    flex: 1,
  },
  syncButton: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    marginLeft: 8,
  },
  card: {
    backgroundColor: '#FFFFFF',
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 14,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 1,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 16,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  duration: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  timeRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  timeLabel: {
    fontSize: 12,
    color: '#9CA3AF',
    textAlign: 'center',
  },
  timeValue: {
    fontSize: 20,
    fontWeight: '600',
    color: '#111827',
    textAlign: 'center',
    marginTop: 4,
  },
  noRecord: {
    fontSize: 14,
    color: '#9CA3AF',
    textAlign: 'center',
    paddingVertical: 16,
  },
  actions: {
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  actionButton: {
    marginBottom: 8,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  stat: {
    alignItems: 'center',
    flex: 1,
  },
  statValue: {
    fontSize: 22,
    fontWeight: '700',
    color: '#10B981',
  },
  statLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 4,
  },
  historyButton: {
    marginHorizontal: 16,
    marginBottom: 32,
  },
});
