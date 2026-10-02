import { useEffect, useState } from 'react';
import { Image, StyleSheet, View } from 'react-native';
import { pickPhoto, recoverPhoto } from '../lib/image/picker';
import type { LocalPhoto } from '../lib/image/validation';
import { Body, Button, ErrorMessage, Loading } from './ui';
import { colors, spacing } from '../constants/theme';

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
      <Image testID="photo-preview" accessibilityLabel={hand ? 'Selected hand photo' : 'Selected portrait'} source={{ uri: photo.uri }} style={styles.photo} resizeMode="contain" />
      <Body>{photo.name}</Body><Body muted>{(photo.size / 1024 / 1024).toFixed(2)} MB · {photo.width} × {photo.height}</Body>
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
  photo: { width: '100%', aspectRatio: 4 / 5, backgroundColor: colors.photo },
  upload: { minHeight: 240, borderWidth: 1, borderStyle: 'dashed', borderColor: colors.border, padding: spacing.lg, gap: spacing.md, justifyContent: 'center' },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  action: { flex: 1, minWidth: 100 },
});
