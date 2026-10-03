import { useRef, useState } from 'react';
import { StyleSheet, TextInput, View } from 'react-native';
import { router } from 'expo-router';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api/client';
import { useAuth } from '../store/auth';
import { Screen, Panel, Body, Button, ErrorMessage, Loading } from '../components/ui';
import { colors, layout, spacing, type } from '../constants/theme';

export default function Login() {
  const [email, setEmail] = useState(''); const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  const submitting = useRef(false);
  const cache = useQueryClient();
  async function signIn() {
    if (submitting.current) return;
    submitting.current = true;
    setBusy(true); setError('');
    try {
      await api.login(email.trim(), password);
      setPassword('');
      // A 200 login alone cannot prove Android retained its HttpOnly cookie.
      const session = await api.session();
      if (!session.user) throw new Error('The device did not retain your session. Sign in again; if this continues, report the session error.');
      useAuth.getState().setUser(session.user); cache.clear(); cache.setQueryData(['session'], session);
      if (session.user.role !== 'client') { router.replace('/settings'); return; }
      await api.features(); // Proves current Client authorization independently.
      router.replace('/');
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Sign in failed. Please try again.'); }
    finally { submitting.current = false; setBusy(false); }
  }
  return <Screen compact title="Welcome back." emphasis="Your next look awaits." description="Sign in with your existing BeautyCore account.">
    <Panel title="Client sign in">
      <View style={styles.field}><Body>Email address</Body><TextInput accessibilityLabel="Email address" value={email} onChangeText={setEmail}
        autoCapitalize="none" autoCorrect={false} keyboardType="email-address" autoComplete="email" editable={!busy} style={styles.input} /></View>
      <View style={styles.field}><Body>Password</Body><TextInput accessibilityLabel="Password" value={password} onChangeText={setPassword}
        secureTextEntry autoCapitalize="none" autoCorrect={false} autoComplete="current-password" editable={!busy} style={styles.input} /></View>
      {error !== '' && <ErrorMessage message={error} />}
      {busy && <Loading label="Signing you in…" />}
      <Button label="Sign in to BeautyCore" disabled={busy || !email.trim() || !password} onPress={() => void signIn()} />
      <Body muted>Your account is verified by BeautyCore. Your password is never saved in the app.</Body>
    </Panel>
  </Screen>;
}
const styles = StyleSheet.create({ field: { gap: spacing.xs }, input: { minHeight: layout.touch, color: colors.white,
  fontSize: type.body, backgroundColor: colors.card, borderWidth: 1, borderColor: colors.border, padding: spacing.sm } });
