import { useCallback, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { AuthGate } from '../components/auth-gate';
import { Body, Button, ErrorMessage, Panel } from '../components/ui';
import { FlowScreen, PhotoFrame } from '../components/workflow';
import { useConsultationSession } from '../store/consultation-session';
import { useConsultation } from '../store/consultation';
import { useAuth } from '../store/auth';
import { spacing } from '../constants/theme';

export default function ConsultationResult() { return <AuthGate><ResultContent /></AuthGate>; }
function ResultContent() {
  const { recommendation: id } = useLocalSearchParams<{ recommendation?: string }>();
  const session = useConsultationSession(); const user = useAuth(s => s.user);
  const [view, setView] = useState<'original' | 'result'>('result');
  const recommendation = session.state?.recommendations?.recommendations.find(r => r.id === id);
  const detail = id ? session.details[id] : null;
  const result = detail?.generation.status === 'completed' ? detail.result : null;
  const valid = session.userId === user?.id && recommendation && result && session.original;
  const selected = id && session.state?.selected_recommendation_id === id;
  const back = useCallback(() => { useConsultation.getState().goToStep(2); router.dismissTo('/consultation'); }, []);
  const timing = id ? session.times[id] : null;
  return <FlowScreen title="Your look, in focus." detail={valid ? recommendation.primary.style_name : 'Your consultation result'} onBack={back}
    actions={valid ? <Button label={selected ? 'This Look is selected ✓' : session.busy ? 'Confirming your selection…' : 'Select This Look'}
      disabled={session.busy || Boolean(session.active) || Boolean(selected) || session.expired} onPress={() => { if (id) void session.select(id); }} /> :
      <Button label="Back to Consultation" onPress={back} />}>
    {session.error !== '' && <ErrorMessage message={session.error} />}
    {valid ? <>
      <View style={styles.row}><View style={styles.flex}><Button label="Original" selected={view === 'original'} secondary={view !== 'original'} onPress={() => setView('original')} /></View>
        <View style={styles.flex}><Button label="Generated Result" selected={view === 'result'} secondary={view !== 'result'} onPress={() => setView('result')} /></View></View>
      <PhotoFrame photo={view === 'original' ? session.original! : { ...session.original!, uri: result.image.data_url }} label={view === 'original' ? 'Original consultation photo' : 'Generated recommended result'} />
      {timing?.end && <Body>{((timing.end - timing.start) / 1000).toFixed(1)}s elapsed</Body>}
      <Panel title={recommendation.primary.style_name} detail={recommendation.reason}>
        <Body>{selected ? 'Your selection is confirmed by BeautyCore.' : 'Select this completed look to record it in your consultation.'}</Body>
        <Body muted>This selection is a consultation summary. It does not create a booking or payment.</Body>
      </Panel>
    </> : <Panel title="Your result is unavailable"><Body>Return to your consultation to view or generate one of your recommended looks.</Body></Panel>}
  </FlowScreen>;
}
const styles = StyleSheet.create({ row: { flexDirection: 'row', gap: spacing.sm }, flex: { flex: 1, minWidth: 0 } });
