import { useEffect, useState } from 'react';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';
import { pickPhoto, recoverPhoto } from '../lib/image/picker';
import type { LocalPhoto } from '../lib/image/validation';
import { Body, Button, ErrorMessage, Loading } from './ui';
import { colors, layout, serif, spacing, type } from '../constants/theme';
import { PhotoFrame } from './workflow';

export function PhotoPicker({ photo, onChange, hand = false, disabled = false, compact = false }: {
  photo: LocalPhoto | null; onChange: (photo: LocalPhoto | null) => void; hand?: boolean; disabled?: boolean; compact?: boolean;
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
    {compact ? photo ? <View style={styles.compactPhoto}>
      <Image testID="photo-preview" accessibilityLabel={hand ? 'Selected hand photo' : 'Selected portrait'} source={{ uri: photo.uri }} style={styles.thumbnail} />
      <View style={styles.compactDetails}><Text style={styles.compactTitle}>{hand ? 'Your hand photo' : 'Your portrait'} ✓</Text>
        <Text style={styles.compactFilename} numberOfLines={1}>{photo.name}</Text>
        <View style={styles.textActions}>
          <Pressable accessibilityRole="button" accessibilityLabel="Change photo" disabled={disabled || busy} onPress={() => void choose()} style={styles.textTouch}>
            <Text style={styles.textAction}>Change photo</Text></Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel="Remove photo" disabled={disabled || busy} onPress={() => { onChange(null); setError(''); }} style={styles.textTouch}>
            <Text style={styles.removeAction}>Remove</Text></Pressable>
        </View>
      </View>
    </View> : <Pressable accessibilityRole="button" accessibilityLabel={hand ? 'Choose your hand photo' : 'Choose your portrait'}
      disabled={disabled || busy} onPress={() => void choose()} style={({ pressed }) => [styles.compactUpload, pressed && { opacity: 0.75 }]}>
      <Text style={styles.uploadGlyph}>↑</Text><Text style={styles.compactTitle}>Bring your photo in</Text>
      <Text style={styles.filename}>Choose a JPG or PNG, up to 8 MB.</Text>
    </Pressable> : photo ? <>
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
  compactUpload: { minHeight: 124, borderWidth: 1, borderStyle: 'dashed', borderColor: colors.border,
    borderRadius: layout.radius, backgroundColor: colors.card, alignItems: 'center', justifyContent: 'center', gap: spacing.xs, padding: spacing.md },
  uploadGlyph: { color: colors.gold, fontSize: 35, lineHeight: 42 },
  compactPhoto: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, backgroundColor: colors.card,
    borderWidth: 1, borderColor: colors.border, borderRadius: layout.radius, padding: spacing.sm, minWidth: 0 },
  thumbnail: { width: 76, height: 88, borderRadius: 8, backgroundColor: colors.photo },
  compactDetails: { flex: 1, minWidth: 0, gap: spacing.xs },
  compactTitle: { color: colors.white, fontFamily: serif, fontSize: 20 },
  filename: { color: colors.muted, fontSize: type.small, lineHeight: 18, textAlign: 'center' },
  compactFilename: { color: colors.muted, fontSize: type.small, lineHeight: 18 },
  textActions: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', columnGap: spacing.sm },
  textTouch: { minHeight: layout.touch, justifyContent: 'center' },
  textAction: { color: colors.goldLight, fontSize: type.small, fontWeight: '700' },
  removeAction: { color: colors.muted, fontSize: type.small },
});
