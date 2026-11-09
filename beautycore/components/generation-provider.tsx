'use client';

import { createContext, useContext, useEffect, useRef, useState, useSyncExternalStore, type ReactNode, type Dispatch, type SetStateAction } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { GenerationStore, pending } from '@/lib/ai/generation-store';
import { STORAGE_PREFIX } from '@/lib/ai/generation-storage';
import type { FeatureId } from '@/lib/ai/browser-client';

export const GenerationContext = createContext<GenerationStore | null>(null);
const Context = GenerationContext;
const routes = { hairstyle: '/client/hair-studio', makeup: '/client/makeup-studio', nails: '/client/nail-studio' };
const labels = { hairstyle: 'Hair', makeup: 'Makeup', nails: 'Nails' };

function Session({ owner, children }: { owner: string; children: ReactNode }) {
  const [store] = useState(() => new GenerationStore(owner));
  const state = useSyncExternalStore(store.subscribe, store.getSnapshot, store.getSnapshot);
  useEffect(() => {
    void store.start();
    const changed = (event: StorageEvent) => {
      if (event.key?.startsWith(STORAGE_PREFIX + owner + ':')) void store.sync();
    };
    window.addEventListener('storage', changed);
    const cleared = (event: Event) => { if ((event as CustomEvent).detail === owner) store.stop(); };
    window.addEventListener('beautycore-generation-clear', cleared);
    const timer = window.setInterval(() => store.tick(), 1000);
    return () => { window.removeEventListener('storage', changed); window.removeEventListener('beautycore-generation-clear', cleared); window.clearInterval(timer); store.stop(); };
  }, [store, owner]);
  const active = store.busyFeature();
  const consultationActive = state.consultation.phase === 'generating';
  return <Context.Provider value={store}>
    {state.warning && <p className="studio-alert" role="status">{state.warning}</p>}
    {active && <p className="studio-alert" role="status">
      Your {consultationActive ? 'consultation' : labels[active]} preview is {state.drafts[active].phase === 'unknown' && !consultationActive ? 'awaiting a status check' : 'being generated'}.
      {' '}You can browse other pages. <Link href={consultationActive ? '/client/ai-consultation' : routes[active]}>Return to your preview</Link>.
    </p>}
    {state.ready ? children : <p role="status">Restoring your workspace…</p>}
  </Context.Provider>;
}

export function GenerationProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  return user ? <Session key={user.id} owner={user.id}>{children}</Session> : null;
}

export function useStudioGeneration(feature: FeatureId) {
  const store = useContext(Context);
  if (!store) throw new Error('Studio generation requires the authenticated GenerationProvider.');
  const state = useSyncExternalStore(store.subscribe, store.getSnapshot, store.getSnapshot);
  const draft = state.drafts[feature];
  const [hiddenProgress, setHiddenProgress] = useState(false);
  return { ...draft, ready: state.ready, locked: pending(draft), busy: !!store.busyFeature(),
    progressOpen: !hiddenProgress, hideProgress: () => setHiddenProgress(true),
    generating: draft.phase === 'submitting' || draft.phase === 'generating',
    setFile: (file: File | null) => store.setFile(feature, file),
    select: (id: string) => store.select(feature, id),
    open: (value: boolean) => store.open(feature, value),
    run: () => { setHiddenProgress(false); return store.run(feature); },
    recover: () => { setHiddenProgress(false); return store.recover(feature); } };
}

const emptyView: Record<string, unknown> = {};
const noSubscribe = () => () => {};
const emptySnapshot = () => emptyView;
export function useManualGenerationBusy() {
  const store = useContext(Context);
  useSyncExternalStore(store?.subscribe || noSubscribe, store?.getSnapshot || emptySnapshot, emptySnapshot);
  return !!store && Object.values(store.getSnapshot().drafts).some(pending);
}
/** Guest trials keep their existing isolated state and restoration path. */
export function useConsultationState<T>(key: string, initial: T, trial: boolean): [T, Dispatch<SetStateAction<T>>] {
  const store = useContext(Context);
  const [local, setLocal] = useState(initial);
  const state = useSyncExternalStore(store?.subscribe || noSubscribe,
    store ? () => store.getSnapshot().consultation : emptySnapshot, emptySnapshot);
  if (trial || !store) return [local, setLocal];
  return [(key in state ? state[key] : initial) as T, value => store.setConsultation(key, value, initial)];
}
export function useConsultationRef<T>(key: string, initial: T, trial: boolean) {
  const store = useContext(Context);
  const local = useRef(initial);
  return trial || !store ? local : store.consultationRef(key, initial);
}
