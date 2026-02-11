import React from 'react';
import {View, Text, StyleSheet} from 'react-native';
import {AttendanceStatus} from '@/types';

interface Props {
  status: AttendanceStatus | string;
}

const STATUS_COLORS: Record<string, {bg: string; text: string}> = {
  [AttendanceStatus.PRESENT]: {bg: '#D1FAE5', text: '#065F46'},
  [AttendanceStatus.LATE]: {bg: '#FEF3C7', text: '#92400E'},
  [AttendanceStatus.EARLY_DEPARTURE]: {bg: '#FEE2E2', text: '#991B1B'},
  [AttendanceStatus.ABSENT]: {bg: '#FEE2E2', text: '#991B1B'},
  [AttendanceStatus.ON_LEAVE]: {bg: '#DBEAFE', text: '#1E40AF'},
  [AttendanceStatus.HOLIDAY]: {bg: '#EDE9FE', text: '#5B21B6'},
};

export function StatusBadge({status}: Props) {
  const colors = STATUS_COLORS[status] || {bg: '#F3F4F6', text: '#374151'};

  return (
    <View style={[styles.badge, {backgroundColor: colors.bg}]}>
      <Text style={[styles.text, {color: colors.text}]}>
        {status.replace(/_/g, ' ')}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  text: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
});
