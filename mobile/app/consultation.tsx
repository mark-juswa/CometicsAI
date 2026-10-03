import { useCallback, useState } from 'react';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { Body, Button, ErrorMessage, Loading } from '../components/ui';
import { FlowScreen, leaveFlow, PhotoFrame } from '../components/workflow';
import { ConsultationServiceCards } from '../components/consultation-service-cards';
import { PhotoPicker } from '../components/photo-picker';
import { DirectionField } from '../components/direction-field';
import { consultationStages } from '../features/consultation/overview';
import { occasions, vibes, preferenceOptions, consultationPreferences } from '../features/consultation/direction';
import { useConsultationStatus } from '../features/consultation/use-status';
import { services } from '../constants/services';
import { colors, layout, serif, spacing, type } from '../constants/theme';
import { useConsultation } from '../store/consultation';
import { useConsultationSession } from '../store/consultation-session';
import { useAiOperation } from '../store/ai-operation';
import { useAuth } from '../store/auth';
import { useStudio, type StudioStep } from '../store/studio';
import { AuthGate } from '../components/auth-gate';

const serviceNames = { hairstyle: 'Hairstyle', makeup: 'Makeup', nails: 'Nails' };
function suggestedReplies(question: string) {
  if (/maintenance|easy to maintain/i.test(question)) return ['Easy to maintain', 'Some styling is fine', 'No preference'];
  if (/intensity|natural|soft|bold/i.test(question)) return ['Natural and subtle', 'Soft and polished', 'Bold and expressive'];
  if (/color|finish/i.test(question)) return ['Dark and glossy', 'Soft and natural', 'No preference'];
  if (/occasion|getting ready|event/i.test(question)) return ['Everyday', 'Special event', 'Graduation'];
  return [];
}
function QuietAction({ label, onPress, disabled = false }: { label: string; onPress: () => void; disabled?: boolean }) {
  return <Pressable accessibilityRole="button" accessibilityLabel={label} disabled={disabled} onPress={onPress}
    style={({ pressed }) => [styles.quietTouch, pressed && { opacity: 0.7 }, disabled && { opacity: 0.45 }]}>
    <Text style={styles.quietText}>{label}</Text>
  </Pressable>;
}

export default function Consultation() { return <AuthGate><ConsultationContent /></AuthGate>; }
function ConsultationContent() {
  const { draft, chooseService, setPhoto, setDirection, goToStep, reset } = useConsultation();
  const session = useConsultationSession();
  const owner = useAiOperation(s => s.owner);
  const user = useAuth(s => s.user);
  const [showPreferences, setShowPreferences] = useState(false);
  const [reply, setReply] = useState('');
  const [activeLookId, setActiveLookId] = useState<string | null>(null);
  const elapsed = useConsultationStatus();
  const back = useCallback(() => {
    if (draft.step > 0) goToStep((draft.step - 1) as StudioStep); else leaveFlow();
  }, [draft.step, goToStep]);
  const feature = draft.feature;
  const preference = feature ? preferenceOptions[feature] : null;
  const state = session.state;
  const busy = session.busy || Boolean(session.active);
  const owned = !session.userId || session.userId === user?.id;
  const ready = owned && state?.conversation_status === 'ready_for_recommendation' && state.recommendations;
  const conversation = owned && Boolean(session.handle);
  const looks = ready ? state.recommendations!.recommendations : [];
  const activeLook = looks.find(item => item.id === activeLookId) ?? looks[0];
  const activeIndex = looks.findIndex(item => item.id === activeLook?.id);
  const activeDetail = activeLook && session.details[activeLook.id];
  const activeGeneration = activeDetail?.generation ?? state?.generations.find(item => item.recommendation_id === activeLook?.id);
  const lastQuestion = [...(state?.messages ?? [])].reverse().find(item => item.role === 'assistant')?.content ?? '';
  const quickReplies = suggestedReplies(lastQuestion);
  const changePhoto = useCallback((photo: Parameters<typeof setPhoto>[0]) => setPhoto(photo), [setPhoto]);

  function openCustom() {
    if (!feature || owner || busy || !owned) return;
    const studio = useStudio.getState();
    if (draft.photo) { studio.setPhoto(feature, draft.photo); studio.selectStyle(feature, null); studio.goToStep(feature, 1); }
    else studio.goToStep(feature, 0);
    router.push(services[feature].route);
  }
  async function begin() {
    if (!feature || !draft.photo || !user || busy || !reply.trim()) return;
    const firstMessage = reply.trim();
    await session.begin(feature, draft.photo, consultationPreferences(feature, draft.direction), user.id, async () => {
      const { photoUpload } = await import('../lib/image/upload'); return photoUpload(draft.photo!);
    });
    const current = useConsultationSession.getState();
    if (current.handle && !current.needsSync && !current.error && await current.reply(firstMessage)) setReply('');
  }
  async function send() { if (await session.reply(reply)) setReply(''); }
  function restart() { if (!busy) { reset(); setReply(''); setActiveLookId(null); setShowPreferences(false); } }
  function customLink() {
    if (!feature) return null;
    return <Pressable accessibilityRole="link" accessibilityLabel={`Custom ${serviceNames[feature]}`} disabled={busy || Boolean(owner)}
      onPress={openCustom} style={styles.customLink}>
      <Text style={styles.customCopy}>Prefer to choose yourself? <Text style={styles.customEmphasis}>Custom {serviceNames[feature]} ↗</Text></Text>
    </Pressable>;
  }
  function looksAction() {
    if (!activeLook || !ready) return <Button label="Return to Direction" onPress={() => goToStep(1)} />;
    if (session.active?.phase === 'unknown') return <Button label="Check generation status" onPress={() => void session.checkGeneration()} />;
    if (session.active) return <Button label={`Creating ${looks.find(item => item.id === session.active?.recommendationId)?.primary.style_name ?? 'your look'}…`} disabled onPress={() => {}} />;
    if (activeGeneration?.status === 'completed' && activeDetail?.result) return <Button label="View this look →"
      onPress={() => router.push({ pathname: '/consultation-result', params: { recommendation: activeLook.id } })} />;
    return <Button label={activeGeneration?.status === 'failed' ? 'Retry this look' : 'Generate this look ✦'}
      disabled={Boolean(owner) || busy || session.expired || session.needsSync || !['pending', 'failed'].includes(activeGeneration?.status ?? '')}
      onPress={() => void session.generate(activeLook.id)} />;
  }

  if (!owned) return <FlowScreen title="Your Consultation" onBack={leaveFlow} actions={<Button label="Start a new consultation" disabled={busy} onPress={restart} />}>
    <ErrorMessage message="This consultation belongs to your previous sign in. Resolve any running request before starting again with this account." />
  </FlowScreen>;
  return <FlowScreen steps={consultationStages} step={draft.step} onBack={back} consultation
    eyebrow={['01 / CHOOSE A SERVICE', '02 / TELL US YOUR DIRECTION', '03 / EXPLORE YOUR LOOKS'][draft.step]}
    title={['Where shall we begin?', 'Tell us what feels like you.', 'Three looks, your direction.'][draft.step]}
    detail={['Choose the experience you want to explore today.', 'A short conversation helps us find styles that fit your plans.', 'Explore one recommendation at a time. Generate only the looks you want to see.'][draft.step]}
    actions={draft.step === 0 ? <Button label="Continue →" disabled={!feature || busy} onPress={() => goToStep(1)} /> :
      draft.step === 1 ? ready ? <Button label="Explore My Looks →" onPress={() => goToStep(2)} /> :
        session.expired ? <Button label="Start a new consultation" disabled={busy} onPress={restart} /> :
          session.needsSync ? <Button label="Check consultation status" disabled={busy} onPress={() => void session.refresh()} /> :
            !conversation ? <Button label={session.busy ? 'Starting…' : 'Start AI consultation ✦'} disabled={busy || !draft.photo || !reply.trim()}
              onPress={() => void begin()} /> :
              <Button label={session.busy ? 'Waiting for your consultant…' : 'Send reply →'} disabled={busy || !reply.trim()}
                onPress={() => void send()} /> : looksAction()}>
    {session.error !== '' && <ErrorMessage message={session.error} />}
    {session.busy && <Loading label={conversation ? 'Waiting for your AI consultant…' : 'Preparing your photo and direction…'} />}
    {session.active && <View style={styles.statusCard} accessibilityLiveRegion="polite">
      <Text style={styles.statusHeading}>{session.active.phase === 'unknown' ? 'Checking your look' : 'Creating your recommended look'}</Text>
      <Body>{looks.find(item => item.id === session.active?.recommendationId)?.primary.style_name ?? 'Your selected recommendation'} · {elapsed}s elapsed</Body>
      <Body muted>{session.active.phase === 'unknown' ? 'The response was interrupted. Only saved status is being checked.' : 'Keep the app open while this look is created.'}</Body>
    </View>}
    {owner === 'custom' && draft.step === 2 && <View style={styles.statusCard}><Body>A Custom look is running. Finish it before generating a Consultation look.</Body>
      <QuietAction label="View current generation ↗" onPress={() => router.push('/generating')} /></View>}

    {draft.step === 0 && <>
      <ConsultationServiceCards selected={feature} onSelect={chooseService} disabled={busy} />
      <Body muted>{feature ? `${serviceNames[feature]} selected` : 'Select one service to continue.'}</Body>
      {customLink()}
    </>}

    {draft.step === 1 && <>
      <View style={styles.photoSection}>
        <View style={styles.sectionTop}><Text style={styles.kicker}>{feature === 'nails' ? 'YOUR HAND PHOTO' : 'YOUR PORTRAIT'}</Text>
          <Text style={styles.sectionMeta}>01 PHOTO · 03 LOOKS</Text></View>
        {conversation && draft.photo ? <View style={styles.photoSummary}>
          <Image source={{ uri: draft.photo.uri }} style={styles.summaryImage} accessibilityLabel="Your consultation photo" />
          <View style={styles.summaryCopy}><Text style={styles.summaryTitle}>Photo ready ✓</Text><Text numberOfLines={1} style={styles.mutedSmall}>{draft.photo.name}</Text></View>
        </View> : <PhotoPicker photo={draft.photo} onChange={changePhoto} hand={feature === 'nails'} disabled={busy} compact />}
        <Text style={styles.mutedSmall}>One photo is used for your previews. The conversational AI receives your words, not your photo.</Text>
      </View>

      {!conversation ? <>
        <LinearGradient colors={[colors.surface, colors.card]} style={styles.introCard}>
          <Text style={styles.introGlyph}>✦</Text><Text style={styles.introTitle}>A conversation about your look</Text>
          <Body>Share what you want. Your consultant may ask a few useful questions.</Body>
        </LinearGradient>
        <DirectionField label="Describe your look" value={reply} onChange={setReply} multiline maxLength={500}
          placeholder="For example, a classic look that is easy to maintain" disabled={busy} />
        <QuietAction label={showPreferences ? 'Hide optional preferences −' : 'Add a few preferences (optional) +'}
          disabled={busy} onPress={() => setShowPreferences(!showPreferences)} />
        {showPreferences && <View style={styles.preferences}>
          <DirectionField disabled={busy} label="Occasion or event" value={draft.direction.occasion} choices={occasions}
            placeholder="Or describe your occasion" onChange={value => setDirection('occasion', value)} />
          <DirectionField disabled={busy} label="Desired vibe" value={draft.direction.vibe} choices={vibes}
            placeholder="Or describe the mood" onChange={value => setDirection('vibe', value)} />
          {preference && <DirectionField disabled={busy} label={preference.label} value={draft.direction.servicePreference}
            choices={preference.choices} onChange={value => setDirection('servicePreference', value)} />}
          <DirectionField disabled={busy} label="Anything to avoid?" value={draft.direction.avoids} maxLength={160}
            placeholder="For example, high maintenance" onChange={value => setDirection('avoids', value)} />
          <DirectionField disabled={busy} label="Optional notes" value={draft.direction.notes} maxLength={500} multiline
            placeholder="What else should we consider?" onChange={value => setDirection('notes', value)} />
        </View>}
      </> : <>
        {state?.messages.length ? <View style={styles.chatLog} accessibilityLabel="Consultation conversation">
          {state.messages.map((item, index) => <View key={index} style={[styles.message, item.role === 'user' && styles.userMessage]}>
            <Text style={styles.messageRole}>{item.role === 'assistant' ? 'AI CONSULTANT' : 'YOU'}</Text><Body>{item.content}</Body>
          </View>)}
        </View> : <LinearGradient colors={[colors.surface, colors.card]} style={styles.introCard}>
          <Text style={styles.introGlyph}>✦</Text><Text style={styles.introTitle}>Your conversation is ready</Text>
          <Body>Describe the look you want to begin.</Body>
        </LinearGradient>}
        {ready ? <View style={styles.readyCard}><Text style={styles.introGlyph}>✦</Text>
          <Text style={styles.introTitle}>We’ve got your direction.</Text><Body>Three supported looks are ready for you to explore.</Body>
        </View> : !session.expired && <>
          {quickReplies.length > 0 && <View style={styles.quickReplies}><Text style={styles.mutedSmall}>SUGGESTED REPLIES</Text>
            <View style={styles.quickRow}>{quickReplies.map(option => <Pressable key={option} accessibilityRole="button"
              accessibilityLabel={option} accessibilityState={{ selected: reply === option }} disabled={busy || session.needsSync}
              onPress={() => setReply(option)} style={[styles.quickChip, reply === option && styles.quickSelected]}>
              <Text style={styles.quickText}>{option}</Text></Pressable>)}</View></View>}
          <DirectionField label={state?.messages.length ? 'Your reply' : 'Describe your look'} value={reply} onChange={setReply}
            multiline maxLength={500} placeholder="Add your own details or choose a reply above" disabled={busy || session.needsSync} />
        </>}
        <QuietAction label="Start consultation over" disabled={busy} onPress={restart} />
      </>}
    </>}

    {draft.step === 2 && <>
      {!ready ? <View style={styles.statusCard}><Text style={styles.statusHeading}>Your direction comes first</Text>
        <Body>{session.expired ? 'This consultation has expired. Start a new one to continue.' : 'Answer your consultant’s questions before exploring looks.'}</Body></View> : <>
        <View style={styles.lookChoices} accessibilityLabel="Your three recommendations">{looks.map((item, index) => {
          const generation = session.details[item.id]?.generation ?? state?.generations.find(row => row.recommendation_id === item.id);
          const selected = item.id === activeLook?.id;
          return <Pressable key={item.id} accessibilityRole="button" accessibilityLabel={`View look ${index + 1}: ${item.primary.style_name}`}
            accessibilityState={{ selected }} onPress={() => setActiveLookId(item.id)}
            style={[styles.lookChoice, selected && styles.lookChoiceActive]}>
            <Text style={styles.lookNumber}>0{index + 1} · {generation?.status === 'completed' ? 'READY' : generation?.status === 'failed' ? 'FAILED' : generation?.status === 'generating' ? 'CREATING' : 'UP NEXT'}</Text>
            <Text numberOfLines={2} style={styles.lookName}>{item.primary.style_name}</Text>
          </Pressable>;
        })}</View>
        {activeLook && <View style={styles.featuredCard}>
          {activeDetail?.result && draft.photo ? <PhotoFrame photo={{ ...draft.photo, uri: activeDetail.result.image.data_url }}
            label={`${activeLook.primary.style_name} generated recommendation`} /> : <LinearGradient colors={[colors.surface, colors.photo]} style={styles.lookPlaceholder}>
            <Text style={styles.placeholderGlyph}>✦</Text><Text style={styles.placeholderText}>
              {session.active?.recommendationId === activeLook.id ? 'Creating this look…' : activeGeneration?.status === 'failed' ? 'Preview unavailable' : 'Your preview is up next'}
            </Text>
          </LinearGradient>}
          <View style={styles.featuredCopy}>
            <Text style={styles.kicker}>LOOK 0{activeIndex + 1} / 03 · {activeGeneration?.status === 'completed' ? 'READY' : activeGeneration?.status === 'failed' ? 'NEEDS ATTENTION' : 'PERSONALIZED EDIT'}</Text>
            <Text style={styles.featuredTitle}>{activeLook.primary.style_name}</Text><Body>{activeLook.reason}</Body>
            <Text style={styles.estimate}>Estimated {activeLook.primary.service.currency} {activeLook.primary.service.estimated_price.toLocaleString()} · {activeLook.primary.service.estimated_duration_minutes} min <Text style={styles.mutedSmall}>(demo estimate)</Text></Text>
            {activeLook.complements.length > 0 && <Text style={styles.mutedSmall}>Pairs with {activeLook.complements.map(item => item.style_name).join(', ')}. Complementary visuals are not generated.</Text>}
            {state?.selected_recommendation_id === activeLook.id && <Text style={styles.selectedNote}>✓ Selected for this consultation</Text>}
            {activeGeneration?.status === 'failed' && <ErrorMessage message={activeGeneration.error || 'This look could not be generated. You can retry it manually.'} />}
          </View>
        </View>}
        {customLink()}
        <QuietAction label="Start consultation over" disabled={busy} onPress={restart} />
      </>}
    </>}
  </FlowScreen>;
}

const styles = StyleSheet.create({
  quietTouch: { minHeight: layout.touch, justifyContent: 'center', alignSelf: 'flex-start' },
  quietText: { color: colors.goldLight, fontSize: type.small, fontWeight: '700' },
  customLink: { minHeight: layout.touch, justifyContent: 'center', alignSelf: 'flex-start' },
  customCopy: { color: colors.secondary, fontSize: type.small },
  customEmphasis: { color: colors.goldLight, fontWeight: '800' },
  photoSection: { padding: spacing.md, borderWidth: 1, borderColor: colors.border, borderRadius: layout.radius,
    backgroundColor: colors.card, gap: spacing.sm },
  sectionTop: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', gap: spacing.xs },
  kicker: { color: colors.gold, fontSize: 10, fontWeight: '800', letterSpacing: 1.3 },
  sectionMeta: { color: colors.muted, fontSize: 10, fontWeight: '700', letterSpacing: 0.5 },
  mutedSmall: { color: colors.muted, fontSize: type.small, lineHeight: 18 },
  photoSummary: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  summaryImage: { width: 56, height: 62, borderRadius: 8, backgroundColor: colors.photo },
  summaryCopy: { flex: 1, minWidth: 0, gap: spacing.xs },
  summaryTitle: { color: colors.white, fontFamily: serif, fontSize: 18 },
  introCard: { borderWidth: 1, borderColor: colors.border, borderRadius: layout.radius, padding: spacing.sm, gap: spacing.xs },
  introGlyph: { color: colors.gold, fontSize: 22, lineHeight: 24 },
  introTitle: { color: colors.white, fontFamily: serif, fontSize: 21, lineHeight: 25 },
  preferences: { gap: spacing.lg, borderWidth: 1, borderColor: colors.border, borderRadius: layout.radius,
    backgroundColor: colors.card, padding: spacing.md },
  chatLog: { gap: spacing.sm, padding: spacing.sm, borderWidth: 1, borderColor: colors.border,
    borderRadius: layout.radius, backgroundColor: colors.photo },
  message: { alignSelf: 'flex-start', maxWidth: '94%', padding: spacing.sm, borderRadius: layout.radius,
    backgroundColor: colors.card, gap: spacing.xs },
  userMessage: { alignSelf: 'flex-end', backgroundColor: colors.selected },
  messageRole: { color: colors.goldLight, fontSize: 10, fontWeight: '800', letterSpacing: 1 },
  readyCard: { gap: spacing.xs, padding: spacing.md, borderWidth: 1, borderColor: colors.gold,
    borderRadius: layout.radius, backgroundColor: colors.selected },
  quickReplies: { gap: spacing.sm }, quickRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs },
  quickChip: { minHeight: 42, justifyContent: 'center', paddingHorizontal: spacing.sm, borderWidth: 1,
    borderColor: colors.border, borderRadius: 22, backgroundColor: colors.card },
  quickSelected: { borderColor: colors.gold, backgroundColor: colors.selected },
  quickText: { color: colors.secondary, fontSize: type.small },
  statusCard: { gap: spacing.xs, padding: spacing.md, borderWidth: 1, borderColor: colors.border,
    borderRadius: layout.radius, backgroundColor: colors.card },
  statusHeading: { color: colors.white, fontFamily: serif, fontSize: 20 },
  lookChoices: { flexDirection: 'row', gap: spacing.xs },
  lookChoice: { flex: 1, minWidth: 0, minHeight: 74, padding: spacing.xs, justifyContent: 'center',
    gap: spacing.xs, borderWidth: 1, borderColor: colors.border, borderRadius: layout.radius, backgroundColor: colors.card },
  lookChoiceActive: { borderColor: colors.gold, backgroundColor: colors.selected },
  lookNumber: { color: colors.gold, fontSize: 9, fontWeight: '800' },
  lookName: { color: colors.white, fontFamily: serif, fontSize: 15, lineHeight: 19 },
  featuredCard: { overflow: 'hidden', borderWidth: 1, borderColor: colors.border, borderRadius: layout.radius, backgroundColor: colors.card },
  lookPlaceholder: { minHeight: 200, alignItems: 'center', justifyContent: 'center', gap: spacing.sm },
  placeholderGlyph: { color: colors.goldLight, fontSize: 45 },
  placeholderText: { color: colors.secondary, fontSize: type.body },
  featuredCopy: { padding: spacing.md, gap: spacing.sm },
  featuredTitle: { color: colors.white, fontFamily: serif, fontSize: 28, lineHeight: 34 },
  estimate: { color: colors.white, fontSize: type.small, borderTopWidth: 1, borderColor: colors.border,
    paddingTop: spacing.sm },
  selectedNote: { color: colors.success, fontSize: type.small, fontWeight: '700' },
});
