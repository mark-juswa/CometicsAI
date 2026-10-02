import { LinearGradient } from 'expo-linear-gradient';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import type { Style } from '../lib/api/contracts';
import { nailSwatches } from '../features/nails/presentation';
import { colors, serif, spacing, type } from '../constants/theme';
import { Body } from './ui';

export function StyleCatalog({ styles, selectedId, onSelect, nails = false, disabled = false }: {
  styles: Style[]; selectedId: string | null; onSelect: (id: string) => void; nails?: boolean; disabled?: boolean;
}) {
  if (!styles.length) return <Body>No styles are available from this API. Check the backend catalog configuration.</Body>;
  return <View style={sheet.catalog}>{styles.map((style, index) => <Pressable key={style.id}
    accessibilityRole="button" accessibilityLabel={`${style.name}. ${style.description}`}
    accessibilityState={{ selected: selectedId === style.id, disabled }} disabled={disabled} onPress={() => onSelect(style.id)}
    style={({ pressed }) => [sheet.card, selectedId === style.id && sheet.selected, pressed && { opacity: 0.75 }]}>
    {nails ? <View style={[sheet.swatch, { backgroundColor: nailSwatches[style.id] ?? colors.muted }]} /> :
      <LinearGradient colors={[colors.surface, colors.tones[index % colors.tones.length]]} style={sheet.art}>
        <Text style={sheet.monogram}>{style.name.charAt(0)}</Text>
      </LinearGradient>}
    <View style={sheet.copy}><Text style={sheet.name}>{style.name}{selectedId === style.id ? ' ✓' : ''}</Text>
      <Body muted>{style.description}</Body><Text style={sheet.status}>{style.status.replaceAll('_', ' ')}</Text></View>
  </Pressable>)}</View>;
}
const sheet = StyleSheet.create({
  catalog: { gap: spacing.sm },
  card: { flexDirection: 'row', gap: spacing.sm, alignItems: 'center', borderWidth: 1, borderColor: colors.border, backgroundColor: colors.deep, padding: spacing.sm, minHeight: 88 },
  selected: { borderColor: colors.gold, backgroundColor: colors.selected },
  art: { width: 56, height: 70, justifyContent: 'flex-end', padding: spacing.xs },
  monogram: { fontSize: type.hero, fontFamily: serif, fontStyle: 'italic', color: colors.white },
  swatch: { width: 44, height: 44, borderRadius: 22, borderWidth: 2, borderColor: colors.secondary },
  copy: { flex: 1, minWidth: 0, gap: spacing.xs },
  name: { fontSize: type.body, fontWeight: '700', color: colors.white },
  status: { color: colors.gold, fontSize: type.small },
});
