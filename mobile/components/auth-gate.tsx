import { useEffect } from 'react';
import type { ReactNode } from 'react';
import { router, Stack } from 'expo-router';
import { useSession } from '../lib/api/queries';
import { useAuth } from '../store/auth';
import { Body, Button, ErrorMessage, Loading, Panel, Screen } from './ui';

export function AuthGate({ children }: { children: ReactNode }) {
  const session = useSession();
  const setUser = useAuth(state => state.setUser);
  useEffect(() => { setUser(session.data?.user ?? null); }, [session.data, setUser]);
  if (session.isPending) return <Screen compact title="Welcome to your studio"><Loading label="Checking your session…" /></Screen>;
  if (session.isError) return <Screen compact title="Your studio connection"><ErrorMessage message={session.error.message} retry={() => void session.refetch()} /></Screen>;
  if (!session.data.user) return <Screen compact title="A look that" emphasis="feels like you." description="Sign in with your BeautyCore Client account.">
    <Stack.Screen options={{ headerRight: () => null }} /><Panel title="Your personal beauty studio"><Body>Your existing BeautyCore account connects your three Custom Studios.</Body>
      <Button label="Sign in" onPress={() => router.push('/login')} /></Panel>
  </Screen>;
  if (session.data.user.role !== 'client') return <Screen compact title="Client access required"><Panel title="Your BeautyCore account">
    <Body>This mobile beauty studio is available to Client accounts.</Body><Button label="Open account settings" onPress={() => router.push('/settings')} />
  </Panel></Screen>;
  return children;
}
