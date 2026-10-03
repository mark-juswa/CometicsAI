import { router } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Screen, Body, Button, Title } from '../components/ui';
import { ServiceCards } from '../components/service-cards';
import { services } from '../constants/services';
import { colors, compactType, layout, serif, spacing, type } from '../constants/theme';
import { AuthGate } from '../components/auth-gate';
import { useGeneration, isUnresolved } from '../store/generation';
import { useConsultationSession } from '../store/consultation-session';

export default function Home() {
  const job = useGeneration(state => state.job);
  const consultation = useConsultationSession(state => state.handle);
  return <AuthGate><Screen compact title="A look that" emphasis="feels like you." description="ANDREA’S AESTHETIC & WELLNESS CLINIC">
    {job && <Button label={isUnresolved(job) ? 'View current generation' : 'View latest generation'} secondary onPress={() => router.push('/generating')} />}
    <LinearGradient colors={[colors.surface, colors.card]} style={styles.consultation}>
      <View style={styles.top}><Text style={styles.eyebrow}>YOUR BEAUTY, YOUR DIRECTION</Text><Text style={styles.mark} accessible={false}>✦</Text></View>
      <Text accessibilityRole="header" style={styles.title}>AI Beauty Consultation</Text>
      <Body>A little guidance for your next look. Choose your service, share your direction, and make it personal.</Body>
      <Text style={styles.journey}>Service   →   Direction   →   Your Looks</Text>
      <Button label={consultation ? 'Continue Consultation ✦' : 'Start Consultation ✦'} onPress={() => router.push('/consultation')} />
    </LinearGradient>
    <View style={styles.custom}><Title>Custom Services</Title><Body muted>Have a look in mind? Head straight to your studio.</Body>
      <ServiceCards onSelect={id => router.push(services[id].route)} />
    </View>
  </Screen></AuthGate>;
}
const styles = StyleSheet.create({
  consultation: { padding: spacing.lg, gap: spacing.md, borderWidth: 1, borderColor: colors.gold, borderRadius: layout.radius },
  top: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  eyebrow: { color: colors.goldLight, fontSize: type.small, fontWeight: '700', flex: 1, letterSpacing: 1 },
  mark: { color: colors.goldLight, fontSize: compactType.glyph },
  title: { color: colors.white, fontFamily: serif, fontSize: compactType.heading, lineHeight: compactType.headingLine },
  journey: { color: colors.muted, fontSize: type.small }, custom: { gap: spacing.sm },
});
