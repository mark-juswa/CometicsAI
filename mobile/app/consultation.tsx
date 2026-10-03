import { useCallback, useState } from 'react';
import { router } from 'expo-router';
import { Body, Button, Panel, ErrorMessage, Loading } from '../components/ui';
import { FlowScreen, leaveFlow, PhotoFrame } from '../components/workflow';
import { ServiceCards, serviceLabels } from '../components/service-cards';
import { PhotoPicker } from '../components/photo-picker';
import { DirectionField } from '../components/direction-field';
import { consultationStages } from '../features/consultation/overview';
import { occasions, vibes, preferenceOptions, consultationPreferences } from '../features/consultation/direction';
import { useConsultationStatus } from '../features/consultation/use-status';
import { services } from '../constants/services';
import { useConsultation } from '../store/consultation';
import { useConsultationSession } from '../store/consultation-session';
import { useAiOperation } from '../store/ai-operation';
import { useAuth } from '../store/auth';
import { useStudio, type StudioStep } from '../store/studio';
import { AuthGate } from '../components/auth-gate';

export default function Consultation() { return <AuthGate><ConsultationContent /></AuthGate>; }
function ConsultationContent() {
  const { draft, chooseService, setPhoto, setDirection, goToStep, reset } = useConsultation();
  const session = useConsultationSession();
  const owner = useAiOperation(s => s.owner);
  const user = useAuth(s => s.user);
  const [more, setMore] = useState(false); const [reply, setReply] = useState('');
  const elapsed = useConsultationStatus();
  const back = useCallback(() => {
    if (draft.step > 0) goToStep((draft.step - 1) as StudioStep); else leaveFlow();
  }, [draft.step, goToStep]);
  const feature = draft.feature; const preference = feature ? preferenceOptions[feature] : null;
  const direction = draft.direction; const state = session.state;
  const busy = session.busy || Boolean(session.active);
  const owned = !session.userId || session.userId === user?.id;
  const ready = owned && state?.conversation_status === 'ready_for_recommendation' && state.recommendations;
  const conversation = owned && Boolean(session.handle);
  const looks = ready ? state.recommendations!.recommendations : [];
  const changePhoto = useCallback((photo: Parameters<typeof setPhoto>[0]) => setPhoto(photo), [setPhoto]);
  function openCustom() {
    if (!feature || !draft.photo || owner || busy || !owned) return;
    const studio = useStudio.getState();
    studio.setPhoto(feature, draft.photo); studio.selectStyle(feature, null); studio.goToStep(feature, 1);
    router.push(services[feature].route);
  }
  async function begin() {
    if (!feature || !draft.photo || !user || busy) return;
    setReply('');
    await session.begin(feature, draft.photo, consultationPreferences(feature, direction), user.id, async () => {
      const { photoUpload } = await import('../lib/image/upload'); return photoUpload(draft.photo!);
    });
  }
  async function send() { if (await session.reply(reply)) setReply(''); }
  function edit() { if (session.clear()) { setReply(''); goToStep(1); } }
  function restart() { if (!busy) { reset(); setReply(''); } }
  if (!owned) return <FlowScreen title="Your Consultation" onBack={leaveFlow} actions={<Button label="Start a new consultation" disabled={busy} onPress={restart} />}>
    <ErrorMessage message="This consultation belongs to your previous sign in. Resolve any running request before starting again with this account." />
  </FlowScreen>;
  return <FlowScreen steps={consultationStages} step={draft.step} onBack={back}
    title={['Your beauty, your direction.', 'What feels like you?', 'Your Looks'][draft.step]}
    detail={['Start with a service and one clear photo.', 'Share your direction with your AI beauty consultant.', 'Three personal directions, validated against the current studio collection.'][draft.step]}
    actions={<>
      {draft.step === 0 && <Button label="Continue to Direction →" disabled={!feature || !draft.photo || session.busy} onPress={() => goToStep(1)} />}
      {draft.step === 1 && (session.active || ready ? <Button label="See Your Looks →" onPress={() => goToStep(2)} /> :
        session.needsSync ? <Button label="Check consultation status" disabled={session.busy || session.expired} onPress={() => void session.refresh()} /> :
        !conversation ? <Button label={session.busy ? 'Preparing your consultation…' : 'Begin AI conversation ✦'} disabled={session.busy || !feature || !draft.photo} onPress={() => void begin()} /> :
        <Button label={session.busy ? 'Waiting for your consultant…' : state?.messages.length ? 'Send reply →' : 'Ask the opening question →'} disabled={busy || session.expired || Boolean(state?.messages.length && !reply.trim())}
          onPress={() => void (state?.messages.length ? send() : session.reply())} />)}
      {draft.step === 2 && <Button label={`Explore Custom ${feature ? serviceLabels[feature] : 'Studio'} →`} secondary disabled={!feature || !draft.photo || Boolean(owner) || busy} onPress={openCustom} />}
    </>}>
    {session.error !== '' && <ErrorMessage message={session.error} />}
    {session.busy && <Loading label={conversation ? 'Waiting for your AI consultant…' : 'Preparing your photo and direction…'} />}
    {session.active && <Panel title={session.active.phase === 'unknown' ? 'Checking your look' : 'Creating your recommended look'}>
      <Body>{looks.find(r => r.id === session.active?.recommendationId)?.primary.style_name || 'Your selected recommendation'} · {elapsed}s elapsed</Body>
      <Body muted>{session.active.phase === 'unknown' ? 'The response was interrupted. We are reading saved status; no new generation request is sent.' : 'Your chosen service is processing. Keep the app open. Other generation actions are paused.'}</Body>
      {session.active.phase === 'unknown' && <Button label="Check generation status" secondary onPress={() => void session.checkGeneration()} />}
    </Panel>}
    {owner === 'custom' && <Panel title="Your Custom look is running"><Body>Finish or resolve that request before generating a Consultation look.</Body><Button label="View current generation" secondary onPress={() => router.push('/generating')} /></Panel>}
    {draft.step === 0 && <>
      <ServiceCards selected={feature} onSelect={chooseService} disabled={busy} />
      {feature ? <><Body>{services[feature].photoDetail}</Body><PhotoPicker photo={draft.photo} onChange={changePhoto} hand={feature === 'nails'} disabled={busy} />
        <Body muted>Hair and Makeup share a portrait. Switching to or from Nails requires a new photo of the right kind.</Body></> :
        <Panel title="One service. One direction."><Body>Choose Hair, Makeup or Nails to prepare your personal brief.</Body></Panel>}
      <Body muted>Your photo is uploaded when you begin the conversation, for recommended image generation. The AI consultant receives your text preferences and replies, not your photo.</Body>
    </>}
    {draft.step === 1 && <>
      {!conversation ? <>
        <DirectionField disabled={busy} label="Occasion or event" value={direction.occasion} choices={occasions} placeholder="Or describe your occasion" onChange={value => setDirection('occasion', value)} />
        <DirectionField disabled={busy} label="Desired vibe" value={direction.vibe} choices={vibes} placeholder="Or describe the mood" onChange={value => setDirection('vibe', value)} />
        {preference && <DirectionField disabled={busy} label={preference.label} value={direction.servicePreference} choices={preference.choices} onChange={value => setDirection('servicePreference', value)} />}
        <Button label={more ? 'Hide optional details −' : 'Add optional details +'} secondary disabled={busy} onPress={() => setMore(!more)} />
        {more && <><DirectionField disabled={busy} label="Anything to avoid?" value={direction.avoids} maxLength={160} placeholder="Comma separated, for example high maintenance" onChange={value => setDirection('avoids', value)} />
          <DirectionField disabled={busy} label="Optional notes" value={direction.notes} maxLength={500} multiline placeholder="What else should we consider?" onChange={value => setDirection('notes', value)} /></>}
      </> : <>
        <Panel title={feature ? `${serviceLabels[feature]} · Your direction` : 'Your direction'}><Body>{[direction.occasion, direction.vibe, direction.servicePreference].filter(Boolean).join(' · ') || 'Open to your consultant’s guidance.'}</Body>
          <Body muted>Text guidance only. Your photo is reserved for preview generation.</Body></Panel>
        {state?.messages.map((m, index) => <Panel key={index} title={m.role === 'assistant' ? 'Your beauty consultant' : 'You'}><Body>{m.content}</Body></Panel>)}
        {ready ? <Panel title="Your recommendations are ready"><Body>Your consultant returned three looks validated by the studio. Continue to Your Looks to explore them.</Body></Panel> :
          !session.expired && <DirectionField label="Your reply" value={reply} onChange={setReply} multiline maxLength={500} placeholder="Reply to your consultant’s question" disabled={busy || session.needsSync} />}
        <Button label="Edit direction" secondary disabled={busy} onPress={edit} />
      </>}
      <Button label="Start consultation over" secondary disabled={busy} onPress={restart} />
    </>}
    {draft.step === 2 && <>
      {!ready && <Panel title="Your direction comes first"><Body>{session.expired ? 'This consultation has expired. Start over to create a new one.' : 'Complete your consultant’s questions before exploring recommendations.'}</Body>
        <Button label="Return to Direction" secondary onPress={() => goToStep(1)} /></Panel>}
      {looks.map((r, index) => {
        const detail = session.details[r.id]; const g = detail?.generation ?? state?.generations.find(row => row.recommendation_id === r.id);
        const running = session.active?.recommendationId === r.id;
        const timing = session.times[r.id]; const seconds = timing?.end ? ((timing.end - timing.start) / 1000).toFixed(1) : null;
        return <Panel key={r.id} number={`0${index + 1}`} title={r.primary.style_name} detail={r.reason}>
          <Body>{serviceLabels[r.primary.feature]} · {running ? session.active?.phase === 'unknown' ? 'Checking status' : 'Generating' : g?.status || 'pending'}{seconds ? ` · ${seconds}s` : ''}</Body>
          <Body muted>Demo estimate: {r.primary.service.currency} {r.primary.service.estimated_price} · {r.primary.service.estimated_duration_minutes} min. Salon prices and duration require confirmation.</Body>
          {r.complements.map(c => <Body key={`${c.feature}/${c.style_id}`} muted>Pairs with {serviceLabels[c.feature]} · {c.style_name}</Body>)}
          {g?.status === 'failed' && <ErrorMessage message={g.error || 'This look could not be generated. You can retry manually.'} />}
          {detail?.result && draft.photo && <PhotoFrame photo={{ ...draft.photo, uri: detail.result.image.data_url }} label={`${r.primary.style_name} generated recommendation`} />}
          {g?.status === 'completed' && detail?.result ? <Button label={state?.selected_recommendation_id === r.id ? 'View selected look' : `View ${r.primary.style_name}`} onPress={() => router.push({ pathname: '/consultation-result', params: { recommendation: r.id } })} /> :
            <Button label={`${g?.status === 'failed' ? 'Retry' : 'Generate'} ${r.primary.style_name}`} disabled={Boolean(owner) || busy || session.expired || session.needsSync || !['pending', 'failed'].includes(g?.status || '')} onPress={() => void session.generate(r.id)} />}
        </Panel>;
      })}
      <Button label="Edit direction" secondary disabled={busy} onPress={edit} />
      <Button label="Start consultation over" secondary disabled={busy} onPress={restart} />
    </>}
  </FlowScreen>;
}
