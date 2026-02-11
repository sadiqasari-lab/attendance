import React, {useEffect, useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import {useAttendanceStore} from '@/store/attendanceStore';
import {StatusBadge} from '@/components/StatusBadge';
import {LoadingScreen} from '@/components/LoadingScreen';
import {formatDate, formatTime, formatDuration} from '@/utils/helpers';
import type {AttendanceRecord} from '@/types';

export function AttendanceHistoryScreen() {
  const {records, isLoading, loadRecords} = useAttendanceStore();
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<'week' | 'month' | 'all'>('week');

  const getDateRange = () => {
    const end = new Date();
    const start = new Date();
    if (filter === 'week') {
      start.setDate(end.getDate() - 7);
    } else if (filter === 'month') {
      start.setMonth(end.getMonth() - 1);
    } else {
      start.setMonth(end.getMonth() - 3);
    }
    return {
      start_date: formatDate(start),
      end_date: formatDate(end),
    };
  };

  useEffect(() => {
    loadRecords(getDateRange());
  }, [filter, loadRecords]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadRecords(getDateRange());
    setRefreshing(false);
  };

  const renderItem = ({item}: {item: AttendanceRecord}) => (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.dateText}>{item.date}</Text>
        <StatusBadge status={item.status} />
      </View>
      <View style={styles.cardBody}>
        <View style={styles.timeCol}>
          <Text style={styles.timeLabel}>In</Text>
          <Text style={styles.timeValue}>
            {item.clock_in_time ? formatTime(item.clock_in_time) : '--:--'}
          </Text>
        </View>
        <View style={styles.timeCol}>
          <Text style={styles.timeLabel}>Out</Text>
          <Text style={styles.timeValue}>
            {item.clock_out_time ? formatTime(item.clock_out_time) : '--:--'}
          </Text>
        </View>
        <View style={styles.timeCol}>
          <Text style={styles.timeLabel}>Duration</Text>
          <Text style={styles.timeValue}>
            {item.duration_minutes
              ? formatDuration(item.duration_minutes)
              : '--:--'}
          </Text>
        </View>
      </View>
      {item.is_offline_record && (
        <Text style={styles.offlineTag}>Offline Record</Text>
      )}
    </View>
  );

  if (isLoading && records.length === 0) {
    return <LoadingScreen message="Loading attendance history..." />;
  }

  return (
    <View style={styles.container}>
      <View style={styles.filterRow}>
        {(['week', 'month', 'all'] as const).map(f => (
          <TouchableOpacity
            key={f}
            style={[styles.filterChip, filter === f && styles.filterActive]}
            onPress={() => setFilter(f)}>
            <Text
              style={[
                styles.filterText,
                filter === f && styles.filterTextActive,
              ]}>
              {f === 'week' ? 'This Week' : f === 'month' ? 'This Month' : 'All'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList
        data={records}
        renderItem={renderItem}
        keyExtractor={item => item.id}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <Text style={styles.empty}>No attendance records found</Text>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#F9FAFB'},
  filterRow: {
    flexDirection: 'row',
    padding: 16,
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#E5E7EB',
  },
  filterActive: {
    backgroundColor: '#2563EB',
  },
  filterText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#6B7280',
  },
  filterTextActive: {
    color: '#FFFFFF',
  },
  list: {paddingHorizontal: 16, paddingBottom: 24},
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.03,
    shadowRadius: 3,
    elevation: 1,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  dateText: {fontSize: 15, fontWeight: '600', color: '#111827'},
  cardBody: {flexDirection: 'row', justifyContent: 'space-around'},
  timeCol: {alignItems: 'center'},
  timeLabel: {fontSize: 11, color: '#9CA3AF'},
  timeValue: {fontSize: 16, fontWeight: '600', color: '#111827', marginTop: 2},
  offlineTag: {
    fontSize: 11,
    color: '#F59E0B',
    marginTop: 8,
    fontStyle: 'italic',
  },
  empty: {
    textAlign: 'center',
    color: '#9CA3AF',
    fontSize: 14,
    marginTop: 48,
  },
});
