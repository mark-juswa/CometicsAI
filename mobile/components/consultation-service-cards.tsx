import { Pressable, StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, layout, serif, spacing, type } from '../constants/theme';
import { featureIds, type FeatureId } from '../lib/api/contracts';

const services = {
  hairstyle: { name: 'Hairstyle', detail: 'A cut or shape for your next look', glyph: '✦', colors: ['#311646', '#5d365f'] as const },
  makeup: { name: 'Makeup', detail: 'A finish for your portrait', glyph: '◐', colors: ['#472746', '#7d4668'] as const },
  nails: { name: 'Nails', detail: 'A polished hand look', glyph: '◇', colors: ['#292042', '#674c6e'] as const },
};

export function ConsultationServiceCards({ selected, onSelect, disabled = false }: {
  selected: FeatureId | null; onSelect: (feature: FeatureId) => void; disabled?: boolean;
}) {
  return <View style={styles.list}>{featureIds.map((id, index) => {
    const service = services[id];
    return <Pressable key={id} accessibilityRole="button" accessibilityLabel={service.name}
      accessibilityState={{ selected: selected === id, disabled }} disabled={disabled} onPress={() => onSelect(id)}
      style={({ pressed }) => [styles.card, selected === id && styles.selected, pressed && { opacity: 0.78 }]}>
      <LinearGradient colors={service.colors} style={styles.art}><Text style={styles.glyph}>{service.glyph}</Text></LinearGradient>
      <View style={styles.copy}><Text style={styles.kicker}>0{index + 1} / BEAUTY SERVICE</Text>
        <Text style={styles.name}>{service.name}</Text><Text style={styles.detail}>{service.detail}</Text></View>
      <Text style={styles.arrow} accessibilityElementsHidden>↗</Text>
    </Pressable>;
  })}</View>;
}

const styles = StyleSheet.create({
  list: { gap: spacing.sm },
  card: { flexDirection: 'row', alignItems: 'center', minHeight: 106, minWidth: 0, borderWidth: 1,
    borderColor: colors.border, borderRadius: layout.radius, overflow: 'hidden', backgroundColor: colors.card },
  selected: { borderColor: colors.gold, backgroundColor: colors.selected },
  art: { width: 92, alignSelf: 'stretch', alignItems: 'center', justifyContent: 'center' },
  glyph: { color: colors.goldLight, fontFamily: serif, fontSize: 55, fontStyle: 'italic' },
  copy: { flex: 1, minWidth: 0, gap: 3, paddingVertical: spacing.sm, paddingHorizontal: spacing.md },
  kicker: { color: colors.gold, fontSize: 9, fontWeight: '800', letterSpacing: 1 },
  name: { color: colors.white, fontFamily: serif, fontSize: 22 },
  detail: { color: colors.secondary, fontSize: type.small, lineHeight: 17 },
  arrow: { color: colors.goldLight, fontSize: 17, paddingRight: spacing.sm },
});
