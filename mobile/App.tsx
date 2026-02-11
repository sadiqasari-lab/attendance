import React from 'react';
import {SafeAreaProvider} from 'react-native-safe-area-context';
import {ErrorBoundary} from '@/components/ErrorBoundary';
import {AppNavigator} from '@/navigation/AppNavigator';

export default function App() {
  return (
    <SafeAreaProvider>
      <ErrorBoundary>
        <AppNavigator />
      </ErrorBoundary>
    </SafeAreaProvider>
  );
}
