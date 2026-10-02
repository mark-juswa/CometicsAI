import { useCallback, useEffect, useRef, useState } from 'react';
import { router } from 'expo-router';
import type { FeatureId } from '../lib/api/contracts';
import type { LocalPhoto } from '../lib/image/validation';
import { useStyles } from '../lib/api/queries';
import { services } from '../constants/services';
import { useStudio } from '../store/studio';
import { Screen, Panel, Body, Button, ErrorMessage, Loading } from './ui';
import { PhotoPicker } from './photo-picker';
import { StyleCatalog } from './style-catalog';

export function StudioScreen({ feature }: { feature: FeatureId }) {
  const presentation = services[feature];
  const catalog = useStyles(feature);
  const draft = useStudio(state => state.drafts[feature]);
  const setPhoto = useStudio(state => state.setPhoto);
  const selectStyle = useStudio(state => state.selectStyle);
  const showPreview = useStudio(state => state.showPreview);
  const reset = useStudio(state => state.reset);
  const [preparing, setPreparing] = useState(false);
  const [previewError, setPreviewError] = useState('');
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const selected = catalog.data?.find(style => style.id === draft.styleId);
  const changePhoto = useCallback((photo: LocalPhoto | null) => { setPhoto(feature, photo); setPreviewError(''); }, [feature, setPhoto]);
  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);
  function preview() {
    if (!draft.photo || !selected || preparing) return;
    setPreparing(true); setPreviewError('');
    timer.current = setTimeout(() => {
      showPreview(feature, selected); setPreparing(false);
      router.push({ pathname: '/result', params: { feature } });
    }, 700);
  }
  return <Screen title={presentation.title} emphasis={presentation.emphasis} description={presentation.description}>
    <Body muted>Development preview · Catalogs from the application API</Body>
    <Panel number="01" title={presentation.photoTitle} detail={presentation.photoDetail}>
      <PhotoPicker photo={draft.photo} onChange={changePhoto} hand={feature === 'nails'} disabled={preparing} />
    </Panel>
    <Panel number="02" title={presentation.styleTitle} detail="Select the look you would like to preview.">
      {catalog.isFetching && <Loading label={`Loading ${presentation.label.toLowerCase()} choices…`} />}
      {catalog.isError && <ErrorMessage message={catalog.error.message} retry={() => void catalog.refetch()} />}
      {catalog.data && <StyleCatalog styles={catalog.data} selectedId={draft.styleId} nails={feature === 'nails'} disabled={preparing} onSelect={id => { selectStyle(feature, id); setPreviewError(''); }} />}
    </Panel>
    <Panel number="03" title="Ready to see your preview?">
      <Body>{selected ? `Selected: ${selected.name}` : 'Choose a photo and a style to continue.'}</Body>
      <Body muted>This mock preview shows your unchanged photo. Real generation comes in the next phase.</Body>
      {preparing && <Loading label="Preparing your preview…" />}
      <Button label="Preview this look ✦" disabled={!draft.photo || !selected || catalog.isError || preparing} onPress={preview} />
      <Button label="Reset photo and style" secondary disabled={preparing} onPress={() => { reset(feature); setPreviewError(''); }} />
      <Button label="View sample failure state" secondary disabled={preparing} onPress={() => setPreviewError('Sample preview failure. Please try the preview again.')} />
      {previewError !== '' && <ErrorMessage message={previewError} />}
    </Panel>
  </Screen>;
}
