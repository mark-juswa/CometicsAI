import { useCallback, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Panel, Body, Button } from '../components/ui';
import { FlowScreen, leaveFlow, PhotoFrame } from '../components/workflow';
import { isFeatureId } from '../lib/api/contracts';
import { useStudio } from '../store/studio';
import { services } from '../constants/services';
import { spacing } from '../constants/theme';

export default function Result() {
  const params = useLocalSearchParams<{ feature?: string }>();
  const feature = isFeatureId(params.feature) ? params.feature : null;
  const draft = useStudio(state => feature ? state.drafts[feature] : null);
  const [view, setView] = useState<'original' | 'result'>('result');
  const returnToStudio = useCallback(() => {
    if (!feature) { leaveFlow(); return; }
    router.dismissTo(services[feature].route);
  }, [feature]);
  function tryAnother() {
    if (!feature) return;
    useStudio.getState().tryAnother(feature); returnToStudio();
  }
  function startOver() {
    if (!feature) return;
    useStudio.getState().reset(feature); returnToStudio();
  }
  const valid = draft?.photo && draft.previewStyle;
  return <FlowScreen title="Your look, in focus." detail={valid ? draft.previewStyle?.name : 'Your studio preview'} onBack={returnToStudio}
    actions={valid ? <><Button label="Try Another Style" onPress={tryAnother} /><Button label="Start Over" secondary onPress={startOver} /></> : <Button label="Choose a service" onPress={() => router.replace('/')} />}>
    {valid && draft.photo && draft.previewStyle ? <>
      <View style={styles.row}>
        <View style={styles.flex}><Button label="Original" selected={view === 'original'} secondary={view !== 'original'} onPress={() => setView('original')} /></View>
        <View style={styles.flex}><Button label="Result" selected={view === 'result'} secondary={view !== 'result'} onPress={() => setView('result')} /></View>
      </View>
      <PhotoFrame photo={draft.photo} label={view === 'original' ? 'Original selected photo' : 'Unchanged mock result photo'} />
      <Body>Mock preview · {view === 'original' ? 'Original' : 'Result'}</Body>
      <Body muted>This is your unchanged local photo. No AI transformation or image upload was performed.</Body>
      <Panel title={draft.previewStyle.name} detail={draft.previewStyle.description}>
        <View style={styles.row}>
          <View style={styles.flex}><Button label="Save" secondary disabled onPress={() => {}} /></View>
          <View style={styles.flex}><Button label="Share" secondary disabled onPress={() => {}} /></View>
        </View>
        <Body muted>Save and Share will be available with generated results.</Body>
      </Panel>
    </> : <Panel title="Your next look starts here"><Body>Choose a photo and style in a Custom Studio to create a preview.</Body></Panel>}
  </FlowScreen>;
}
const styles = StyleSheet.create({ row: { flexDirection: 'row', gap: spacing.sm }, flex: { flex: 1, minWidth: 0 } });
