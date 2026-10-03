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
export function FlowScreen({ steps, step, onBack, title, detail, children, actions }: {
  steps?: readonly string[]; step?: number; onBack?: () => void; title: string;
  detail?: string; children: ReactNode; actions: ReactNode;
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
      {steps && step !== undefined && <View style={styles.progress} accessibilityLabel={`Step ${step + 1} of ${steps.length}: ${steps[step]}`}>
        {steps.map((label, index) => <View key={label} style={[styles.progressItem, index === step && styles.progressActive]}>
          <Text style={[styles.progressText, index === step && { color: colors.goldLight }]}>{index < step ? '✓' : `0${index + 1}`}  {label}</Text>
        </View>)}
      </View>}
      <ScrollView key={step} style={styles.scroll} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.intro}><Text accessibilityRole="header" style={styles.title}>{title}</Text>{detail && <Body>{detail}</Body>}</View>
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
  actionBorder: { backgroundColor: colors.card, borderTopWidth: 1, borderColor: colors.border },
  actions: { padding: spacing.md, gap: spacing.sm, maxWidth: layout.maxWidth, width: '100%', alignSelf: 'center' },
  headerAction: { minWidth: layout.touch, minHeight: layout.touch, justifyContent: 'center', alignItems: 'center' },
  glyph: { color: colors.goldLight, fontSize: compactType.glyph },
  photo: { width: '100%', backgroundColor: colors.photo, borderRadius: layout.radius },
});
