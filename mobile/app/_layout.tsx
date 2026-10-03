import { useState } from 'react';
import { router, Stack } from 'expo-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { colors, serif } from '../constants/theme';
import { HeaderAction } from '../components/workflow';

export default function RootLayout() {
  const [queryClient] = useState(() => new QueryClient({ defaultOptions: { queries: {
    retry: false, refetchOnWindowFocus: false, refetchOnReconnect: false,
  } } }));
  return <SafeAreaProvider><QueryClientProvider client={queryClient}><StatusBar style="light" />
    <Stack screenOptions={{ headerStyle: { backgroundColor: colors.deep }, headerTintColor: colors.gold,
      headerTitleStyle: { fontFamily: serif, color: colors.white }, contentStyle: { backgroundColor: colors.deep },
      headerRight: () => <HeaderAction label="Settings" glyph="⚙" onPress={() => router.push('/settings')} /> }}>
      <Stack.Screen name="index" options={{ title: 'ANDREA’S ✦' }} />
      <Stack.Screen name="hair" options={{ title: 'Hairstyle' }} />
      <Stack.Screen name="makeup" options={{ title: 'Makeup' }} />
      <Stack.Screen name="nails" options={{ title: 'Nails' }} />
      <Stack.Screen name="consultation" options={{ title: 'Consultation' }} />
      <Stack.Screen name="connection" options={{ title: 'API connection' }} />
      <Stack.Screen name="settings" options={{ title: 'Settings', headerRight: () => null }} />
      <Stack.Screen name="result" options={{ title: 'Your look' }} />
    </Stack>
  </QueryClientProvider></SafeAreaProvider>;
}
