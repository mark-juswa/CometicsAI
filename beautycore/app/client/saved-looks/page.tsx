"use client";
import { PortalWorkspace } from "@/components/portal-workspace";
import { LookInformation } from "@/components/look-information";
import { featureFromType } from "@/lib/business/look-information";
import Image from "next/image";
import {
  Heart,
  ArrowRight,
  Download,
  ImageIcon,
  ShieldCheck,
  SlidersHorizontal,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { PageHeader, Card, Skeleton, EmptyState } from "@/components/ui";
import { businessRequest, type SavedLook } from "@/lib/business/client";
export default function SavedLooksPage() {
  const [looks, setLooks] = useState<SavedLook[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [feature, setFeature] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [busy, setBusy] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    const params = new URLSearchParams({ page: String(page) });
    if (feature) params.set("feature", feature);
    if (from) params.set("from", from);
    if (to) params.set("to", to);
    businessRequest("/api/saved-looks?" + params, { signal: controller.signal })
      .then((data) => {
        if (controller.signal.aborted) return;
        setLooks(data.looks);
        setTotal(data.total);
        if (!data.looks.length && page > 1) setPage(page - 1);
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setError(cause.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [page, feature, from, to, refresh]);
  async function remove(look: SavedLook) {
    if (
      !confirm(
        "Remove from My Saved Looks? Existing appointments will keep this reference for your stylist.",
      )
    )
      return;
    setBusy(look.id);
    setError("");
    try {
      await businessRequest(`/api/saved-looks/${look.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ saved: false }),
      });
      setRefresh((v) => v + 1);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Could not remove the look.",
      );
    } finally {
      setBusy("");
    }
  }
  return (
    <PortalWorkspace className="looks-workspace">
      <header className="portal-hero">
        <div>
          <p className="portal-eyebrow">Your personal lookbook</p>
          <h1>My Saved Looks</h1>
          <p>
            Your favourite previews, ready to revisit or bring to your next
            appointment.
          </p>
        </div>
        <Link
          href="/client/ai-consultation"
          className="portal-button portal-primary"
        >
          Explore a new look
          <ArrowRight size={15} />
        </Link>
      </header>
      <section className="portal-panel">
        <div className="portal-panel-heading">
          <div>
            <h2 className="flex items-center gap-2">
              <Heart size={20} className="text-gold" />
              Your collection
            </h2>
            <p>
              {loading
                ? "Loading your collection…"
                : error
                  ? "Your saved previews"
                  : total + " saved " + (total === 1 ? "look" : "looks")}
            </p>
          </div>
          <span className="portal-pill">
            <ShieldCheck size={13} className="mr-1.5" />
            Private to you
          </span>
        </div>
        <div className="portal-toolbar">
          <label className="text-xs text-secondary">
            Feature
            <select
              value={feature}
              onChange={(e) => {
                setFeature(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All features</option>
              <option value="hairstyle">Hairstyle</option>
              <option value="makeup">Makeup</option>
              <option value="nails">Nails</option>
            </select>
          </label>
          <label className="text-xs text-secondary">
            Saved from
            <input
              type="date"
              value={from}
              onChange={(e) => {
                setFrom(e.target.value);
                setPage(1);
              }}
            />
          </label>
          <label className="text-xs text-secondary">
            Saved through
            <input
              type="date"
              value={to}
              onChange={(e) => {
                setTo(e.target.value);
                setPage(1);
              }}
            />
          </label>
          <button
            className="portal-button self-end"
            onClick={() => {
              setFeature("");
              setFrom("");
              setTo("");
              setPage(1);
            }}
          >
            Clear filters
          </button>
        </div>
        <p className="border-t border-purple-light/10 px-6 py-4 text-xs leading-relaxed text-muted">
          Removing a look from this gallery keeps it attached to appointments
          already booked.
        </p>
      </section>
      {error && (
        <p role="alert" className="portal-alert">
          {error}
        </p>
      )}
      {loading ? (
        <div className="saved-gallery">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-96 w-full" />
          ))}
        </div>
      ) : error ? null : !looks.length ? (
        <EmptyState
          icon={Heart}
          title={
            feature || from || to
              ? "No saved looks match"
              : "Your lookbook starts here"
          }
          body={
            feature || from || to
              ? "Try another feature or clear your date filters."
              : "Save a completed preview from a studio or consultation to keep it here."
          }
          action={
            <Link
              href="/client/ai-consultation"
              className="portal-button portal-primary"
            >
              Start a consultation
              <ArrowRight size={14} />
            </Link>
          }
        />
      ) : (
        <div className="saved-gallery">
          {looks.map((look) => (
            <article key={look.id} className="lookbook-card">
              <div className="lookbook-image">
                <Image
                  src={look.imageUrl}
                  fill
                  unoptimized
                  sizes="(max-width: 700px) 100vw, (max-width: 1200px) 50vw, 33vw"
                  alt={look.styleName}
                  className="object-contain"
                />
                <span className="lookbook-feature">
                  {look.styleType === "nail"
                    ? "Nails"
                    : look.styleType === "hair"
                      ? "Hairstyle"
                      : "Makeup"}
                </span>
              </div>
              <div className="p-5">
                <p className="mb-2 text-[10px] uppercase tracking-wider text-muted">
                  Saved{" "}
                  {new Date(look.savedAt).toLocaleDateString("en-PH", {
                    timeZone: "Asia/Manila",
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </p>
                <h2 className="font-serif text-2xl text-white">
                  {look.styleName}
                </h2>
                <details className="my-4 rounded-lg border border-purple-light/15 p-3">
                  <summary className="cursor-pointer text-xs text-secondary">
                    Style details & service estimates
                  </summary>
                  <LookInformation
                    saved
                    feature={featureFromType(look.styleType)}
                    styleId={look.styleId}
                    details={look.lookDetails}
                  />
                </details>
                <Link
                  className="portal-button portal-primary w-full"
                  href={"/booking?look=" + look.id}
                >
                  Book This Look
                  <ArrowRight size={14} />
                </Link>
                <div className="mt-3 flex flex-wrap gap-2">
                  <a
                    className="portal-button flex-1"
                    href={look.imageUrl}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <ImageIcon size={13} />
                    View image
                  </a>
                  <a
                    className="portal-button flex-1"
                    href={look.imageUrl}
                    download={"andreas-" + look.styleId}
                  >
                    <Download size={13} />
                    Download
                  </a>
                </div>
                <button
                  className="mt-4 w-full text-xs text-muted underline underline-offset-4 hover:text-error disabled:opacity-50"
                  disabled={!!busy}
                  onClick={() => void remove(look)}
                >
                  {busy === look.id ? "Removing…" : "Remove from Saved"}
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
      <nav
        aria-label="Saved looks pagination"
        className="portal-pagination mt-6"
      >
        <span>
          Page {page} · {total} saved looks
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
    </PortalWorkspace>
  );
}
