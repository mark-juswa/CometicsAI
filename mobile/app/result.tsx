import { useCallback, useState } from 'react';
import { Linking, StyleSheet, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Panel, Body, Button, ErrorMessage } from '../components/ui';
import { FlowScreen, leaveFlow, PhotoFrame } from '../components/workflow';
import { AuthGate } from '../components/auth-gate';
import { isFeatureId } from '../lib/api/contracts';
import { useStudio } from '../store/studio';
import { useGeneration } from '../store/generation';
import { useAuth } from '../store/auth';
import { saveResult, shareResult, PhotoPermissionError } from '../lib/image/result-actions';
import { services } from '../constants/services';
import { spacing } from '../constants/theme';

export default function Result() { return <AuthGate><ResultContent /></AuthGate>; }
function ResultContent() {
  const params = useLocalSearchParams<{ feature?: string }>();
  const feature = isFeatureId(params.feature) ? params.feature : null;
  const job = useGeneration(state => state.job);
  const user = useAuth(state => state.user);
  const [view, setView] = useState<'original' | 'result'>('result');
  const [busy, setBusy] = useState(false); const [message, setMessage] = useState('');
  const [error, setError] = useState(''); const [settings, setSettings] = useState(false);
  const valid = job?.phase === 'completed' && job.feature === feature && job.userId === user?.id && job.result;
  const returnToStudio = useCallback(() => {
    if (!feature) { leaveFlow(); return; }
    router.dismissTo(services[feature].route);
  }, [feature]);
  function tryAnother() {
    if (!feature || busy) return;
    useStudio.getState().tryAnother(feature); useGeneration.getState().clear(); returnToStudio();
  }
  function startOver() {
    if (!feature || busy) return;
    useStudio.getState().reset(feature); useGeneration.getState().clear(); returnToStudio();
  }
  async function resultAction(kind: 'save' | 'share') {
    if (!job?.result || busy) return;
    setBusy(true); setMessage(''); setError(''); setSettings(false);
    try {
      if (kind === 'save') { const saved = await saveResult(job.result); setMessage(saved ? 'Saved your generated image.' : 'Save cancelled. Your result is still available.'); }
      else { await shareResult(job.result); setMessage('Sharing sheet closed. Your result is still available.'); }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'This action could not be completed. Your result is still available.');
      setSettings(cause instanceof PhotoPermissionError && !cause.canAskAgain);
    } finally { setBusy(false); }
  }
  const elapsed = job?.endedAt ? ((job.endedAt - job.startedAt) / 1000).toFixed(1) : '';
  return <FlowScreen title="Your look, in focus." detail={valid ? job.style.name : 'Your studio result'} onBack={returnToStudio}
    actions={valid ? <><Button label="Try Another Style" disabled={busy} onPress={tryAnother} /><Button label="Start Over" secondary disabled={busy} onPress={startOver} /></> : <Button label="Choose a service" onPress={() => router.replace('/')} />}>
    {valid && job.result ? <>
      <View style={styles.row}>
        <View style={styles.flex}><Button label="Original" selected={view === 'original'} secondary={view !== 'original'} onPress={() => setView('original')} /></View>
        <View style={styles.flex}><Button label="Generated Result" selected={view === 'result'} secondary={view !== 'result'} onPress={() => setView('result')} /></View>
      </View>
      <PhotoFrame photo={view === 'original' ? job.original : { ...job.original, uri: job.result.image.data_url }} label={view === 'original' ? 'Original selected photo' : 'Generated beauty result'} />
      <Body>{view === 'original' ? 'Your original photo' : 'Your generated result'} · {elapsed}s</Body>
      <Panel title={job.style.name} detail={job.style.description}>
        <View style={styles.row}>
          <View style={styles.flex}><Button label={busy ? 'Please wait…' : 'Save'} secondary disabled={busy} onPress={() => void resultAction('save')} /></View>
          <View style={styles.flex}><Button label="Share" secondary disabled={busy} onPress={() => void resultAction('share')} /></View>
        </View>
        {message !== '' && <Body>{message}</Body>}
        {error !== '' && <ErrorMessage message={error} />}
        {settings && <Button label="Open photo permission settings" secondary onPress={() => void Linking.openSettings()} />}
        <Body muted>Save and Share use the generated image. Your original stays available for comparison.</Body>
      </Panel>
    </> : <Panel title="Your next look starts here"><Body>Choose a photo and style in a Custom Studio to generate your look.</Body></Panel>}
  </FlowScreen>;
}
const styles = StyleSheet.create({ row: { flexDirection: 'row', gap: spacing.sm }, flex: { flex: 1, minWidth: 0 } });
