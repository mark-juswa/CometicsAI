"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { saveLook, type SavedLook } from "../lib/business/client";
import type { FeatureId, GeneratedResult } from "../lib/ai/browser-client";
export function SavedLookActions({
  feature,
  result,
  sourceKind = "manual",
  bookLabel = "Book This Look",
}: {
  feature: FeatureId;
  result: GeneratedResult;
  sourceKind?: "manual" | "consultation";
  bookLabel?: string;
}) {
  const router = useRouter();
  const [savedResult, setSavedResult] = useState<{
    key: string;
    look: SavedLook;
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const lock = useRef(false);
  const resultKey = `${feature}:${result.style.id}:${result.image.data_url}`;
  const saved = savedResult?.key === resultKey ? savedResult.look : null;
  const latestKey = useRef(resultKey);
  latestKey.current = resultKey;
  useEffect(() => {
    setSavedResult(null);
    setError("");
  }, [resultKey]);
  async function run(book: boolean) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    const current = result;
    const currentKey = resultKey;
    try {
      const look = saved ?? (await saveLook(feature, current, sourceKind));
      if (latestKey.current !== currentKey) return;
      setSavedResult({ key: currentKey, look });
      if (book) router.push(`/booking?look=${encodeURIComponent(look.id)}`);
    } catch (cause) {
      if (latestKey.current === currentKey)
        setError(
          cause instanceof Error ? cause.message : "Could not save this look.",
        );
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  if (result.status !== "completed") return null;
  return (
    <div className="saved-look-actions">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className="studio-secondary-button"
          disabled={busy || !!saved}
          onClick={() => void run(false)}
        >
          {busy ? "Saving…" : saved ? "Saved to My Looks" : "Save Look"}
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
      {saved && (
        <p role="status">
          Saved to your account. You can find it in My Saved Looks.
        </p>
      )}
      {error && (
        <p role="alert" className="studio-alert">
          {error} Your preview and download remain available.
        </p>
      )}
    </div>
  );
}
