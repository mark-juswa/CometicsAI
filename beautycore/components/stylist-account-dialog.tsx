"use client";
import { useEffect, useRef, useState } from "react";
import { Loader2, Save, UserPlus, X } from "lucide-react";
import { businessRequest } from "@/lib/business/client";
import type { RevenueStylist } from "@/lib/business/revenue-periods";
import { serviceGroups } from "@/lib/services";
const specialties = [
  ...new Map(
    serviceGroups.map((group) => [group.serviceType, group.label]),
  ).entries(),
];
export function StylistAccountDialog({
  stylist,
  onClose,
  onSaved,
}: {
  stylist: RevenueStylist | null;
  onClose: () => void;
  onSaved: (message: string) => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null),
    lock = useRef(false);
  const [draft, setDraft] = useState({
      name: stylist?.name ?? "",
      email: stylist?.email ?? "",
      password: "",
      isActive: stylist?.isActive ?? true,
      specialties: stylist?.specialties ?? ([] as string[]),
    }),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    const element = dialog.current;
    element?.showModal();
    return () => element?.close();
  }, []);
  async function save(event: React.FormEvent) {
    event.preventDefault();
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      await businessRequest("/api/stylists", {
        method: stylist ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          stylist
            ? {
                id: stylist.id,
                name: draft.name,
                email: draft.email,
                isActive: draft.isActive,
                specialties: draft.specialties,
              }
            : {
                name: draft.name,
                email: draft.email,
                password: draft.password,
                specialties: draft.specialties,
              },
        ),
      });
      onSaved(
        stylist
          ? "Stylist details saved."
          : "Stylist account created. They can set working hours and availability in their dashboard.",
      );
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Could not save this account.",
      );
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  return (
    <dialog
      ref={dialog}
      aria-labelledby="stylist-dialog-title"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
      className="fixed inset-0 m-auto max-h-[90dvh] overflow-y-auto rounded-xl border border-purple-light/25 bg-card p-5 text-white shadow-2xl backdrop:bg-black/70 sm:p-7"
      style={{ width: "min(36rem, calc(100vw - 2rem))" }}
    >
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <p className="mb-2 text-[10px] uppercase tracking-[2px] text-gold">
            Team management
          </p>
          <h2 id="stylist-dialog-title" className="font-serif text-2xl">
            {stylist ? "Edit stylist" : "Add a stylist"}
          </h2>
          <p className="mt-2 text-xs text-muted">
            {stylist
              ? "Update account details and service qualifications."
              : "Create a staff login and assign their qualified services."}
          </p>
        </div>
        <button
          type="button"
          aria-label="Close stylist form"
          disabled={busy}
          onClick={onClose}
          className="rounded-lg p-2 text-muted hover:bg-surface"
        >
          <X size={18} />
        </button>
      </div>
      {error && (
        <p
          role="alert"
          className="mb-4 rounded border border-error/30 p-3 text-sm text-error"
        >
          {error}
        </p>
      )}
      <form onSubmit={save}>
        <fieldset disabled={busy} className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="text-xs text-secondary">
              Full name
              <input
                required
                maxLength={255}
                value={draft.name}
                onChange={(e) => setDraft({ ...draft, name: e.target.value })}
              />
            </label>
            <label className="text-xs text-secondary">
              Email address
              <input
                required
                type="email"
                maxLength={255}
                value={draft.email}
                onChange={(e) => setDraft({ ...draft, email: e.target.value })}
              />
            </label>
          </div>
          {!stylist && (
            <label className="block text-xs text-secondary">
              Temporary password
              <input
                required
                autoComplete="new-password"
                minLength={8}
                maxLength={128}
                type="password"
                value={draft.password}
                onChange={(e) =>
                  setDraft({ ...draft, password: e.target.value })
                }
              />
              <span className="mt-2 block text-[11px] text-muted">
                At least 8 characters. Share it directly with the stylist.
              </span>
            </label>
          )}
          <fieldset>
            <legend className="mb-3 text-xs font-medium text-secondary">
              Qualified services
            </legend>
            <div className="grid gap-2 sm:grid-cols-2">
              {specialties.map(([value, label]) => (
                <label
                  key={value}
                  className={`flex cursor-pointer items-center gap-2 rounded-lg border p-3 text-xs ${draft.specialties.includes(value) ? "border-purple-light/40 bg-purple/10 text-white" : "border-purple-light/15 text-muted"}`}
                >
                  <input
                    type="checkbox"
                    checked={draft.specialties.includes(value)}
                    onChange={() =>
                      setDraft({
                        ...draft,
                        specialties: draft.specialties.includes(value)
                          ? draft.specialties.filter((type) => type !== value)
                          : [...draft.specialties, value],
                      })
                    }
                  />
                  {label}
                </label>
              ))}
            </div>
          </fieldset>
          {stylist && (
            <label className="flex items-center gap-3 rounded-lg border border-purple-light/20 p-3 text-sm">
              <input
                type="checkbox"
                checked={draft.isActive}
                onChange={(e) =>
                  setDraft({ ...draft, isActive: e.target.checked })
                }
              />
              <span>
                Active account
                <span className="mt-1 block text-xs text-muted">
                  Inactive accounts cannot sign in or accept new bookings.
                  Existing history is kept.
                </span>
              </span>
            </label>
          )}
          <div className="flex flex-wrap items-center justify-end gap-3 border-t border-purple-light/15 pt-4">
            <button
              type="button"
              className="studio-secondary-button"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="inline-flex items-center gap-2 rounded-lg bg-gold px-5 py-2.5 text-sm font-semibold text-deep hover:bg-gold-hover disabled:opacity-50"
            >
              {busy ? (
                <Loader2 size={15} className="animate-spin" />
              ) : stylist ? (
                <Save size={15} />
              ) : (
                <UserPlus size={15} />
              )}{" "}
              {busy
                ? "Saving…"
                : stylist
                  ? "Save changes"
                  : "Create stylist account"}
            </button>
          </div>
        </fieldset>
      </form>
    </dialog>
  );
}
