"use client";
import { PortalWorkspace } from "@/components/portal-workspace";
import {
  History,
  ShieldCheck,
  ArrowRight,
  ImageIcon,
  Sparkles,
  Download,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { businessRequest } from "@/lib/business/client";
import {
  Card,
  PageHeader,
  Skeleton,
  EmptyState,
  formatDate,
} from "@/components/ui";
type Session = {
  id: string;
  feature: string;
  createdAt: string;
  uploads: number;
  results: number;
  snapshot?: {
    messages?: { role: string; content: string }[];
    selected_recommendation_id?: string;
  };
};
type Asset = {
  id: string;
  name: string;
  imageUrl: string;
  savedAt?: string | null;
  recommendationId?: string;
};
export function ConsultationHistory({ sessionId }: { sessionId?: string }) {
  const [sessions, setSessions] = useState<Session[]>([]),
    [session, setSession] = useState<Session | null>(null),
    [uploads, setUploads] = useState<Asset[]>([]),
    [results, setResults] = useState<Asset[]>([]),
    [page, setPage] = useState(1),
    [total, setTotal] = useState(0),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState("");
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    businessRequest(
      sessionId
        ? `/api/consultation-history/${sessionId}`
        : `/api/consultation-history?page=${page}`,
    )
      .then((d) => {
        if (!active) return;
        if (sessionId) {
          setSession(d.session);
          setUploads(d.uploads);
          setResults(d.results);
        } else {
          setSessions(d.sessions);
          setTotal(d.total);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [sessionId, page]);
  async function save(asset: Asset) {
    if (busy) return;
    setBusy(asset.id);
    setError("");
    try {
      await businessRequest(`/api/saved-looks/${asset.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ saved: true }),
      });
      setResults((old) =>
        old.map((row) =>
          row.id === asset.id
            ? { ...row, savedAt: new Date().toISOString() }
            : row,
        ),
      );
      setMessage(
        "Look saved. You can reuse it as a reference in a new consultation.",
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save.");
    } finally {
      setBusy("");
    }
  }
  return (
    <PortalWorkspace className="history-workspace">
      <header className="portal-hero">
        <div>
          <p className="portal-eyebrow">Your private beauty journal</p>
          <h1>
            {sessionId ? "Previous Consultation" : "Consultation History"}
          </h1>
          <p>
            Your uploaded photos, conversation, and generated results are
            private to your account.
          </p>
        </div>
        <Link
          className="portal-button portal-primary"
          href="/client/ai-consultation"
        >
          New consultation
          <ArrowRight size={15} />
        </Link>
      </header>
      {sessionId && (
        <Link
          className="mb-5 inline-block text-sm text-gold underline"
          href="/client/consultation-history"
        >
          ← All consultations
        </Link>
      )}
      {error && (
        <p role="alert" className="portal-alert">
          {error}
        </p>
      )}
      {message && (
        <p role="status" className="portal-notice">
          {message}
        </p>
      )}
      {loading ? (
        <Skeleton className="h-64 w-full" />
      ) : sessionId && session ? (
        <div className="space-y-6">
          <Card>
            <h2 className="font-serif text-xl capitalize">
              {session.feature} · {formatDate(session.createdAt)}
            </h2>
            <p className="mt-2 text-sm text-muted">
              These are archived records. Choose an existing image inside a new
              consultation to generate another look.
            </p>
          </Card>
          <Card>
            <h2 className="mb-4 font-serif text-xl">Uploaded references</h2>
            {uploads.length === 0 ? (
              <p className="text-muted">
                No photo was uploaded in this consultation.
              </p>
            ) : (
              <div className="history-assets grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {uploads.map((asset) => (
                  <figure key={asset.id}>
                    <a href={asset.imageUrl} target="_blank" rel="noreferrer">
                      <img
                        src={asset.imageUrl}
                        alt={asset.name}
                        className="aspect-square w-full rounded object-contain bg-deep"
                      />
                    </a>
                    <figcaption className="mt-2 break-words text-sm">
                      {asset.name}
                    </figcaption>
                  </figure>
                ))}
              </div>
            )}
          </Card>
          <Card>
            <h2 className="mb-4 font-serif text-xl">Generated looks</h2>
            {results.length === 0 ? (
              <p className="text-muted">
                No completed result was archived for this consultation.
              </p>
            ) : (
              <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {results.map((asset) => (
                  <article
                    key={asset.id + asset.recommendationId}
                    className="rounded border border-purple-light/20 p-3"
                  >
                    <a href={asset.imageUrl} target="_blank" rel="noreferrer">
                      <img
                        src={asset.imageUrl}
                        alt={asset.name}
                        className="aspect-square w-full rounded object-contain bg-deep"
                      />
                    </a>
                    <h3 className="my-3 text-lg">{asset.name}</h3>
                    {session.snapshot?.selected_recommendation_id ===
                      asset.recommendationId && (
                      <p className="mb-2 text-xs text-gold">
                        Selected in this consultation
                      </p>
                    )}
                    <div className="flex flex-wrap gap-2">
                      <a
                        className="studio-secondary-button inline-flex items-center gap-2"
                        href={asset.imageUrl + "?download=1"}
                        download
                        aria-label={"Download " + asset.name}
                      >
                        <Download size={14} />
                        Download image
                      </a>
                      <button
                        type="button"
                        className="studio-secondary-button"
                        disabled={!!busy || !!asset.savedAt}
                        onClick={() => void save(asset)}
                      >
                        {busy === asset.id
                          ? "Saving…"
                          : asset.savedAt
                            ? "Saved to My Looks"
                            : "Save Look"}
                      </button>
                    </div>
                    <p className="mt-3 text-xs leading-relaxed text-muted">
                      Download this image to upload it in another AI
                      consultation.
                    </p>
                  </article>
                ))}
              </div>
            )}
          </Card>
          <Card>
            <h2 className="mb-4 font-serif text-xl">Conversation</h2>
            {session.snapshot?.messages?.length ? (
              <ol className="history-conversation space-y-4">
                {session.snapshot.messages.map((item, index) => (
                  <li
                    key={index}
                    data-author={item.role}
                    className="rounded border border-purple-light/15 p-4"
                  >
                    <span className="text-xs font-medium uppercase text-gold">
                      {item.role === "user" ? "You" : "Beauty consultation"}
                    </span>
                    <p className="mt-2 whitespace-pre-wrap text-sm text-secondary">
                      {item.content}
                    </p>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="text-muted">
                This consultation did not include a conversation.
              </p>
            )}
          </Card>
        </div>
      ) : !sessionId ? (
        <>
          <section className="portal-panel">
            <div className="portal-panel-heading">
              <div>
                <h2 className="flex items-center gap-2">
                  <History size={20} className="text-gold" />
                  Your consultations
                </h2>
                <p>
                  {error
                    ? "Your archived conversations"
                    : total +
                      " archived " +
                      (total === 1 ? "consultation" : "consultations")}{" "}
                  · open a record to revisit photos, looks, and messages.
                </p>
              </div>
              <span className="portal-pill">
                <ShieldCheck size={13} className="mr-1.5" />
                Private archive
              </span>
            </div>
            <div className="portal-inset">
              <div className="grid auto-rows-fr gap-5 md:grid-cols-2 xl:grid-cols-3">
                {sessions.map((row) => (
                  <Link
                    key={row.id}
                    href={"/client/consultation-history/" + row.id}
                    className="history-card"
                  >
                    <span className="mb-5 inline-flex h-11 w-11 items-center justify-center rounded-xl border border-gold/25 bg-gold/5 text-gold">
                      <Sparkles size={20} />
                    </span>
                    <p className="mb-2 text-[10px] uppercase tracking-wide text-muted">
                      {formatDate(row.createdAt)}
                    </p>
                    <h2 className="capitalize">
                      {row.feature === "hairstyle"
                        ? "Hair"
                        : row.feature === "nails"
                          ? "Nail"
                          : row.feature}{" "}
                      consultation
                    </h2>
                    <div className="my-5 flex flex-wrap gap-2">
                      <span className="portal-pill">
                        <ImageIcon size={12} className="mr-1.5" />
                        {row.uploads} reference photos
                      </span>
                      <span className="portal-pill">
                        {row.results} generated looks
                      </span>
                    </div>
                    <span className="mt-auto flex items-center justify-between border-t border-purple-light/15 pt-4 text-xs text-gold">
                      View consultation
                      <ArrowRight size={15} />
                    </span>
                  </Link>
                ))}
              </div>
              {sessions.length === 0 && !error && (
                <EmptyState
                  icon={History}
                  title="No consultation history yet"
                  body="New consultations and their uploaded photos will appear here. Earlier temporary AI sessions cannot be recovered after they have expired."
                />
              )}
            </div>
            <nav
              aria-label="Consultation history pagination"
              className="portal-pagination"
            >
              <span>
                Page {page} of {Math.max(1, Math.ceil(total / 12))} · {total}{" "}
                consultations
              </span>
              <div>
                <button
                  className="portal-button"
                  disabled={loading || !!error || page === 1}
                  onClick={() => setPage(page - 1)}
                >
                  Previous
                </button>
                <button
                  className="portal-button"
                  disabled={loading || !!error || page * 12 >= total}
                  onClick={() => setPage(page + 1)}
                >
                  Next
                </button>
              </div>
            </nav>
          </section>
        </>
      ) : null}
    </PortalWorkspace>
  );
}
