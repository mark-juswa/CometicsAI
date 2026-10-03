import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { colors, layout, spacing, type } from '../constants/theme';
import { Body } from './ui';

export function DirectionField({ label, value, onChange, choices, placeholder, maxLength = 80, multiline = false, disabled = false }: {
  label: string; value: string; onChange: (value: string) => void; choices?: string[];
  placeholder?: string; maxLength?: number; multiline?: boolean; disabled?: boolean;
}) {
  return <View style={styles.field}><Body>{label}</Body>
    {choices && <View style={styles.choices}>{choices.map(choice => <Pressable key={choice} accessibilityRole="button"
      accessibilityLabel={`${label}: ${choice}`} accessibilityState={{ selected: value === choice, disabled }} disabled={disabled}
      onPress={() => onChange(value === choice ? '' : choice)}
      style={({ pressed }) => [styles.chip, value === choice && styles.selected, pressed && { opacity: 0.75 }]}>
      <Text style={styles.choice}>{choice}</Text>
    </Pressable>)}</View>}
    {placeholder && <TextInput accessibilityLabel={label} value={value} onChangeText={onChange} maxLength={maxLength} editable={!disabled}
      placeholder={placeholder} placeholderTextColor={colors.muted} multiline={multiline}
      style={[styles.input, multiline && { minHeight: layout.touch * 2, textAlignVertical: 'top' }]} />}
  </View>;
}
const styles = StyleSheet.create({
  field: { gap: spacing.sm }, choices: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs },
  chip: { minHeight: layout.touch, paddingHorizontal: spacing.sm, justifyContent: 'center', backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderRadius: layout.radius },
  selected: { borderColor: colors.gold, backgroundColor: colors.selected }, choice: { color: colors.white, fontSize: type.body },
  input: { color: colors.white, fontSize: type.body, minHeight: layout.touch, padding: spacing.sm, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.card, borderRadius: layout.radius },
});
