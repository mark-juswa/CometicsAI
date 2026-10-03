import { useCallback, useRef, useState } from 'react';
import { router, useFocusEffect } from 'expo-router';
import type { FeatureId } from '../lib/api/contracts';
import type { LocalPhoto } from '../lib/image/validation';
import { useStyles } from '../lib/api/queries';
import { services } from '../constants/services';
import { useStudio, type StudioStep } from '../store/studio';
import { Panel, Body, Button, ErrorMessage, Loading } from './ui';
import { PhotoPicker } from './photo-picker';
import { StyleCatalog } from './style-catalog';
import { FlowScreen, leaveFlow, PhotoFrame } from './workflow';

export function StudioScreen({ feature }: { feature: FeatureId }) {
  const presentation = services[feature];
  const catalog = useStyles(feature);
  const draft = useStudio(state => state.drafts[feature]);
  const { setPhoto, selectStyle, showPreview, goToStep } = useStudio();
  const [preparing, setPreparing] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const selected = catalog.data?.find(style => style.id === draft.styleId);
  const changePhoto = useCallback((photo: LocalPhoto | null) => setPhoto(feature, photo), [feature, setPhoto]);
  const cancel = useCallback(() => { if (timer.current) clearTimeout(timer.current); timer.current = null; setPreparing(false); }, []);
  useFocusEffect(useCallback(() => cancel, [cancel]));
  const back = useCallback(() => {
    cancel();
    if (draft.step > 0) goToStep(feature, (draft.step - 1) as StudioStep); else leaveFlow();
  }, [cancel, draft.step, feature, goToStep]);
  function preview() {
    if (!draft.photo || !selected || preparing || catalog.isError) return;
    setPreparing(true);
    timer.current = setTimeout(() => {
      timer.current = null;
      showPreview(feature, selected); setPreparing(false);
      router.push({ pathname: '/result', params: { feature } });
    }, 700);
  }
  const titles = [presentation.photoTitle, presentation.styleTitle, 'Make it yours.'];
  const details = [presentation.photoDetail, 'Choose one look from your studio collection.', 'Your photo. Your chosen direction.'];
  return <FlowScreen steps={['Photo', 'Style', 'Review']} step={draft.step} onBack={back}
    title={titles[draft.step]} detail={details[draft.step]} actions={<>
      {draft.step === 0 && <Button label="Continue to Style →" disabled={!draft.photo} onPress={() => goToStep(feature, 1)} />}
      {draft.step === 1 && <><Body muted>{selected ? `Selected: ${selected.name}` : 'Select a style to continue.'}</Body>
        <Button label="Review your look →" disabled={!selected || catalog.isError} onPress={() => goToStep(feature, 2)} /></>}
      {draft.step === 2 && <><Body muted>Preview mode · Your unchanged photo, no AI transformation.</Body>
        <Button label={preparing ? 'Preparing preview…' : 'Generate preview ✦'} disabled={!draft.photo || !selected || catalog.isError || preparing} onPress={preview} /></>}
    </>}>
    {draft.step === 0 && <><PhotoPicker photo={draft.photo} onChange={changePhoto} hand={feature === 'nails'} />
      <Body muted>Your photo stays on this device during this preview.</Body></>}
    {draft.step === 1 && <>
      {catalog.isFetching && <Loading label={`Loading ${presentation.label.toLowerCase()} choices…`} />}
      {catalog.isError && <ErrorMessage message={catalog.error.message} retry={() => void catalog.refetch()} />}
      {catalog.data && <StyleCatalog styles={catalog.data} selectedId={draft.styleId} nails={feature === 'nails'} onSelect={id => selectStyle(feature, id)} />}
      {catalog.data?.length === 0 && <Button label="Refresh styles" secondary disabled={catalog.isFetching} onPress={() => void catalog.refetch()} />}
    </>}
    {draft.step === 2 && <>
      {draft.photo && <PhotoFrame photo={draft.photo} label="Photo for your selected look" />}
      {catalog.isError && <ErrorMessage message={catalog.error.message} retry={() => void catalog.refetch()} />}
      <Panel title={selected?.name ?? 'Choose a style again'} detail={selected?.description}>
        <Body>{presentation.label} · Custom Studio</Body>
        <Button label="Change style" secondary disabled={preparing} onPress={() => goToStep(feature, 1)} />
      </Panel>
      <Button label="Change photo" secondary disabled={preparing} onPress={() => goToStep(feature, 0)} />
      {preparing && <Loading label="Preparing your preview…" />}
    </>}
  </FlowScreen>;
}
