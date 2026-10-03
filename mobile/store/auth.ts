import { create } from 'zustand';
import type { User } from '../lib/api/contracts';

// Only public user identity is retained. Passwords and cookies never enter this store.
export const useAuth = create<{ user: User | null; setUser: (user: User | null) => void }>(set => ({
  user: null, setUser: user => set({ user }),
}));
