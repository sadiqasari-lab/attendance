import React, {useEffect} from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {useAuthStore} from '@/store/authStore';
import {AuthNavigator} from './AuthNavigator';
import {MainNavigator} from './MainNavigator';
import {LoadingScreen} from '@/components/LoadingScreen';

export function AppNavigator() {
  const {isAuthenticated, isLoading, loadUser} = useAuthStore();

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  if (isLoading) {
    return <LoadingScreen message="Loading..." />;
  }

  return (
    <NavigationContainer>
      {isAuthenticated ? <MainNavigator /> : <AuthNavigator />}
    </NavigationContainer>
  );
}
