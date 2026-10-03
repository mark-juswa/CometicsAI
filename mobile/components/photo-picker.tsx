import { useEffect, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { pickPhoto, recoverPhoto } from '../lib/image/picker';
import type { LocalPhoto } from '../lib/image/validation';
import { Body, Button, ErrorMessage, Loading } from './ui';
import { colors, spacing } from '../constants/theme';
import { PhotoFrame } from './workflow';

export function PhotoPicker({ photo, onChange, hand = false, disabled = false }: {
  photo: LocalPhoto | null; onChange: (photo: LocalPhoto | null) => void; hand?: boolean; disabled?: boolean;
}) {
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let mounted = true;
    void recoverPhoto().then(recovered => { if (mounted && recovered) onChange(recovered); })
      .catch(cause => { if (mounted) setError(cause instanceof Error ? cause.message : 'Please choose your photo again.'); });
    return () => { mounted = false; };
  }, [onChange]);
  async function choose() {
    setBusy(true); setError('');
    try { const selected = await pickPhoto(); if (selected) onChange(selected); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Photo selection failed. Please try again.'); }
    finally { setBusy(false); }
  }
  return <View style={styles.container}>
    {photo ? <>
      <PhotoFrame testID="photo-preview" label={hand ? 'Selected hand photo' : 'Selected portrait'} photo={photo} />
      <Body>{photo.name}</Body>
      <View style={styles.actions}>
        <View style={styles.action}><Button label="Replace" secondary disabled={disabled || busy} onPress={() => void choose()} /></View>
        <View style={styles.action}><Button label="Remove" secondary disabled={disabled || busy} onPress={() => { onChange(null); setError(''); }} /></View>
      </View>
    </> : <View style={styles.upload}>
      <Body>↑</Body>
      <Button label={hand ? 'Choose your hand photo' : 'Choose your portrait'} secondary disabled={disabled || busy} onPress={() => void choose()} />
      <Body muted>JPG or PNG, up to 8 MB. Your original stays available for comparison.</Body>
    </View>}
    {busy && <Loading label="Opening your gallery…" />}
    {error !== '' && <ErrorMessage message={error} />}
  </View>;
}
const styles = StyleSheet.create({
  container: { gap: spacing.sm },
  upload: { minHeight: 180, borderWidth: 1, borderStyle: 'dashed', borderColor: colors.border, padding: spacing.md, gap: spacing.md, justifyContent: 'center' },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  action: { flex: 1, minWidth: 100 },
});
