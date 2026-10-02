import { Image, StyleSheet } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Screen, Panel, Body, Button } from '../components/ui';
import { isFeatureId } from '../lib/api/contracts';
import { useStudio } from '../store/studio';
import { colors } from '../constants/theme';

export default function Result() {
  const params = useLocalSearchParams<{ feature?: string }>();
  const feature = isFeatureId(params.feature) ? params.feature : null;
  const draft = useStudio(state => feature ? state.drafts[feature] : null);
  const close = () => { if (router.canGoBack()) router.back(); else router.replace('/'); };
  return <Screen title="A first look" emphasis="at the flow." description="Development preview">
    {draft?.photo && draft.previewStyle ? <>
      <Body>{draft.previewStyle.name} · Mock result</Body>
      <Panel number="01" title="Original image"><Image accessibilityLabel="Original selected photo" source={{ uri: draft.photo.uri }} style={styles.photo} resizeMode="contain" /></Panel>
      <Panel number="02" title="Mock preview"><Image accessibilityLabel="Unchanged photo used as mock preview" source={{ uri: draft.photo.uri }} style={styles.photo} resizeMode="contain" /></Panel>
      <Body>This is your unchanged local photo, not an AI transformation. No image was uploaded and no generation was run.</Body>
    </> : <Panel title="No preview selected"><Body>Choose a photo and style in a service studio to see the mock comparison.</Body></Panel>}
    <Button label="Back to your studio" onPress={close} />
  </Screen>;
}
const styles = StyleSheet.create({ photo: { width: '100%', aspectRatio: 4 / 5, backgroundColor: colors.photo } });
