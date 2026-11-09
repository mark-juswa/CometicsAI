import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { JSDOM } from 'jsdom';
import { renderToStaticMarkup } from 'react-dom/server';
const dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'https://fixture.example' });
for (const name of ['window', 'document', 'HTMLElement', 'HTMLDialogElement', 'HTMLVideoElement', 'HTMLCanvasElement', 'HTMLMediaElement', 'Event'])
  Object.defineProperty(globalThis, name, { configurable: true, value: dom.window[name] });
Object.defineProperty(globalThis, 'navigator', { configurable: true, value: dom.window.navigator });
globalThis.localStorage = window.localStorage;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', ''); };
HTMLDialogElement.prototype.close = function () { this.removeAttribute('open'); this.dispatchEvent(new Event('close')); };
HTMLMediaElement.prototype.play = async function () {};
test.mock.module('next/link', { defaultExport: ({ children, ...props }) => React.createElement('a', props, children) });
const { render, screen, fireEvent, waitFor, cleanup, act } = await import('@testing-library/react');
const { CameraCapture } = await import('../components/camera-capture.tsx');
const { default: Methodology } = await import('../app/(public)/how-ai-works/page.tsx');
const { default: Consultation } = await import('../components/consultation.tsx');
const { GenerationContext } = await import('../components/generation-provider.tsx');
const { GenerationStore } = await import('../lib/ai/generation-store.ts');
let stopped, requests, files, revoked, drawing;
test.beforeEach(() => {
  stopped = 0; requests = []; files = []; revoked = []; drawing = [];
  URL.createObjectURL = () => 'blob:camera-fixture'; URL.revokeObjectURL = url => revoked.push(url);
  Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: { getUserMedia: async constraints => {
    requests.push(constraints); return { getTracks: () => [{ stop: () => { stopped++; } }] };
  } } });
  HTMLCanvasElement.prototype.getContext = () => ({ drawImage: (...args) => { drawing.push(args); } });
  HTMLCanvasElement.prototype.toBlob = callback => callback(new Blob(['fixture'], { type: 'image/jpeg' }));
});
test.afterEach(cleanup);
function mount(props = {}) { return render(React.createElement(CameraCapture, { onCapture: file => files.push(file), ...props })); }
async function open() {
  fireEvent.click(screen.getByRole('button', { name: 'Use camera', exact: true }));
  await waitFor(() => assert.equal(requests.length, 1));
}
function ready(width = 1920, height = 1080) {
  const video = screen.getByLabelText('Live camera preview');
  Object.defineProperties(video, { videoWidth: { configurable: true, value: width }, videoHeight: { configurable: true, value: height } });
  fireEvent.loadedData(video);
}

test('camera is explicit, video only, reviewed before selection, bounded and never auto submitted', async () => {
  let network = 0; const previous = globalThis.fetch;
  globalThis.fetch = async () => { network++; throw Error('Network forbidden'); };
  try {
    mount(); assert.equal(requests.length, 0); await open(); ready();
    assert.equal(requests[0].audio, false); assert.equal(requests[0].video.facingMode.ideal, 'user');
    fireEvent.click(screen.getByRole('button', { name: 'Take photo', exact: true }));
    await screen.findByAltText('Captured photo for review');
    assert.equal(stopped, 1); assert.equal(files.length, 0);
    assert.deepEqual(drawing[0].slice(-2), [1600, 900]);
    fireEvent.click(screen.getByRole('button', { name: 'Use photo', exact: true }));
    assert.equal(files.length, 1); assert.equal(files[0].type, 'image/jpeg'); assert.match(files[0].name, /^camera-.*\.jpg$/);
    assert.equal(screen.queryByRole('dialog'), null); assert.ok(revoked.includes('blob:camera-fixture')); assert.equal(network, 0);
  } finally { globalThis.fetch = previous; }
});

test('retake acquires a new preview and switching camera releases the old one', async () => {
  mount(); await open(); ready(); fireEvent.click(screen.getByRole('button', { name: 'Take photo', exact: true }));
  await screen.findByAltText('Captured photo for review'); fireEvent.click(screen.getByRole('button', { name: 'Retake' }));
  await waitFor(() => assert.equal(requests.length, 2));
  fireEvent.click(screen.getByRole('button', { name: 'Switch camera' }));
  await waitFor(() => assert.equal(requests.length, 3));
  assert.equal(requests[2].video.facingMode.ideal, 'environment');
  assert.equal(stopped, 2); fireEvent.click(screen.getByRole('button', { name: 'Close camera' })); assert.equal(stopped, 3);
});

test('close, cancellation, route departure and disabled state release camera resources', async () => {
  let view = mount(); await open(); view.unmount(); assert.equal(stopped, 1);
  requests = []; view = mount(); await open(); fireEvent(screen.getByRole('dialog'), new Event('cancel', { bubbles: true }));
  assert.equal(stopped, 2); assert.equal(screen.queryByRole('dialog'), null); view.unmount();
  requests = []; view = mount(); await open(); view.rerender(React.createElement(CameraCapture, { disabled: true, onCapture: () => {} }));
  assert.equal(stopped, 3); assert.equal(screen.queryByRole('dialog'), null);
});

test('a late permission response is stopped after the camera window closes', async () => {
  let grant;
  navigator.mediaDevices.getUserMedia = constraints => { requests.push(constraints); return new Promise(resolve => { grant = resolve; }); };
  mount(); await open(); fireEvent.click(screen.getByRole('button', { name: 'Close camera' }));
  await act(async () => { grant({ getTracks: () => [{ stop: () => { stopped++; } }] }); });
  assert.equal(stopped, 1); assert.equal(files.length, 0); assert.equal(screen.queryByRole('dialog'), null);
});

test('permission denial and missing camera keep fallback and ordinary upload available', async () => {
  for (const name of ['NotAllowedError', 'NotFoundError']) {
    navigator.mediaDevices.getUserMedia = async () => { throw Object.assign(Error('controlled'), { name }); };
    mount(); fireEvent.click(screen.getByRole('button', { name: 'Use camera', exact: true }));
    const alert = await screen.findByRole('alert'); assert.match(alert.textContent, /upload a photo instead/);
    assert.ok(screen.getByRole('button', { name: 'Use device camera picker' })); assert.equal(files.length, 0); cleanup();
  }
});

test('unsupported live preview offers a rear facing native picker and review', async () => {
  Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: undefined });
  mount({ facing: 'environment' }); fireEvent.click(screen.getByRole('button', { name: 'Use camera', exact: true }));
  await screen.findByRole('alert'); const input = screen.getByLabelText('Device camera photo');
  assert.equal(input.getAttribute('capture'), 'environment');
  fireEvent.change(input, { target: { files: [new File(['p'], 'native.png', { type: 'image/png' })] } });
  await screen.findByAltText('Captured photo for review'); assert.equal(files.length, 0);
  fireEvent.click(screen.getByRole('button', { name: 'Use photo', exact: true })); assert.equal(files[0].name, 'native.png');
});

test('capture failure and unsupported native files never select a photo', async () => {
  HTMLCanvasElement.prototype.toBlob = callback => callback(null);
  mount(); await open(); ready(); fireEvent.click(screen.getByRole('button', { name: 'Take photo', exact: true }));
  assert.match(screen.getByRole('alert').textContent, /could not be captured/); assert.equal(files.length, 0);
  fireEvent.change(screen.getByLabelText('Device camera photo'), { target: { files: [new File(['x'], 'photo.heic', { type: 'image/heic' })] } });
  assert.match(screen.getByRole('alert').textContent, /JPG or PNG/); assert.equal(files.length, 0);
});

test('a canvas response after dismissal is ignored and generation lock prevents opening', async () => {
  let encoded; HTMLCanvasElement.prototype.toBlob = callback => { encoded = callback; };
  mount(); await open(); ready(); fireEvent.click(screen.getByRole('button', { name: 'Take photo', exact: true }));
  fireEvent.click(screen.getByRole('button', { name: 'Close camera' }));
  await act(async () => { encoded(new Blob(['x'], { type: 'image/jpeg' })); }); assert.equal(files.length, 0);
  cleanup(); requests = []; mount({ disabled: true }); fireEvent.click(screen.getByRole('button', { name: 'Use camera', exact: true }));
  assert.equal(requests.length, 0); assert.equal(screen.queryByRole('dialog'), null);
});

test('methodology distinguishes project training, inference, hybrid Nails and quality limits', () => {
  const html = renderToStaticMarkup(React.createElement(Methodology));
  for (const text of ['FLUX.2 Klein Base 4B', 'LoRA', 'does not retrain', 'not an untouched final test set', 'programmed rendering', 'cannot guarantee'])
    assert.ok(html.includes(text), text);
  assert.equal((html.match(/<h1/g) || []).length, 1);
  assert.ok(html.includes('id="training"')); assert.ok(html.includes('id="your-preview"'));
});

test('consultation offers the same camera input with rear facing capture for Nails', async () => {
  const before = globalThis.fetch;
  globalThis.fetch = async () => Response.json({ provider: 'deterministic' });
  const workspace = new GenerationStore('fixture', { assets: { read: async () => undefined, write: async () => {}, remove: async () => {} } });
  workspace.setConsultation('service', 'nails', null); workspace.setConsultation('step', 2, 1);
  try {
    render(React.createElement(GenerationContext.Provider, { value: workspace }, React.createElement(Consultation)));
    await open(); assert.equal(requests[0].video.facingMode.ideal, 'environment');
    fireEvent.click(screen.getByRole('button', { name: 'Close camera' }));
    assert.equal(stopped, 1);
  } finally { workspace.stop(); globalThis.fetch = before; }
});
