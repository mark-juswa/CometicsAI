"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  Bell,
  ArrowRight,
  CalendarDays,
  Check,
  RefreshCw,
  X,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { businessRequest } from "@/lib/business/client";
import type { BookingNotification } from "@/lib/business/booking-notifications";
import { formatDate, formatTime } from "./ui";

export function BookingNotifications() {
  const { user } = useAuth();
  if (!user || !["client", "stylist"].includes(user.role)) return null;
  return (
    <AccountBookingNotifications
      key={user.role + ":" + user.id}
      owner={{ id: user.id, role: user.role }}
    />
  );
}
function AccountBookingNotifications({
  owner,
}: {
  owner: { id: string; role: string };
}) {
  const [rows, setRows] = useState<BookingNotification[]>([]),
    [seen, setSeen] = useState<string[]>([]),
    [total, setTotal] = useState(0),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [open, setOpen] = useState(false),
    [revision, setRevision] = useState(0);
  const panel = useRef<HTMLDivElement>(null);
  const storage = owner
    ? `beautycore:booking-alerts:v1:${owner.role}:${owner.id}`
    : "";
  useEffect(() => {
    setRows([]);
    setTotal(0);
    setOpen(false);
    setLoading(true);
    setError("");
    try {
      const stored = JSON.parse(localStorage.getItem(storage) || "[]");
      setSeen(
        Array.isArray(stored)
          ? stored.filter((value) => typeof value === "string").slice(-200)
          : [],
      );
    } catch {
      setSeen([]);
    }
  }, [storage]);
  useEffect(() => {
    if (!owner) return;
    let stopped = false;
    let controller: AbortController | undefined;
    async function load() {
      controller?.abort();
      controller = new AbortController();
      const signal = controller.signal;
      try {
        const data = await businessRequest("/api/booking-notifications", {
          signal,
        });
        if (
          stopped ||
          signal.aborted ||
          data.ownerId !== owner!.id ||
          data.role !== owner!.role
        )
          return;
        setRows(data.notifications ?? []);
        setTotal(data.total ?? 0);
        setError("");
      } catch (cause) {
        if (!stopped && !signal.aborted)
          setError(
            cause instanceof Error
              ? cause.message
              : "Notifications unavailable.",
          );
      } finally {
        if (!stopped && !signal.aborted) setLoading(false);
      }
    }
    const refresh = () => {
      if (document.visibilityState === "visible") void load();
    };
    void load();
    const timer = window.setInterval(refresh, 30000);
    window.addEventListener("focus", refresh);
    document.addEventListener("visibilitychange", refresh);
    window.addEventListener("appointments-updated", refresh);
    const sync = (event: StorageEvent) => {
      if (event.key !== storage) return;
      try {
        const value = JSON.parse(event.newValue || "[]");
        if (Array.isArray(value))
          setSeen(value.filter((item) => typeof item === "string").slice(-200));
      } catch {}
    };
    window.addEventListener("storage", sync);
    return () => {
      stopped = true;
      controller?.abort();
      window.clearInterval(timer);
      window.removeEventListener("focus", refresh);
      document.removeEventListener("visibilitychange", refresh);
      window.removeEventListener("appointments-updated", refresh);
      window.removeEventListener("storage", sync);
    };
  }, [owner?.id, owner?.role, storage, revision]);
  useEffect(() => {
    if (!open) return;
    const outside = (event: PointerEvent) => {
      if (!panel.current?.contains(event.target as Node)) setOpen(false);
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", outside);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("pointerdown", outside);
      document.removeEventListener("keydown", escape);
    };
  }, [open]);
  if (!owner) return null;
  const unread = rows.filter((row) => !seen.includes(row.key)),
    first = unread[0] ?? rows[0],
    base = `/${owner.role}/appointments`;
  const mark = (keys: string[]) => {
    setSeen((previous) => {
      const next = [...new Set([...previous, ...keys])].slice(-200);
      try {
        localStorage.setItem(storage, JSON.stringify(next));
      } catch {}
      return next;
    });
  };
  const visit = (row: BookingNotification) => {
    mark([row.key]);
    setOpen(false);
    window.dispatchEvent(new Event("appointments-updated"));
    window.dispatchEvent(
      new CustomEvent("booking-notification-open", { detail: row.id }),
    );
  };
  return (
    <div
      ref={panel}
      className="booking-notification-bar"
      aria-label="Booking notifications"
    >
      <div className="booking-notification-inner">
        <CalendarDays size={19} className="shrink-0 text-gold" />
        <div className="min-w-0 flex-1">
          {loading ? (
            <p className="text-xs text-muted">Loading booking updates…</p>
          ) : error ? (
            <div className="flex items-center gap-2 text-xs text-warning">
              <span>Booking updates unavailable</span>
              <button
                type="button"
                aria-label="Retry booking notifications"
                onClick={() => setRevision((value) => value + 1)}
              >
                <RefreshCw size={13} />
              </button>
            </div>
          ) : first ? (
            <Link
              href={`${base}#booking-${first.id}`}
              onClick={() => visit(first)}
              className="block min-w-0"
            >
              <p className="truncate text-xs font-medium text-white">
                {unread.length
                  ? `${unread.length} unread booking ${unread.length === 1 ? "update" : "updates"}`
                  : `${total} upcoming ${total === 1 ? "booking" : "bookings"}`}
              </p>
              <p className="mt-1 truncate text-[11px] text-secondary">
                {first.serviceName} · {formatDate(first.appointmentDate)} ·{" "}
                {formatTime(first.appointmentDate)}
              </p>
            </Link>
          ) : (
            <Link href={base} className="text-xs text-secondary">
              No upcoming bookings · View appointments
            </Link>
          )}
        </div>
        <button
          type="button"
          aria-label={`Booking notifications${unread.length ? `, ${unread.length} unread` : ""}`}
          aria-expanded={open}
          aria-controls="booking-notification-list"
          onClick={() => setOpen((value) => !value)}
          className="booking-notification-bell"
        >
          <Bell size={18} />
          {unread.length > 0 && <span>{unread.length}</span>}
        </button>
      </div>
      {open && (
        <section
          id="booking-notification-list"
          aria-label="Your booking updates"
          className="booking-notification-list"
        >
          <div className="flex items-center justify-between gap-3 border-b border-purple-light/20 p-4">
            <h2 className="font-serif text-xl text-white">Booking updates</h2>
            <button
              type="button"
              aria-label="Close booking notifications"
              onClick={() => setOpen(false)}
            >
              <X size={18} />
            </button>
          </div>
          <p className="px-4 py-3 text-xs text-muted">
            Upcoming bookings and assignment updates. Checks refresh every 30
            seconds while this page is visible.
          </p>
          <div className="max-h-[50dvh] overflow-y-auto">
            {rows.map((row) => (
              <Link
                key={row.key}
                href={`${base}#booking-${row.id}`}
                onClick={() => visit(row)}
                className="booking-notification-item"
              >
                <span
                  className={`mt-1 h-2 w-2 shrink-0 rounded-full ${seen.includes(row.key) ? "bg-purple-light/25" : "bg-gold"}`}
                />
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-white">{row.serviceName}</p>
                  <p className="mt-1 text-xs text-secondary">
                    {owner.role === "client"
                      ? row.status === "pending"
                        ? "Booking received · awaiting assignment"
                        : "Booking confirmed"
                      : "Assigned to you"}
                    {row.otherName ? " · " + row.otherName : ""}
                  </p>
                  <p className="mt-1 text-[11px] text-muted">
                    {formatDate(row.appointmentDate)} ·{" "}
                    {formatTime(row.appointmentDate)}
                  </p>
                </div>
                <ArrowRight size={14} className="mt-1 text-gold" />
              </Link>
            ))}
            {!rows.length && (
              <p className="p-5 text-sm text-muted">
                {error
                  ? "Could not load booking updates."
                  : loading
                    ? "Loading…"
                    : "No upcoming bookings yet."}
              </p>
            )}
          </div>
          {unread.length > 0 && (
            <button
              type="button"
              onClick={() => mark(rows.map((row) => row.key))}
              className="flex w-full items-center justify-center gap-2 border-t border-purple-light/20 px-4 py-3 text-xs text-gold"
            >
              <Check size={14} />
              Mark displayed updates as read
            </button>
          )}
          <p className="border-t border-purple-light/15 px-4 py-3 text-[11px] text-muted">
            Read status is saved in this browser.
          </p>
        </section>
      )}
      <span className="sr-only" role="status" aria-live="polite">
        {!loading && !error && unread.length
          ? `${unread.length} unread booking updates`
          : ""}
      </span>
    </div>
  );
}
