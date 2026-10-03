import { useCallback, useEffect, useState } from 'react';
import { Alert } from 'react-native';
import { router, useFocusEffect } from 'expo-router';
import { useGeneration, isUnresolved } from '../store/generation';
import { useAuth } from '../store/auth';
import { services } from '../constants/services';
import { generationUpload } from '../lib/image/upload';
import { AuthGate } from '../components/auth-gate';
import { FlowScreen } from '../components/workflow';
import { Body, Button, ErrorMessage, Loading, Panel } from '../components/ui';

export default function Generating() { return <AuthGate><GenerationContent /></AuthGate>; }
function GenerationContent() {
  const job = useGeneration(state => state.job);
  const [clock, setClock] = useState(() => Date.now());
  const back = useCallback(() => router.dismissTo('/'), []);
  useEffect(() => {
    const timer = setInterval(() => setClock(Date.now()), 1000); return () => clearInterval(timer);
  }, []);
  useFocusEffect(useCallback(() => {
    if (job?.phase === 'completed') router.replace({ pathname: '/result', params: { feature: job.feature } });
  }, [job]));
  function retry() {
    if (!job || job.phase !== 'failed') return;
    const user = useAuth.getState().user;
    if (!user || user.id !== job.userId) return;
    void useGeneration.getState().run(job.feature, job.original, job.style, user.id, () => generationUpload(job.original, job.style.id));
  }
  function acknowledge() {
    Alert.alert('Confirm processing has ended', 'Ask the operator to verify that the earlier request has finished or failed. A new request spends GPU work and cannot recover a lost result. Do not confirm while processing may still be active.', [
      { text: 'Keep waiting', style: 'cancel' },
      { text: 'Operator confirmed it ended', onPress: () => useGeneration.getState().acknowledgeEnded() },
    ]);
  }
  const elapsed = job ? Math.max(0, Math.floor(((job.endedAt ?? clock) - job.startedAt) / 1000)) : 0;
  const ongoing = job?.phase === 'preparing' || job?.phase === 'running';
  return <FlowScreen title={ongoing ? 'Creating your look.' : job?.phase === 'uncertain' ? 'Your request needs a check.' : 'Let’s find your next look.'}
    detail={job ? `${services[job.feature].label} · ${job.style.name}` : 'Choose a service and style to start.'} onBack={back}
    actions={job ? <>
      {ongoing && <Button label="Keep browsing" secondary onPress={back} />}
      {job.phase === 'uncertain' && <Button label="Operator confirmed processing ended" secondary onPress={acknowledge} />}
      {job.phase === 'failed' && <><Button label="Retry generation" onPress={retry} /><Button label="Back to Review" secondary onPress={() => router.dismissTo(services[job.feature].route)} /></>}
      {job.phase === 'completed' && <Button label="View result" onPress={() => router.replace({ pathname: '/result', params: { feature: job.feature } })} />}
    </> : <Button label="Choose your studio" onPress={back} />}>
    {job && <Panel title={job.style.name}>
      <Body>{elapsed < 60 ? `${elapsed}s elapsed` : `${Math.floor(elapsed / 60)}m ${elapsed % 60}s elapsed`}</Body>
      {ongoing && <><Loading label={job.phase === 'preparing' ? 'Preparing your photo…' : 'Your look is processing…'} />
        <Body>This may take several minutes, especially for Nails. You can keep browsing; another generation is blocked until this one ends.</Body>
        <Body muted>Elapsed time reflects waiting, not a predicted completion percentage.</Body></>}
      {job.error && <ErrorMessage message={job.error} />}
      {job.phase === 'uncertain' && <><Body>We could not confirm the outcome. Your request may still be running. No automatic retry was made.</Body>
        <Body muted>The service has no manual-generation status lookup. Ask the operator to confirm processing has ended before enabling a new request.</Body></>}
      {job.phase === 'failed' && <Body>You can correct the photo/style in Review, or explicitly try again. No request will restart by itself.</Body>}
      {isUnresolved(job) && <Body muted>Your original photo and selected style are preserved.</Body>}
    </Panel>}
  </FlowScreen>;
}
