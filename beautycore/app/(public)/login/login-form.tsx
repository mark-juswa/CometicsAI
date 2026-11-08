'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { LogIn, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth, roleHome } from '@/context/AuthContext';
import type { UserRole } from '@/db/schema';

const roles: Array<{ value: UserRole; label: string }> = [
  { value: 'client', label: 'Client' },
  { value: 'admin', label: 'Admin' },
  { value: 'stylist', label: 'Stylist' },
];

export default function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();

  const [role, setRole] = useState<UserRole>('client');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const user = await login(email.trim(), password);
      const redirect = user.role === 'client' && searchParams.get('continue') === 'consultation'
        ? '/client/ai-consultation' : searchParams.get('redirect') || roleHome[user.role];
      router.push(redirect);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to sign in.');
    } finally {
      setLoading(false);
    }
  };

return (
    <div className="flex min-h-screen items-center justify-center px-6 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <div className="glass rounded-sm p-8">
          <div className="mb-8 text-center">
            <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full border border-gold/30 bg-gold/10">
              <LogIn size={20} className="text-gold" />
            </div>
            <h1 className="mb-2 font-serif text-3xl text-white">Welcome back</h1>
            <p className="text-[13px] text-muted">Sign in to continue</p>
          </div>

          {/* Role tabs */}
          <div className="mb-6 flex gap-1 rounded-sm border border-purple-light/15 bg-surface/40 p-1">
            {roles.map((r) => (
              <button
                key={r.value}
                type="button"
                onClick={() => setRole(r.value)}
                className={`relative flex-1 rounded-sm py-2 text-[11px] font-medium uppercase tracking-[1.5px] transition-colors ${
                  role === r.value ? 'text-white' : 'text-muted hover:text-secondary'
                }`}
              >
                {role === r.value && (
                  <motion.span
                    layoutId="login-role"
                    className="absolute inset-0 rounded-sm bg-purple/30"
                  />
                )}
                <span className="relative">{r.label}</span>
              </button>
            ))}
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-5 flex items-start gap-2 rounded-sm border border-error/30 bg-error/10 p-3 text-[13px] text-error"
            >
              <AlertCircle size={16} className="mt-0.5 shrink-0" />
              <span>{error}</span>
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div>
              <label htmlFor="email" className="mb-1.5 block text-[11px] font-medium text-secondary">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full rounded-sm border border-purple-light/20 bg-surface/40 px-4 py-2.5 text-[13px] text-white placeholder-muted focus:border-purple-light focus:outline-none"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="mb-1.5 block text-[11px] font-medium text-secondary">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full rounded-sm border border-purple-light/20 bg-surface/40 px-4 py-2.5 text-[13px] text-white placeholder-muted focus:border-purple-light focus:outline-none"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="flex items-center justify-center gap-2 bg-gold px-6 py-3 text-[11px] font-semibold uppercase tracking-[2px] text-card transition-all hover:bg-gold-hover disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Signing in…
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-[12px] text-muted">
            Don&apos;t have an account?{' '}
            <Link href="/register" className="text-gold hover:underline">
              Register
            </Link>
          </p>


        </div>
      </motion.div>
    </div>
  );
}
