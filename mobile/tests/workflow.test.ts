import test from 'node:test';
import assert from 'node:assert/strict';
import { useStudio } from '../store/studio';
import { useConsultation } from '../store/consultation';
import { featureIds } from '../lib/api/contracts';

const photo = { uri: 'file:///local/portrait.png', name: 'portrait.png', mimeType: 'image/png' as const, width: 512, height: 512, size: 2048 };
const style = { id: 'actual_catalog_id', name: 'Selected style', description: 'Catalog description', status: 'available' };

test('each studio gates progression and Back preserves photo and selection', () => {
  for (const feature of featureIds) {
    const actions = useStudio.getState(); actions.reset(feature);
    actions.goToStep(feature, 1); assert.equal(useStudio.getState().drafts[feature].step, 0);
    actions.setPhoto(feature, photo); actions.goToStep(feature, 1);
    actions.goToStep(feature, 2); assert.equal(useStudio.getState().drafts[feature].step, 1);
    actions.selectStyle(feature, style.id); actions.goToStep(feature, 2);
    actions.goToStep(feature, 1); actions.goToStep(feature, 0);
    assert.deepEqual(useStudio.getState().drafts[feature].photo, photo);
    assert.equal(useStudio.getState().drafts[feature].styleId, style.id);
  }
});

test('Try Another Style retains draft and Start Over resets only its feature', () => {
  const actions = useStudio.getState();
  actions.goToStep('hairstyle', 2); actions.tryAnother('hairstyle');
  const draft = useStudio.getState().drafts.hairstyle;
  assert.equal(draft.step, 1); assert.deepEqual(draft.photo, photo);
  assert.equal(draft.styleId, style.id);
  actions.reset('hairstyle');
  assert.equal(useStudio.getState().drafts.hairstyle.step, 0);
  assert.equal(useStudio.getState().drafts.hairstyle.photo, null);
  assert.deepEqual(useStudio.getState().drafts.makeup.photo, photo);
});

test('photo removal repairs an advanced studio and replacement retains the current selection', () => {
  const actions = useStudio.getState();
  actions.goToStep('nails', 2);
  actions.setPhoto('nails', { ...photo, uri: 'file:///local/replacement.png' });
  assert.equal(useStudio.getState().drafts.nails.photo?.uri, 'file:///local/replacement.png');
  actions.setPhoto('nails', null);
  assert.equal(useStudio.getState().drafts.nails.step, 0);
  actions.tryAnother('nails'); assert.equal(useStudio.getState().drafts.nails.step, 0);
});

test('Consultation gates on service/photo and Back preserves optional direction', () => {
  const actions = useConsultation.getState(); actions.reset(); actions.goToStep(1);
  assert.equal(useConsultation.getState().draft.step, 0);
  actions.chooseService('hairstyle'); actions.goToStep(1);
  assert.equal(useConsultation.getState().draft.step, 0);
  actions.setPhoto(photo); actions.goToStep(1); actions.setDirection('occasion', 'Celebration');
  actions.setDirection('notes', 'My own brief'); actions.goToStep(2); actions.goToStep(0);
  assert.deepEqual(useConsultation.getState().draft.photo, photo);
  assert.equal(useConsultation.getState().draft.direction.occasion, 'Celebration');
  assert.equal(useConsultation.getState().draft.direction.notes, 'My own brief');
});

test('Consultation only clears incompatible photos and service-specific preferences', () => {
  const actions = useConsultation.getState(); actions.setDirection('servicePreference', 'Low');
  actions.chooseService('makeup');
  assert.deepEqual(useConsultation.getState().draft.photo, photo);
  assert.equal(useConsultation.getState().draft.direction.servicePreference, '');
  assert.equal(useConsultation.getState().draft.direction.occasion, 'Celebration');
  actions.chooseService('nails'); assert.equal(useConsultation.getState().draft.photo, null);
  actions.setPhoto(photo); actions.chooseService('nails'); assert.deepEqual(useConsultation.getState().draft.photo, photo);
  actions.chooseService('hairstyle'); assert.equal(useConsultation.getState().draft.photo, null);
});

test('Consultation reset is local and never clears a custom studio', () => {
  const actions = useStudio.getState(); actions.setPhoto('makeup', photo);
  useConsultation.getState().reset();
  assert.equal(useConsultation.getState().draft.feature, null);
  assert.equal(useConsultation.getState().draft.photo, null);
  assert.equal(useConsultation.getState().draft.direction.notes, '');
  assert.deepEqual(useStudio.getState().drafts.makeup.photo, photo);
});
