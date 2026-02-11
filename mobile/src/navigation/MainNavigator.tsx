import React from 'react';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {createNativeStackNavigator} from '@react-navigation/native-stack';
import {DashboardScreen} from '@/modules/attendance/DashboardScreen';
import {AttendanceHistoryScreen} from '@/modules/attendance/AttendanceHistoryScreen';
import {ClockInScreen} from '@/modules/attendance/ClockInScreen';
import {ClockOutScreen} from '@/modules/attendance/ClockOutScreen';
import {BiometricEnrollScreen} from '@/modules/biometric/BiometricEnrollScreen';
import {SettingsScreen} from '@/modules/settings/SettingsScreen';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

function HomeStack() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {backgroundColor: '#FFFFFF'},
        headerTintColor: '#111827',
        headerTitleStyle: {fontWeight: '600'},
      }}>
      <Stack.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{title: 'Inspire Attendance'}}
      />
      <Stack.Screen
        name="ClockIn"
        component={ClockInScreen}
        options={{title: 'Clock In'}}
      />
      <Stack.Screen
        name="ClockOut"
        component={ClockOutScreen}
        options={{title: 'Clock Out'}}
      />
      <Stack.Screen
        name="BiometricEnroll"
        component={BiometricEnrollScreen}
        options={{title: 'Biometric Enrollment'}}
      />
    </Stack.Navigator>
  );
}

function HistoryStack() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {backgroundColor: '#FFFFFF'},
        headerTintColor: '#111827',
        headerTitleStyle: {fontWeight: '600'},
      }}>
      <Stack.Screen
        name="AttendanceHistory"
        component={AttendanceHistoryScreen}
        options={{title: 'History'}}
      />
    </Stack.Navigator>
  );
}

function SettingsStack() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {backgroundColor: '#FFFFFF'},
        headerTintColor: '#111827',
        headerTitleStyle: {fontWeight: '600'},
      }}>
      <Stack.Screen
        name="Settings"
        component={SettingsScreen}
        options={{title: 'Settings'}}
      />
      <Stack.Screen
        name="BiometricEnroll"
        component={BiometricEnrollScreen}
        options={{title: 'Biometric Enrollment'}}
      />
    </Stack.Navigator>
  );
}

export function MainNavigator() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: '#2563EB',
        tabBarInactiveTintColor: '#9CA3AF',
        tabBarStyle: {
          backgroundColor: '#FFFFFF',
          borderTopColor: '#E5E7EB',
          paddingBottom: 4,
          height: 56,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '500',
        },
      }}>
      <Tab.Screen
        name="HomeTab"
        component={HomeStack}
        options={{
          tabBarLabel: 'Home',
        }}
      />
      <Tab.Screen
        name="HistoryTab"
        component={HistoryStack}
        options={{
          tabBarLabel: 'History',
        }}
      />
      <Tab.Screen
        name="SettingsTab"
        component={SettingsStack}
        options={{
          tabBarLabel: 'Settings',
        }}
      />
    </Tab.Navigator>
  );
}
