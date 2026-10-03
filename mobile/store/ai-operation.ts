import { create } from 'zustand';
export type OperationKind = 'custom' | 'consultation';
export function createOperationStore() {
  return create<{ owner: OperationKind | null; claim: (owner: OperationKind) => boolean; release: (owner: OperationKind) => void }>((set, get) => ({
    owner: null,
    claim: owner => { if (get().owner) return false; set({ owner }); return true; },
    release: owner => { if (get().owner === owner) set({ owner: null }); },
  }));
}
export const useAiOperation = createOperationStore();
