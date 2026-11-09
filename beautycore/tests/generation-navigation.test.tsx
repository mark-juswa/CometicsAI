/** Investigation harness: reproduce the submitted branch, no real AI or database. */
import test, { mock } from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
// @ts-expect-error The existing runtime test dependency has no bundled declarations.
import { JSDOM } from 'jsdom';
import { act } from 'react';
import { render, fireEvent, waitFor, cleanup } from '@testing-library/react';

const dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'https://fixture.example/client/hair-studio' });
Object.assign(globalThis, { window: dom.window, self: dom.window, document: dom.window.document,
  HTMLElement: dom.window.HTMLElement, IS_REACT_ACT_ENVIRONMENT: true });
Object.defineProperty(globalThis, 'navigator', { configurable: true, value: dom.window.navigator });
Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: dom.window.localStorage });
let revoked = 0;
URL.createObjectURL = () => 'blob:investigation-photo';
URL.revokeObjectURL = () => { revoked++; };

const Container = ({ children }: { children?: React.ReactNode }) => <div>{children}</div>;
mock.module('../components/ai-studio.tsx', { namedExports: {
  StudioShell: Container, StudioPanel: Container,
  StudioPhoto: ({ src }: { src: string }) => <img src={src} alt="uploaded fixture" />,
  GenerationProgress: () => <div data-testid="progress">Generation in progress</div>,
  ResultDialog: ({ result }: { result: unknown }) => result ? <div data-testid="result">Completed result</div> : null,
}});
mock.module('../components/reference-image-picker.tsx', { namedExports: { ReferenceImagePicker: () => null } });

mock.module('../context/AuthContext.tsx', { namedExports: { useAuth: () => ({ user: { id: 'test-client' } }) } });
const { GenerationProvider } = await import('../components/generation-provider');
const { default: Hair } = await import('../app/client/hair-studio/page');
const { default: Makeup } = await import('../app/client/makeup-studio/page');
const { default: Nails } = await import('../app/client/nail-studio/page');
const pages = [Hair, Makeup, Nails];
const names = ['hairstyle', 'makeup', 'nails'];

for (let index = 0; index < pages.length; index++) {
  test(`${names[index]}: route exit preserves photo and progress, blocks competing work, and restores result`, async () => {
    localStorage.clear();
    const before = globalThis.fetch;
    const calls: string[] = [];
    let active = false;
    let completed = false;
    let dispatches = 0;
    const job = '11111111-1111-4111-8111-111111111111';
    const result = { status: 'completed', style: { id: 'fixture', name: 'Fixture Style', description: '', status: 'available' },
      image: { content_type: 'image/png', width: 1, height: 1, data_url: 'data:image/png;base64,AA==' } };
    globalThis.fetch = async (input, init) => {
      const path = String(input);
      calls.push((init?.method || 'GET') + ' ' + path);
      if (path.endsWith('/styles')) return Response.json([{ id: 'fixture', name: 'Fixture Style', description: '', status: 'available' }]);
      if (init?.method === 'POST' && path.endsWith('/generate')) {
        if (active) return Response.json({ error: 'Another generation is already running.', code: 'AI_BUSY' }, { status: 429 });
        active = true; dispatches++;
        return Response.json({ job_id: job, status: 'generating' }, { status: 202 });
      }
      if (path.endsWith('/result')) return Response.json(result);
      if (path.endsWith('/jobs/' + job)) return Response.json({ job_id: job, status: completed ? 'completed' : 'generating' });
      throw Error('Unexpected request ' + path);
    };
    async function choose(view: ReturnType<typeof render>) {
      await waitFor(() => assert.equal(view.getAllByRole('button', { name: /Fixture Style/ }).length, 1));
      const input = view.container.querySelector('input[type=file]')!;
      fireEvent.change(input, { target: { files: [new File(['fixture'], 'fixture.png', { type: 'image/png' })] } });
      fireEvent.click(view.getByRole('button', { name: /Fixture Style/ }));
    }
    try {
      const First = pages[index], Other = pages[(index + 1) % pages.length];
      const view = render(<GenerationProvider><First /></GenerationProvider>);
      await choose(view);
      fireEvent.click(view.container.querySelector('button.studio-primary-button')!);
      await waitFor(() => assert.equal(dispatches, 1));
      assert.ok(view.queryByTestId('progress'));
      const beforeRevoke = revoked;
      view.rerender(<GenerationProvider><Other /></GenerationProvider>);
      assert.equal(revoked, beforeRevoke);
      await choose(view);
      assert.equal(view.queryByTestId('progress'), null);
      assert.equal((view.container.querySelector('button.studio-primary-button')! as HTMLButtonElement).disabled, true);
      fireEvent.click(view.container.querySelector('button.studio-primary-button')!);
      assert.equal(calls.filter(call => call.startsWith('POST ')).length, 1);
      assert.equal(dispatches, 1, 'server rejects a competing POST rather than dispatching a second GPU job');
      view.rerender(<GenerationProvider><First /></GenerationProvider>);
      await waitFor(() => assert.ok(view.getByRole('button', { name: /Fixture Style/ })));
      assert.ok(view.queryByTestId('progress'));
      assert.ok(view.container.querySelector('img'), 'original preview survives route exit');
      assert.equal((view.container.querySelector('button.studio-primary-button')! as HTMLButtonElement).disabled, true);
      await act(async () => {
        completed = true; active = false;
        await new Promise(resolve => setTimeout(resolve, 2200));
      });
      assert.ok(calls.some(call => call.endsWith('/jobs/' + job + '/result')), 'old unmounted request still fetches completed result');
      assert.ok(view.queryByTestId('result'), 'completed response is delivered to the returning page');
      assert.equal(calls.filter(call => call.startsWith('POST ')).length, 1);
      console.log(JSON.stringify({ feature: names[index], accepted_gpu_dispatches: dispatches,
        competing_post_prevented: true, original_job_completed: true, result_restored: true,
        preview_restored: true, progress_restored: true, calls }));
    } finally { cleanup(); globalThis.fetch = before; }
  });
}
