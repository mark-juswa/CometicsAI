import { Image, Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, layout, serif, spacing, type } from '../constants/theme';
import { featureIds, type FeatureId } from '../lib/api/contracts';

// Bundled copies of the existing BeautyCore service imagery; no remote requests.
const artwork = { hairstyle: require('../assets/hair.jpg'), makeup: require('../assets/makeup.png'), nails: require('../assets/nails.jpg') };
export const serviceLabels = { hairstyle: 'Hair', makeup: 'Makeup', nails: 'Nails' };
export function ServiceCards({ selected, onSelect }: { selected?: FeatureId | null; onSelect: (id: FeatureId) => void }) {
  return <View style={styles.row}>{featureIds.map(id => <Pressable key={id} accessibilityRole="button"
    accessibilityLabel={serviceLabels[id]} accessibilityState={{ selected: selected === id }} onPress={() => onSelect(id)}
    style={({ pressed }) => [styles.card, selected === id && styles.selected, pressed && { opacity: 0.75 }]}>
    <Image source={artwork[id]} style={styles.image} accessible={false} />
    <Text style={styles.label}>{serviceLabels[id]}{selected === id ? ' ✓' : ''}</Text>
  </Pressable>)}</View>;
}
const styles = StyleSheet.create({
  row: { flexDirection: 'row', gap: spacing.sm },
  card: { flex: 1, minWidth: 0, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.card, overflow: 'hidden', borderRadius: layout.radius },
  selected: { borderColor: colors.gold, backgroundColor: colors.selected },
  image: { width: '100%', height: 88, opacity: 0.9 },
  label: { color: colors.white, fontFamily: serif, fontSize: type.body, textAlign: 'center', paddingVertical: spacing.sm, minHeight: layout.touch },
});
