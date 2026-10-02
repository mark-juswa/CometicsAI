import type { ReactNode } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, serif, spacing, type } from '../constants/theme';

export function Body({ children, muted = false }: { children: ReactNode; muted?: boolean }) {
  return <Text style={[styles.body, muted && { color: colors.muted }]}>{children}</Text>;
}
export function Title({ children }: { children: ReactNode }) {
  return <Text accessibilityRole="header" style={styles.title}>{children}</Text>;
}
export function Button({ label, onPress, secondary = false, disabled = false, testID }: {
  label: string; onPress: () => void; secondary?: boolean; disabled?: boolean; testID?: string;
}) {
  return <Pressable testID={testID} accessibilityRole="button" accessibilityState={{ disabled }} disabled={disabled} onPress={onPress}
    style={({ pressed }) => [styles.button, secondary && styles.secondary, disabled && { opacity: 0.47 }, pressed && { opacity: 0.75 }]}>
    <Text style={[styles.buttonText, secondary && { color: colors.white }]}>{label}</Text>
  </Pressable>;
}
export function ErrorMessage({ message, retry }: { message: string; retry?: () => void }) {
  return <View style={styles.error} accessibilityRole="alert" accessibilityLiveRegion="polite">
    <Text style={[styles.body, { color: colors.error }]}>{message}</Text>
    {retry && <Button label="Retry connection" secondary onPress={retry} />}
  </View>;
}
export function Loading({ label }: { label: string }) {
  return <View style={styles.loading} accessibilityLiveRegion="polite"><ActivityIndicator color={colors.gold} /><Body>{label}</Body></View>;
}
export function Panel({ number, title, detail, children }: { number?: string; title: string; detail?: string; children: ReactNode }) {
  return <LinearGradient colors={[colors.surface, colors.card]} style={styles.panel}>
    <View style={styles.panelHeader}>
      {number && <Text style={styles.number}>{number}</Text>}
      <View style={styles.flex}><Title>{title}</Title>{detail && <Body muted>{detail}</Body>}</View>
    </View>{children}
  </LinearGradient>;
}
export function Screen({ children, title, emphasis, description }: { children: ReactNode; title: string; emphasis?: string; description?: string }) {
  return <SafeAreaView style={styles.screen} edges={['left', 'right', 'bottom']}>
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <View style={styles.hero}>
        <Text style={styles.eyebrow}>THE AI BEAUTY STUDIO</Text>
        <Text accessibilityRole="header" style={styles.heroTitle}>{title}{emphasis && <Text style={styles.emphasis}>{'\n'}{emphasis}</Text>}</Text>
        {description && <Body>{description}</Body>}
      </View>
      {children}
      <View style={styles.footer}><Text style={styles.eyebrow}>ANDREA’S ✦ AI STUDIO</Text><Body muted>Explore a look that feels like you.</Body></View>
    </ScrollView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.deep },
  content: { padding: spacing.md, gap: spacing.lg, width: '100%', maxWidth: 720, alignSelf: 'center' },
  hero: { gap: spacing.md, paddingVertical: spacing.lg },
  eyebrow: { color: colors.gold, fontSize: type.small, letterSpacing: 2, fontWeight: '700' },
  heroTitle: { fontFamily: serif, color: colors.white, fontSize: type.hero, lineHeight: 46 },
  emphasis: { color: colors.goldLight, fontStyle: 'italic' },
  body: { color: colors.secondary, fontSize: type.body, lineHeight: 23, flexShrink: 1 },
  title: { fontFamily: serif, fontSize: type.panel, color: colors.white, marginBottom: spacing.xs },
  button: { minHeight: 48, borderWidth: 1, borderColor: colors.gold, backgroundColor: colors.gold, paddingVertical: spacing.sm, paddingHorizontal: spacing.md, alignItems: 'center', justifyContent: 'center' },
  secondary: { backgroundColor: colors.surface, borderColor: colors.border },
  buttonText: { color: colors.ink, fontWeight: '800', fontSize: type.button, textAlign: 'center', flexShrink: 1 },
  panel: { padding: spacing.md, borderWidth: 1, borderColor: colors.border, gap: spacing.md },
  panelHeader: { flexDirection: 'row', gap: spacing.sm, alignItems: 'flex-start' },
  number: { color: colors.gold, borderColor: colors.gold, borderWidth: 1, padding: spacing.xs, fontSize: type.small },
  flex: { flex: 1, minWidth: 0 },
  error: { backgroundColor: colors.errorSurface, borderWidth: 1, borderColor: colors.error, padding: spacing.md, gap: spacing.sm },
  loading: { padding: spacing.md, gap: spacing.sm, alignItems: 'center' },
  footer: { paddingVertical: spacing.lg, gap: spacing.sm, borderTopWidth: 1, borderColor: colors.border },
});
