import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { JSDOM } from 'jsdom';
const dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'http://localhost:3000' });
for (const name of ['window', 'document', 'HTMLElement', 'Event', 'CustomEvent', 'StorageEvent'])
  Object.defineProperty(globalThis, name, { configurable: true, value: dom.window[name] });
Object.defineProperty(globalThis, 'navigator', { configurable: true, value: dom.window.navigator });
globalThis.localStorage = window.localStorage;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
test.mock.module('next/navigation', { namedExports: { useRouter: () => ({ push() {}, replace() {} }) } });
test.mock.module('next/link', { defaultExport: ({ children, ...props }) => React.createElement('a', props, children) });
const { render, screen, fireEvent, waitFor, cleanup, act } = await import('@testing-library/react');
const { AuthProvider, useAuth } = await import('../context/AuthContext.tsx');
const { GenerationProvider, useStudioGeneration } = await import('../components/generation-provider.tsx');
const { ticketKey } = await import('../lib/ai/generation-storage.ts');
const { rememberCustomPhoto, takeCustomPhoto } = await import('../lib/ai/studio-photo-handoff.ts');
const alice = { id: 'alice', name: 'Alice', email: 'alice@example.invalid', role: 'client', avatar: null };
const bob = { ...alice, id: 'bob', name: 'Bob' };
function Studio() {
  const job = useStudioGeneration('makeup');
  return React.createElement('section', null,
    React.createElement('output', null, job.file?.name || 'No draft photo'),
    React.createElement('button', { onClick: () => { job.setFile(new File(['p'], 'alice.png', { type: 'image/png' })); job.select('red'); } }, 'Choose fixture'),
    React.createElement('button', { onClick: () => { void job.run(); } }, 'Generate fixture'));
}
function Harness() {
  const { user, loading, logout } = useAuth();
  return React.createElement(React.Fragment, null,
    React.createElement('p', null, loading ? 'Loading identity' : user ? 'Account: ' + user.id : 'Signed out'),
    user && React.createElement('button', { onClick: () => { void logout(); } }, 'Log out'),
    React.createElement(GenerationProvider, null, React.createElement(Studio)));
}
test.afterEach(() => { cleanup(); localStorage.clear(); });

test('logout clears the account draft and a late admitted response cannot recreate its journal', async () => {
  let admit; let posts = 0;
  globalThis.fetch = async (input) => {
    const url = String(input);
    if (url === '/api/auth/session') return Response.json({ user: alice });
    if (url === '/api/auth/logout') return Response.json({ ok: true });
    if (url.endsWith('/generate')) { posts++; return new Promise(resolve => { admit = resolve; }); }
    throw Error('Unexpected request ' + url);
  };
  render(React.createElement(AuthProvider, null, React.createElement(Harness)));
  await screen.findByText('No draft photo');
  fireEvent.click(screen.getByRole('button', { name: 'Choose fixture' }));
  fireEvent.click(screen.getByRole('button', { name: 'Generate fixture' }));
  await waitFor(() => assert.equal(posts, 1));
  assert.ok(localStorage.getItem(ticketKey('alice', 'makeup')));
  rememberCustomPhoto('nails', new File(['private'], 'handoff.png'));
  fireEvent.click(screen.getByRole('button', { name: 'Log out' }));
  await screen.findByText('Signed out');
  assert.equal(localStorage.getItem(ticketKey('alice', 'makeup')), null);
  assert.equal(takeCustomPhoto('nails'), null);
  await act(async () => { admit(Response.json({ job_id: '11111111-1111-4111-8111-111111111111', status: 'generating' }, { status: 202 })); });
  assert.equal(localStorage.getItem(ticketKey('alice', 'makeup')), null);
  assert.equal(posts, 1);
});

test('focus detects another account and replaces the workspace without exposing the previous photo', async () => {
  let account = alice;
  globalThis.fetch = async () => Response.json({ user: account });
  render(React.createElement(AuthProvider, null, React.createElement(Harness)));
  await screen.findByText('No draft photo'); fireEvent.click(screen.getByRole('button', { name: 'Choose fixture' }));
  await screen.findByText('alice.png');
  account = bob; fireEvent(window, new Event('focus'));
  await screen.findByText('Account: bob'); await screen.findByText('No draft photo');
  assert.equal(localStorage.getItem(ticketKey('alice', 'makeup')), null);
  assert.equal(screen.queryByText('alice.png'), null);
});

test('a stale focus response cannot sign the user back in after logout', async () => {
  let read = 0, complete;
  globalThis.fetch = async input => {
    if (String(input) === '/api/auth/logout') return Response.json({ ok: true });
    if (++read === 1) return Response.json({ user: alice });
    return new Promise(resolve => { complete = resolve; });
  };
  render(React.createElement(AuthProvider, null, React.createElement(Harness)));
  await screen.findByText('No draft photo'); fireEvent(window, new Event('focus'));
  await waitFor(() => assert.equal(typeof complete, 'function'));
  fireEvent.click(screen.getByRole('button', { name: 'Log out' })); await screen.findByText('Signed out');
  await act(async () => { complete(Response.json({ user: alice })); });
  assert.ok(screen.getByText('Signed out')); assert.equal(screen.queryByText('Account: alice'), null);
});

test('an interrupted or unavailable focus check preserves the existing account draft', async () => {
  let unavailable = false;
  globalThis.fetch = async () => unavailable ? Response.json({ error: 'temporarily unavailable' }, { status: 503 }) : Response.json({ user: alice });
  render(React.createElement(AuthProvider, null, React.createElement(Harness)));
  await screen.findByText('No draft photo'); fireEvent.click(screen.getByRole('button', { name: 'Choose fixture' }));
  await screen.findByText('alice.png'); unavailable = true;
  await act(async () => { fireEvent(window, new Event('focus')); });
  assert.ok(screen.getByText('Account: alice')); assert.ok(screen.getByText('alice.png'));
  assert.ok(localStorage.getItem(ticketKey('alice', 'makeup')));
});

test('the session endpoint distinguishes account service failure from a confirmed signed out session', async () => {
  let outage = true;
  test.mock.module('../lib/auth.ts', { namedExports: { getSession: async () => {
    if (outage) throw Error('controlled session service outage');
    return null;
  } } });
  test.mock.module('../db/index.ts', { namedExports: { db: {} } });
  const { GET } = await import('../app/api/auth/session/route.ts');
  const before = console.error;
  console.error = () => {};
  try {
    const failed = await GET(); assert.equal(failed.status, 503);
    assert.equal('user' in await failed.json(), false);
    outage = false;
    const signedOut = await GET(); assert.equal(signedOut.status, 200);
    assert.deepEqual(await signedOut.json(), { user: null });
  } finally { console.error = before; }
});
