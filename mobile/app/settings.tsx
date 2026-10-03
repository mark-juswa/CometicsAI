import { useState } from 'react';
import { router } from 'expo-router';
import { useQueryClient } from '@tanstack/react-query';
import { Screen, Panel, Body, Button, ErrorMessage, Loading } from '../components/ui';
import { useSession } from '../lib/api/queries';
import { api } from '../lib/api/client';
import { apiBaseUrl } from '../lib/config/environment';
import { useAuth } from '../store/auth';
import { featureIds } from '../lib/api/contracts';
import { useStudio } from '../store/studio';
import { useConsultation } from '../store/consultation';
import { isUnresolved, useGeneration } from '../store/generation';

export default function Settings() {
  const session = useSession(); const cache = useQueryClient();
  const job = useGeneration(state => state.job);
  const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  const [catalogReady, setCatalogReady] = useState(false);
  async function check() {
    setBusy(true); setError(''); setCatalogReady(false);
    try {
      const value = await api.session(); cache.setQueryData(['session'], value); useAuth.getState().setUser(value.user);
      if (value.user?.role === 'client') { await api.features(); setCatalogReady(true); }
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Connection failed.'); }
    finally { setBusy(false); }
  }
  async function logout() {
    if (busy || isUnresolved(useGeneration.getState().job)) return;
    setBusy(true); setError('');
    try {
      await api.logout();
      const after = await api.session();
      if (after.user) throw new Error('Your session could not be cleared. Please try signing out again.');
      useAuth.getState().setUser(null); useGeneration.getState().clear();
      for (const feature of featureIds) useStudio.getState().reset(feature);
      useConsultation.getState().reset(); cache.clear(); cache.setQueryData(['session'], { user: null });
      router.replace('/');
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Sign out failed.'); }
    finally { setBusy(false); }
  }
  return <Screen compact title="Your studio settings" description="Your BeautyCore account and connection.">
    <Panel title="BeautyCore account">
      {session.isPending && <Loading label="Checking your session…" />}
      {session.data?.user ? <><Body>{session.data.user.name}</Body><Body muted>{session.data.user.email} · {session.data.user.role}</Body>
        <Button label="Sign out" secondary disabled={busy || isUnresolved(job)} onPress={() => void logout()} /></> :
        <><Body>Sign in to use your personal studios.</Body><Button label="Sign in" onPress={() => router.push('/login')} /></>}
      {isUnresolved(job) && <Body muted>Finish or resolve the current generation before signing out.</Body>}
    </Panel>
    <Panel title="Studio connection" detail="Check BeautyCore and your authenticated studio access.">
      {(busy || session.isFetching) && <Loading label="Checking connection…" />}
      {(error || session.isError) && <ErrorMessage message={error || session.error?.message || 'Connection failed.'} />}
      {session.isSuccess && !session.isFetching && !error && <Body>Connected · {session.data.user ? 'Session available.' : 'Sign in required.'}</Body>}
      {catalogReady && <Body>Client studio access confirmed.</Body>}
      <Button label="Check connection" disabled={busy || session.isFetching} onPress={() => void check()} />
      <Body muted>{apiBaseUrl || 'No application address configured.'}</Body>
    </Panel>
    <Panel title="Your photos, your choice">
      <Body>Your photo is sent through BeautyCore only when you choose Generate. On Android, Save writes the generated image to a folder you choose; Share opens your device’s sharing sheet.</Body>
      <Body muted>Consultation preferences remain local until recommendations are integrated.</Body>
    </Panel>
  </Screen>;
}
