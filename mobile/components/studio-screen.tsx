import { useCallback } from 'react';
import { router } from 'expo-router';
import type { FeatureId } from '../lib/api/contracts';
import type { LocalPhoto } from '../lib/image/validation';
import { generationUpload } from '../lib/image/upload';
import { useStyles } from '../lib/api/queries';
import { services } from '../constants/services';
import { useStudio, type StudioStep } from '../store/studio';
import { useAuth } from '../store/auth';
import { useGeneration, isUnresolved } from '../store/generation';
import { useAiOperation } from '../store/ai-operation';
import { AuthGate } from './auth-gate';
import { Panel, Body, Button, ErrorMessage, Loading } from './ui';
import { PhotoPicker } from './photo-picker';
import { StyleCatalog } from './style-catalog';
import { FlowScreen, leaveFlow, PhotoFrame } from './workflow';

export function StudioScreen({ feature }: { feature: FeatureId }) { return <AuthGate><StudioContent feature={feature} /></AuthGate>; }
function StudioContent({ feature }: { feature: FeatureId }) {
  const presentation = services[feature];
  const catalog = useStyles(feature);
  const draft = useStudio(state => state.drafts[feature]);
  const { setPhoto, selectStyle, goToStep } = useStudio();
  const job = useGeneration(state => state.job);
  const owner = useAiOperation(state => state.owner);
  const blocked = Boolean(owner) || isUnresolved(job);
  const currentGeneration = useCallback(() => router.push(owner === 'consultation' ? '/consultation' : '/generating'), [owner]);
  const selected = catalog.data?.find(style => style.id === draft.styleId);
  const changePhoto = useCallback((photo: LocalPhoto | null) => setPhoto(feature, photo), [feature, setPhoto]);
  const back = useCallback(() => {
    if (blocked) { currentGeneration(); return; }
    if (draft.step > 0) goToStep(feature, (draft.step - 1) as StudioStep); else leaveFlow();
  }, [blocked, currentGeneration, draft.step, feature, goToStep]);
  function generate() {
    const user = useAuth.getState().user;
    if (!draft.photo || !selected || !user || blocked || catalog.isError) return;
    const photo = draft.photo;
    void useGeneration.getState().run(feature, photo, selected, user.id, () => generationUpload(photo, selected.id));
    router.push('/generating');
  }
  const titles = [presentation.photoTitle, presentation.styleTitle, 'Make it yours.'];
  const details = [presentation.photoDetail, 'Choose one look from your studio collection.', 'Your photo. Your chosen direction.'];
  return <FlowScreen steps={['Photo', 'Style', 'Review']} step={draft.step} onBack={back}
    title={titles[draft.step]} detail={details[draft.step]} actions={<>
      {blocked ? <Button label="View current generation" onPress={currentGeneration} /> : <>
        {draft.step === 0 && <Button label="Continue to Style →" disabled={!draft.photo} onPress={() => goToStep(feature, 1)} />}
        {draft.step === 1 && <><Body muted>{selected ? `Selected: ${selected.name}` : 'Select a style to continue.'}</Body>
          <Button label="Review your look →" disabled={!selected || catalog.isError} onPress={() => goToStep(feature, 2)} /></>}
        {draft.step === 2 && <><Body muted>Your photo is sent through your BeautyCore account when you generate.</Body>
          <Button label="Generate this look ✦" disabled={!draft.photo || !selected || catalog.isError} onPress={generate} /></>}
      </>}
    </>}>
    {draft.step === 0 && <><PhotoPicker photo={draft.photo} onChange={changePhoto} hand={feature === 'nails'} disabled={blocked} />
      <Body muted>Choose a clear photo. Your original stays available for comparison.</Body></>}
    {draft.step === 1 && <>
      {catalog.isFetching && <Loading label={`Loading ${presentation.label.toLowerCase()} choices…`} />}
      {catalog.isError && <ErrorMessage message={catalog.error.message} retry={() => void catalog.refetch()} />}
      {catalog.data && <StyleCatalog styles={catalog.data} selectedId={draft.styleId} nails={feature === 'nails'} disabled={blocked} onSelect={id => selectStyle(feature, id)} />}
      {catalog.data?.length === 0 && <Button label="Refresh styles" secondary disabled={catalog.isFetching} onPress={() => void catalog.refetch()} />}
    </>}
    {draft.step === 2 && <>
      {draft.photo && <PhotoFrame photo={draft.photo} label="Photo for your selected look" />}
      {catalog.isError && <ErrorMessage message={catalog.error.message} retry={() => void catalog.refetch()} />}
      <Panel title={selected?.name ?? 'Choose a style again'} detail={selected?.description}>
        <Body>{presentation.label} · Custom Studio</Body>
        <Button label="Change style" secondary disabled={blocked} onPress={() => goToStep(feature, 1)} />
      </Panel>
      <Button label="Change photo" secondary disabled={blocked} onPress={() => goToStep(feature, 0)} />
    </>}
  </FlowScreen>;
}
