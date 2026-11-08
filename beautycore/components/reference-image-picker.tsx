"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { businessRequest } from "@/lib/business/client";
type ImageRow = {
  id: string;
  kind: "uploaded" | "generated";
  name: string;
  imageUrl: string;
  createdAt: string;
};
export function ReferenceImagePicker({
  disabled = false,
  onSelect,
  purpose = "your new consultation",
}: {
  disabled?: boolean;
  onSelect: (file: File) => void;
  purpose?: string;
}) {
  const [open, setOpen] = useState(false),
    [rows, setRows] = useState<ImageRow[]>([]),
    [kind, setKind] = useState("all"),
    [page, setPage] = useState(1),
    [total, setTotal] = useState(0),
    [selected, setSelected] = useState<ImageRow | null>(null),
    [loading, setLoading] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    if (!open) return;
    let active = true;
    setLoading(true);
    setError("");
    setSelected(null);
    businessRequest(`/api/client-images?kind=${kind}&page=${page}`)
      .then((d) => {
        if (active) {
          setRows(d.images);
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
  }, [open, kind, page]);
  async function useImage() {
    if (!selected || busy) return;
    setBusy(true);
    setError("");
    try {
      const response = await fetch(selected.imageUrl, { cache: "no-store" });
      if (!response.ok) throw Error("This private image could not be loaded.");
      const blob = await response.blob();
      if (
        !["image/png", "image/jpeg"].includes(blob.type) ||
        blob.size > 8 * 1024 * 1024
      )
        throw Error("Choose a PNG or JPEG up to 8 MB.");
      onSelect(
        new File(
          [blob],
          selected.name.replace(/[^a-zA-Z0-9._ -]/g, "_") +
            (blob.type === "image/png" ? ".png" : ".jpg"),
          { type: blob.type },
        ),
      );
      setOpen(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not use this image.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="mt-4 border-t border-purple-light/20 pt-4">
      <button
        type="button"
        disabled={disabled}
        className="studio-secondary-button"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        {open ? "Close saved images" : "Choose an existing image"}
      </button>
      <Link
        className="mt-3 block text-sm text-gold underline"
        href="/client/consultation-history"
      >
        View consultation history
      </Link>
      {open && (
        <div className="mt-4 space-y-4">
          <label className="block text-sm">
            Image category
            <select
              className="mt-1 w-full rounded border border-purple-light/30 bg-card p-2"
              value={kind}
              onChange={(e) => {
                setKind(e.target.value);
                setPage(1);
              }}
            >
              <option value="all">All saved images</option>
              <option value="uploaded">Uploaded reference images</option>
              <option value="generated">AI-generated saved looks</option>
            </select>
          </label>
          {error && (
            <p role="alert" className="text-sm text-error">
              {error}
            </p>
          )}
          {loading ? (
            <p role="status">Loading your private images…</p>
          ) : rows.length === 0 ? (
            <p className="text-sm text-muted">
              No images in this category yet. Upload a photo or save a generated
              look to reuse it here.
            </p>
          ) : (
            <div className="grid grid-cols-2 gap-2">
              {rows.map((row) => (
                <button
                  type="button"
                  key={row.kind + row.id}
                  aria-pressed={
                    selected?.id === row.id && selected?.kind === row.kind
                  }
                  disabled={disabled || busy}
                  className={`overflow-hidden rounded border p-2 text-left ${selected?.id === row.id && selected?.kind === row.kind ? "border-gold" : "border-purple-light/20"}`}
                  onClick={() => setSelected(row)}
                >
                  <img
                    src={row.imageUrl}
                    alt={row.name}
                    loading="lazy"
                    className="aspect-square w-full rounded object-cover"
                  />
                  <span className="mt-2 block text-xs text-gold">
                    {row.kind === "uploaded"
                      ? "Uploaded reference"
                      : "AI-generated look"}
                  </span>
                  <span className="block truncate text-xs">{row.name}</span>
                </button>
              ))}
            </div>
          )}
          {selected && (
            <div className="rounded border border-gold/30 p-3">
              <img
                src={selected.imageUrl}
                alt={`Preview of ${selected.name}`}
                className="max-h-64 w-full object-contain"
              />
              <p className="my-3 text-sm">
                This image will become the reference photo for {purpose}.
              </p>
              <button
                type="button"
                className="studio-primary-button"
                disabled={disabled || busy}
                onClick={() => void useImage()}
              >
                {busy ? "Loading image…" : "Use this image"}
              </button>
            </div>
          )}
          <div className="flex items-center justify-between gap-2 text-sm">
            <button
              type="button"
              className="studio-text-button"
              disabled={page === 1 || loading}
              onClick={() => setPage(page - 1)}
            >
              Previous
            </button>
            <span>Page {page}</span>
            <button
              type="button"
              className="studio-text-button"
              disabled={page * 12 >= total || loading}
              onClick={() => setPage(page + 1)}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
