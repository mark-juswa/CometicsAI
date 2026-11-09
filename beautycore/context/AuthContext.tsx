'use client';

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
  type ReactNode,
} from 'react';
import { useRouter } from 'next/navigation';
import type { UserRole } from '@/db/schema';
import { clearGenerationDrafts } from '@/lib/ai/generation-storage';
import { authUserFromResponse, readAuthResponse } from '@/lib/auth-response';

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatar: string | null;
}

interface AuthContextValue {
  user: AuthUser | null;
  /** True while the initial session check is in flight. */
  loading: boolean;
  login: (email: string, password: string) => Promise<AuthUser>;
  register: (name: string, email: string, password: string) => Promise<AuthUser>;
  logout: () => Promise<void>;
  /** Re-reads the session from the server (e.g. after a profile update). */
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/** Where each role lands after signing in. */
export const roleHome: Record<UserRole, string> = {
  admin: '/admin/dashboard',
  stylist: '/stylist/dashboard',
  client: '/client/dashboard',
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const previousOwner = useRef<string | null>(null);
  const sessionVersion = useRef(0);
  const signingOut = useRef(false);
  const sessionResolved = useRef(false);
  useEffect(() => {
    if (previousOwner.current && previousOwner.current !== user?.id) clearGenerationDrafts(previousOwner.current);
    previousOwner.current = user?.id || null;
  }, [user?.id]);

  const loadSession = useCallback(async () => {
    if (signingOut.current) return;
    const version = ++sessionVersion.current;
    try {
      const res = await fetch('/api/auth/session', { cache: 'no-store' });
      if ((res.status === 401 || res.status === 403) && version === sessionVersion.current) {
        sessionResolved.current = true; setUser(null); return;
      }
      const data = await readAuthResponse(res, 'Could not restore your session.');
      const restored = data.user == null ? null : authUserFromResponse(data.user);
      if (version === sessionVersion.current) { sessionResolved.current = true; setUser(restored); }
    } catch {
      // A transient refresh failure must not erase an active workspace.
      if (version === sessionVersion.current && !sessionResolved.current) setUser(null);
    }
  }, []);

  // Restore the session on first mount so a refresh keeps you signed in.
  useEffect(() => {
    loadSession().finally(() => setLoading(false));
    const refreshOnFocus = () => { void loadSession(); };
    const changed = (event: StorageEvent) => {
      if (event.key === 'beautycore:generation:v1:auth') void loadSession();
    };
    window.addEventListener('focus', refreshOnFocus);
    window.addEventListener('storage', changed);
    return () => { window.removeEventListener('focus', refreshOnFocus); window.removeEventListener('storage', changed); };
  }, [loadSession]);

  const login = useCallback(
    async (email: string, password: string): Promise<AuthUser> => {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await readAuthResponse(res, 'Unable to sign in.');
      const signedIn = authUserFromResponse(data.user);
      sessionVersion.current++;
      sessionResolved.current = true;
      setUser(signedIn);
      return signedIn;
    },
    []
  );

  const register = useCallback(
    async (name: string, email: string, password: string): Promise<AuthUser> => {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
      });
      const data = await readAuthResponse(res, 'Unable to create your account.');
      const registered = authUserFromResponse(data.user);
      sessionVersion.current++;
      sessionResolved.current = true;
      setUser(registered);
      return registered;
    },
    []
  );

  const logout = useCallback(async () => {
    signingOut.current = true;
    sessionVersion.current++;
    if (user) clearGenerationDrafts(user.id);
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
    } finally {
      // Clear locally even if the request failed — the user asked to leave.
      setUser(null);
      signingOut.current = false;
      router.push('/login');
    }
  }, [router, user]);

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, refresh: loadSession }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used inside an <AuthProvider>.');
  }
  return ctx;
}
