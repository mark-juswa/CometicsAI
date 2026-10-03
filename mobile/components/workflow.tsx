import { useCallback } from 'react';
import type { ReactNode } from 'react';
import { BackHandler, Image, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, Stack, useFocusEffect } from 'expo-router';
import { colors, compactType, layout, serif, spacing, type } from '../constants/theme';
import type { LocalPhoto } from '../lib/image/validation';
import { Body } from './ui';

export function HeaderAction({ label, glyph, onPress }: { label: string; glyph: string; onPress: () => void }) {
  return <Pressable accessibilityRole="button" accessibilityLabel={label} onPress={onPress}
    style={({ pressed }) => [styles.headerAction, pressed && { opacity: 0.75 }]}>
    <Text style={styles.glyph}>{glyph}</Text>
  </Pressable>;
}
export function leaveFlow() { if (router.canGoBack()) router.back(); else router.replace('/'); }

// Only the focused wizard consumes Android Back. Opening Settings/result never
// leaves a hidden screen's handler active. Returning from them keeps the draft.
export function FlowScreen({ steps, step, onBack, title, detail, eyebrow, consultation = false, children, actions }: {
  steps?: readonly string[]; step?: number; onBack?: () => void; title: string;
  detail?: string; eyebrow?: string; consultation?: boolean; children: ReactNode; actions: ReactNode;
}) {
  const back = onBack ?? leaveFlow;
  useFocusEffect(useCallback(() => {
    const subscription = BackHandler.addEventListener('hardwareBackPress', () => { back(); return true; });
    return () => subscription.remove();
  }, [back]));
  return <SafeAreaView style={styles.screen} edges={['left', 'right', 'bottom']}>
    <Stack.Screen options={{ headerBackVisible: false, gestureEnabled: false,
      headerLeft: () => <HeaderAction label="Back" glyph="‹" onPress={back} /> }} />
    <KeyboardAvoidingView style={styles.screen} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      {steps && step !== undefined && <View style={[styles.progress, consultation && styles.consultProgress]} accessibilityLabel={`Step ${step + 1} of ${steps.length}: ${steps[step]}`}>
        {steps.map((label, index) => <View key={label} style={[styles.progressItem, consultation && styles.consultProgressItem,
          index === step && (consultation ? styles.consultProgressActive : styles.progressActive)]}>
          {consultation ? <><Text style={[styles.consultNumber, index < step && styles.consultComplete]}>{index < step ? '✓' : `0${index + 1}`}</Text>
            <Text numberOfLines={1} style={[styles.consultLabel, index === step && { color: colors.white }, index < step && { color: colors.goldLight }]}>{label}</Text></> :
            <Text style={[styles.progressText, index === step && { color: colors.goldLight }]}>{index < step ? '✓' : `0${index + 1}`}  {label}</Text>}
        </View>)}
      </View>}
      <ScrollView key={step} style={styles.scroll} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.intro}>{eyebrow && <Text style={styles.eyebrow}>{eyebrow}</Text>}
          <Text accessibilityRole="header" style={styles.title}>{title}</Text>{detail && <Body>{detail}</Body>}</View>
        {children}
      </ScrollView>
      <View style={styles.actionBorder}><View style={styles.actions}>{actions}</View></View>
    </KeyboardAvoidingView>
  </SafeAreaView>;
}

export function PhotoFrame({ photo, label, testID }: { photo: LocalPhoto; label: string; testID?: string }) {
  const { height } = useWindowDimensions();
  return <Image testID={testID} accessibilityLabel={label} source={{ uri: photo.uri }} resizeMode="contain"
    style={[styles.photo, { height: Math.min(layout.previewMax, Math.max(layout.previewMin, height * 0.3)) }]} />;
}
const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.deep }, scroll: { flex: 1 },
  content: { padding: spacing.md, paddingBottom: spacing.lg, gap: spacing.md, width: '100%', maxWidth: layout.maxWidth, alignSelf: 'center' },
  intro: { gap: spacing.xs }, title: { fontFamily: serif, fontSize: compactType.heading, lineHeight: compactType.headingLine, color: colors.white },
  progress: { flexDirection: 'row', gap: spacing.xs, padding: spacing.md, paddingBottom: spacing.sm, maxWidth: layout.maxWidth, width: '100%', alignSelf: 'center' },
  progressItem: { flex: 1, borderBottomWidth: 2, borderColor: colors.border, paddingBottom: spacing.sm, minWidth: 0 },
  progressActive: { borderColor: colors.gold }, progressText: { color: colors.muted, fontSize: type.small, fontWeight: '700', flexShrink: 1 },
  consultProgress: { marginHorizontal: spacing.md, marginTop: spacing.xs, marginBottom: spacing.sm, padding: 4,
    borderWidth: 1, borderColor: colors.border, borderRadius: 15, backgroundColor: colors.card, width: undefined },
  consultProgressItem: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 5, minHeight: 42,
    paddingHorizontal: 4, paddingBottom: 0, borderBottomWidth: 0, borderRadius: 11 },
  consultProgressActive: { backgroundColor: colors.selected, borderWidth: 1, borderColor: colors.border },
  consultNumber: { color: colors.secondary, borderWidth: 1, borderColor: colors.border, borderRadius: 20, width: 23, height: 23,
    textAlign: 'center', textAlignVertical: 'center', fontSize: 9 },
  consultComplete: { color: colors.goldLight, borderColor: colors.gold },
  consultLabel: { color: colors.muted, fontSize: 10, fontWeight: '700', flexShrink: 1 },
  eyebrow: { color: colors.gold, fontSize: type.small, fontWeight: '800', letterSpacing: 1.5 },
  actionBorder: { backgroundColor: colors.card, borderTopWidth: 1, borderColor: colors.border },
  actions: { padding: spacing.md, gap: spacing.sm, maxWidth: layout.maxWidth, width: '100%', alignSelf: 'center' },
  headerAction: { minWidth: layout.touch, minHeight: layout.touch, justifyContent: 'center', alignItems: 'center' },
  glyph: { color: colors.goldLight, fontSize: compactType.glyph },
  photo: { width: '100%', backgroundColor: colors.photo, borderRadius: layout.radius },
});
