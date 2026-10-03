import { useCallback, useState } from 'react';
import { router } from 'expo-router';
import { Body, Button, Panel } from '../components/ui';
import { FlowScreen, leaveFlow, PhotoFrame } from '../components/workflow';
import { ServiceCards, serviceLabels } from '../components/service-cards';
import { PhotoPicker } from '../components/photo-picker';
import { DirectionField } from '../components/direction-field';
import { consultationStages } from '../features/consultation/overview';
import { occasions, vibes, preferenceOptions } from '../features/consultation/direction';
import { services } from '../constants/services';
import { useConsultation } from '../store/consultation';
import { useStudio, type StudioStep } from '../store/studio';
import { AuthGate } from '../components/auth-gate';

export default function Consultation() {
  return <AuthGate><ConsultationContent /></AuthGate>;
}
function ConsultationContent() {
  const { draft, chooseService, setPhoto, setDirection, goToStep, reset } = useConsultation();
  const [more, setMore] = useState(false);
  const back = useCallback(() => {
    if (draft.step > 0) goToStep((draft.step - 1) as StudioStep); else leaveFlow();
  }, [draft.step, goToStep]);
  const feature = draft.feature;
  const preference = feature ? preferenceOptions[feature] : null;
  const direction = draft.direction;
  function openCustom() {
    if (!feature || !draft.photo) return;
    const studio = useStudio.getState();
    studio.setPhoto(feature, draft.photo); studio.goToStep(feature, 1);
    router.push(services[feature].route);
  }
  return <FlowScreen steps={consultationStages} step={draft.step} onBack={back}
    title={['Your beauty, your direction.', 'What feels like you?', 'Your Looks'][draft.step]}
    detail={['Start with a service and one clear photo.', 'Share a little about the look you have in mind. All preferences are optional.', 'Your brief is ready for the next step.'][draft.step]}
    actions={<>
      {draft.step === 0 && <Button label="Continue to Direction →" disabled={!feature || !draft.photo} onPress={() => goToStep(1)} />}
      {draft.step === 1 && <Button label="Review your direction →" onPress={() => goToStep(2)} />}
      {draft.step === 2 && <><Button label={`Explore Custom ${feature ? serviceLabels[feature] : 'Studio'} →`} disabled={!feature || !draft.photo} onPress={openCustom} />
        <Button label="Edit direction" secondary onPress={() => goToStep(1)} /></>}
    </>}>
    {draft.step === 0 && <>
      <ServiceCards selected={feature} onSelect={chooseService} />
      {feature ? <>
        <Body>{services[feature].photoDetail}</Body>
        <PhotoPicker photo={draft.photo} onChange={setPhoto} hand={feature === 'nails'} />
        <Body muted>Hair and Makeup share a portrait. Switching to or from Nails requires a new photo of the right kind.</Body>
      </> : <Panel title="One service. One direction."><Body>Choose Hair, Makeup or Nails to prepare your personal brief.</Body></Panel>}
      <Body muted>Consultation preview · Recommendations are awaiting integration. Your photo and preferences stay local.</Body>
    </>}
    {draft.step === 1 && <>
      <DirectionField label="Occasion or event" value={direction.occasion} choices={occasions} placeholder="Or describe your occasion" onChange={value => setDirection('occasion', value)} />
      <DirectionField label="Desired vibe" value={direction.vibe} choices={vibes} placeholder="Or describe the mood" onChange={value => setDirection('vibe', value)} />
      {preference && <DirectionField label={preference.label} value={direction.servicePreference} choices={preference.choices} onChange={value => setDirection('servicePreference', value)} />}
      <Button label={more ? 'Hide optional details −' : 'Add optional details +'} secondary onPress={() => setMore(!more)} />
      {more && <>
        <DirectionField label="Anything to avoid?" value={direction.avoids} maxLength={160} placeholder="Comma separated, for example high maintenance" onChange={value => setDirection('avoids', value)} />
        <DirectionField label="Optional notes" value={direction.notes} maxLength={500} multiline placeholder="What else should we consider?" onChange={value => setDirection('notes', value)} />
      </>}
    </>}
    {draft.step === 2 && <>
      <Panel title="A little guidance is coming." detail="Personal recommendations are awaiting integration.">
        <Body>Your service, photo and direction are prepared. No AI recommendation has been requested yet.</Body>
        <Body muted>In the meantime, explore a style yourself in your Custom Studio using this photo.</Body>
      </Panel>
      {draft.photo && <PhotoFrame photo={draft.photo} label="Your consultation photo" />}
      <Panel title={feature ? `${serviceLabels[feature]} · Your brief` : 'Your brief'}>
        <Body>Occasion: {direction.occasion || 'No preference'}</Body>
        <Body>Vibe: {direction.vibe || 'No preference'}</Body>
        {preference && <Body>{preference.label}: {direction.servicePreference || 'No preference'}</Body>}
        {direction.avoids !== '' && <Body>Avoid: {direction.avoids}</Body>}
        {direction.notes !== '' && <Body>Notes: {direction.notes}</Body>}
        <Button label="Change service or photo" secondary onPress={() => goToStep(0)} />
      </Panel>
      <Button label="Start consultation over" secondary onPress={reset} />
    </>}
  </FlowScreen>;
}
