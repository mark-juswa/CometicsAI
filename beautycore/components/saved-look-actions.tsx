'use client';
import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { saveLook, type SavedLook } from '../lib/business/client';
import type { FeatureId, GeneratedResult } from '../lib/ai/browser-client';
export function SavedLookActions({
  feature,
  result,
  sourceKind = 'manual',
  bookLabel = 'Book This Look',
}: {
  feature: FeatureId;
  result: GeneratedResult;
  sourceKind?: 'manual' | 'consultation';
  bookLabel?: string;
}) {
  const router = useRouter();
  const [saved, setSaved] = useState<SavedLook | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const lock = useRef(false);
  const latest = useRef(result);
  latest.current = result;
  useEffect(() => {
    setSaved(null);
    setError('');
  }, [result]);
  async function run(book: boolean) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError('');
    const current = result;
    try {
      const look = saved ?? (await saveLook(feature, current, sourceKind));
      if (latest.current !== current) return;
      setSaved(look);
      if (book) router.push(`/booking?look=${encodeURIComponent(look.id)}`);
    } catch (cause) {
      if (latest.current === current)
        setError(cause instanceof Error ? cause.message : 'Could not save this look.');
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  if (result.status !== 'completed') return null;
  return (
    <div className="saved-look-actions">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className="studio-secondary-button"
          disabled={busy || !!saved}
          onClick={() => void run(false)}
        >
          {busy ? 'Saving…' : saved ? 'Saved to My Looks' : 'Save Look'}
        </button>
        <button
          type="button"
          className="studio-primary-button"
          disabled={busy}
          onClick={() => void run(true)}
        >
          {bookLabel}
        </button>
      </div>
      {saved && <p role="status">Saved to your account. You can find it in My Saved Looks.</p>}
      {error && (
        <p role="alert" className="studio-alert">
          {error} Your preview and download remain available.
        </p>
      )}
    </div>
  );
}
