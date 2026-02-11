import React from 'react';
import {View, ActivityIndicator, Text, StyleSheet} from 'react-native';

interface Props {
  message?: string;
}

export function LoadingScreen({message}: Props) {
  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#2563EB" />
      {message && <Text style={styles.text}>{message}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
  },
  text: {
    marginTop: 16,
    fontSize: 16,
    color: '#6B7280',
  },
});
