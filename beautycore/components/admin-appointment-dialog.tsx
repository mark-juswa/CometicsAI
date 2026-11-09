"use client";
import { ServiceControls } from "@/components/service-controls";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  CalendarDays,
  Clock,
  ExternalLink,
  Loader2,
  Scissors,
  Trash2,
  UserRound,
  X,
  XCircle,
} from "lucide-react";
import { AdminBookingControls } from "./admin-booking-controls";
import { AppointmentLookPreview } from "./appointment-look";
import { AppointmentServiceRecord } from "./appointment-service-record";
import { ServiceCompletion } from "./service-completion";
import { StatusBadge, formatDate, formatTime, formatPeso } from "./ui";
import { businessRequest } from "@/lib/business/client";
import {
  activeAppointment,
  appointmentTimeInput,
  type AdminAppointment,
  type AdminStylistOption,
} from "@/lib/business/appointment-list";
import { salonDay, salonDateTime } from "@/lib/business/dates";

export function AdminAppointmentDialog({
  appointment: row,
  stylists,
  directoryReady,
  onClose,
  onChanged,
  onDeleted,
}: {
  appointment: AdminAppointment;
  stylists: AdminStylistOption[];
  directoryReady: boolean;
  onClose: () => void;
  onChanged: (message: string) => Promise<void>;
  onDeleted: (id: string) => Promise<void>;
}) {
  const dialog = useRef<HTMLDialogElement>(null),
    lock = useRef(false);
  const [busy, setBusy] = useState(false),
    [assignmentBusy, setAssignmentBusy] = useState(false),
    [completionBusy, setCompletionBusy] = useState(false),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [confirmation, setConfirmation] = useState<"cancel" | "delete" | null>(
      null,
    );
  const [notes, setNotes] = useState(row.notes ?? ""),
    [date, setDate] = useState(() => salonDay(new Date(row.appointmentDate))),
    [time, setTime] = useState(() => appointmentTimeInput(row.appointmentDate));
  const working = busy || assignmentBusy || completionBusy,
    active = activeAppointment(row);
  useEffect(() => {
    const element = dialog.current;
    element?.showModal();
    return () => element?.close();
  }, []);
  useEffect(() => setNotes(row.notes ?? ""), [row.notes]);
  useEffect(() => {
    setDate(salonDay(new Date(row.appointmentDate)));
    setTime(appointmentTimeInput(row.appointmentDate));
  }, [row.appointmentDate]);
  const choices = stylists
    .filter(
      (stylist) =>
        stylist.id === row.stylistId ||
        (stylist.isActive !== false &&
          stylist.specialties?.includes(row.serviceType)),
    )
    .map((stylist) => ({
      id: stylist.id,
      name: stylist.name,
      disabled:
        stylist.id !== row.stylistId &&
        (stylist.isActive === false || stylist.workAvailable === false),
    }));
  if (row.stylistId && !choices.some((stylist) => stylist.id === row.stylistId))
    choices.unshift({
      id: row.stylistId,
      name: row.stylist?.name ?? "Current assigned stylist",
      disabled: false,
    });
  async function change(fields: Record<string, unknown>, success: string) {
    if (lock.current || working) return;
    lock.current = true;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await businessRequest(`/api/appointments/${row.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(fields),
      });
      setConfirmation(null);
      await onChanged(success);
      setMessage(success);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Could not update this appointment.",
      );
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  async function remove() {
    if (lock.current || working) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      await businessRequest(`/api/appointments/${row.id}`, {
        method: "DELETE",
      });
      await onDeleted(row.id);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Could not delete this appointment.",
      );
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  function reschedule(event: React.FormEvent) {
    event.preventDefault();
    try {
      const value = salonDateTime(date, time);
      if (Date.parse(value) <= Date.now())
        throw Error("Choose a future date and time.");
      void change({ appointmentDate: value }, "Appointment rescheduled.");
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Choose a valid date and time.",
      );
    }
  }
  return (
    <dialog
      ref={dialog}
      aria-labelledby="appointment-detail-title"
      onCancel={(event) => {
        event.preventDefault();
        if (!working) onClose();
      }}
      className="fixed inset-0 m-auto max-h-[92dvh] overflow-y-auto rounded-xl border border-purple-light/25 bg-card p-0 text-white shadow-2xl backdrop:bg-black/70"
      style={{ width: "min(64rem, calc(100vw - 2rem))" }}
    >
      <header className="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-purple-light/15 bg-card px-5 py-5 sm:px-7">
        <div>
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-[2px] text-gold">
            Booking details · {row.id.slice(0, 8).toUpperCase()}
          </p>
          <h2 id="appointment-detail-title" className="font-serif text-2xl">
            {row.serviceName}
          </h2>
          <p className="mt-2 text-sm text-muted">
            {row.client?.name ?? "Unknown client"}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge status={row.status} />
          <button
            type="button"
            disabled={working}
            aria-label="Close appointment details"
            onClick={onClose}
            className="rounded-lg p-2 text-muted hover:bg-surface/50"
          >
            <X size={18} />
          </button>
        </div>
      </header>
      <div className="p-5 sm:p-7">
        {error && (
          <p
            role="alert"
            className="mb-5 rounded-lg border border-error/30 bg-error/10 p-3 text-sm text-error"
          >
            {error}
          </p>
        )}
        {message && (
          <p
            role="status"
            className="mb-5 rounded-lg border border-success/25 bg-success/10 p-3 text-sm text-success"
          >
            {message}
          </p>
        )}
        <div className="mb-6 grid gap-3 rounded-lg border border-purple-light/15 bg-deep/35 p-4 sm:grid-cols-3">
          <div>
            <p className="mb-2 flex items-center gap-1.5 text-[10px] uppercase tracking-wide text-muted">
              <CalendarDays size={12} />
              Scheduled visit
            </p>
            <p className="text-sm">{formatDate(row.appointmentDate)}</p>
            <p className="mt-1 text-xs text-secondary">
              {formatTime(row.appointmentDate)} · {row.durationMinutes ?? 60}{" "}
              min
            </p>
          </div>
          <div>
            <p className="mb-2 flex items-center gap-1.5 text-[10px] uppercase tracking-wide text-muted">
              <Scissors size={12} />
              Assigned stylist
            </p>
            <p className="text-sm">{row.stylist?.name ?? "Not assigned"}</p>
          </div>
          <div>
            <p className="mb-2 text-[10px] uppercase tracking-wide text-muted">
              Recorded service amount
            </p>
            <p className="font-serif text-xl text-gold">
              {row.totalPrice === null
                ? "To be confirmed"
                : formatPeso(row.totalPrice)}
            </p>
          </div>
        </div>
        <ServiceControls
          id={row.id}
          status={row.status}
          appointmentDate={row.appointmentDate}
          record={row}
          admin
          onUpdated={() => onChanged("Service status updated.")}
        />
        <div className="grid items-start gap-6 lg:grid-cols-2">
          <div className="space-y-5">
            <section className="rounded-lg border border-purple-light/15 p-4">
              <h3 className="mb-3 flex items-center gap-2 font-serif text-lg">
                <UserRound size={15} className="text-gold" />
                Customer
              </h3>
              <p className="text-sm text-white">
                {row.client?.name ?? "Unknown client"}
              </p>
              <p className="mt-1 break-all text-xs text-muted">
                {row.client?.email ?? "Email unavailable"}
              </p>
              {row.client && (
                <Link
                  href={`/admin/clients/${row.client.id}`}
                  className="mt-3 inline-flex items-center gap-1.5 text-xs text-gold underline"
                >
                  View client service history
                  <ExternalLink size={11} />
                </Link>
              )}
            </section>
            {row.look && (
              <section className="rounded-lg border border-purple-light/15 p-4">
                <h3 className="mb-3 font-serif text-lg">
                  Customer-selected look
                </h3>
                <AppointmentLookPreview look={row.look} />
              </section>
            )}
            <section className="rounded-lg border border-purple-light/15 p-4">
              <h3 className="mb-3 font-serif text-lg">Appointment notes</h3>
              {["cancelled", "no_show"].includes(row.status) ? (
                <p className="whitespace-pre-wrap text-sm text-secondary">
                  {row.notes || "No notes recorded."}
                </p>
              ) : (
                <form
                  onSubmit={(event) => {
                    event.preventDefault();
                    void change({ notes }, "Appointment notes saved.");
                  }}
                >
                  <fieldset disabled={working}>
                    <label className="block text-xs text-muted">
                      <span className="sr-only">Appointment notes</span>
                      <textarea
                        aria-label="Appointment notes"
                        rows={4}
                        maxLength={1000}
                        value={notes}
                        onChange={(event) => setNotes(event.target.value)}
                        placeholder="Requests, preferences, or service notes"
                      />
                    </label>
                    <button
                      type="submit"
                      className="studio-secondary-button mt-3"
                      disabled={working || notes === (row.notes ?? "")}
                    >
                      Save notes
                    </button>
                  </fieldset>
                </form>
              )}
            </section>
            {(row.status === "completed" ||
              row.products?.length ||
              row.review) && (
              <section className="rounded-lg border border-purple-light/15 p-4">
                <h3 className="font-serif text-lg">Service record</h3>
                <AppointmentServiceRecord record={row} />
                {row.status === "completed" && !row.completedAt && (
                  <p className="mt-3 text-xs text-muted">
                    The completion timestamp was not recorded for this
                    historical service.
                  </p>
                )}
              </section>
            )}
          </div>
          <div className="space-y-5">
            {row.status !== "cancelled" && (
              <section className="rounded-lg border border-purple-light/15 p-4">
                <h3 className="mb-2 font-serif text-lg">
                  Assignment & pricing
                </h3>
                <p className="mb-4 text-xs leading-relaxed text-muted">
                  {row.status === "completed"
                    ? "The stylist assignment is preserved for completed services. You can correct the recorded amount."
                    : "Qualified staff are listed below. Availability and schedule conflicts are checked when you save."}
                </p>
                {!directoryReady && active && (
                  <p className="mb-3 text-xs text-warning">
                    Staff assignments are temporarily locked while the stylist
                    directory is unavailable. Price corrections remain
                    available.
                  </p>
                )}
                <AdminBookingControls
                  id={row.id}
                  stylistId={row.stylistId}
                  lockedAssignment={
                    ["completed", "in_progress", "no_show"].includes(
                      row.status,
                    ) || !directoryReady
                  }
                  totalPrice={row.totalPrice}
                  stylists={choices}
                  disabled={busy || completionBusy || row.status === "no_show"}
                  onBusyChange={setAssignmentBusy}
                  onUpdated={() => onChanged("Assignment and pricing updated.")}
                />
              </section>
            )}
            {active && (
              <>
                <section className="rounded-lg border border-purple-light/15 p-4">
                  <details>
                    <summary className="cursor-pointer font-serif text-lg">
                      Reschedule booking
                    </summary>
                    <p className="my-3 text-xs leading-relaxed text-muted">
                      Choose a future time in the Philippines. The assigned
                      stylist's working hours and the full service duration will
                      be checked.
                    </p>
                    <form onSubmit={reschedule}>
                      <fieldset disabled={working} className="space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                          <label className="text-xs text-secondary">
                            New appointment date
                            <input
                              required
                              type="date"
                              min={salonDay()}
                              value={date}
                              onChange={(event) => setDate(event.target.value)}
                            />
                          </label>
                          <label className="text-xs text-secondary">
                            New appointment time
                            <input
                              required
                              type="time"
                              value={time}
                              onChange={(event) => setTime(event.target.value)}
                            />
                          </label>
                        </div>
                        <button
                          type="submit"
                          className="studio-secondary-button"
                        >
                          Save new schedule
                        </button>
                      </fieldset>
                    </form>
                  </details>
                </section>
                <section className="rounded-lg border border-purple-light/15 p-4">
                  <h3 className="mb-2 font-serif text-lg">Manage visit</h3>
                  {!row.stylistId && (
                    <p className="mb-4 text-xs text-warning">
                      Assign an available stylist before confirming or
                      completing this service.
                    </p>
                  )}
                  <div className="flex flex-wrap gap-2">
                    {row.status === "pending" && row.stylistId && (
                      <button
                        type="button"
                        disabled={working}
                        className="studio-primary-button"
                        onClick={() =>
                          void change(
                            { status: "confirmed" },
                            "Appointment confirmed.",
                          )
                        }
                      >
                        Confirm booking
                      </button>
                    )}
                    <ServiceCompletion
                      id={row.id}
                      disabled={working || !row.stylistId}
                      onBusyChange={setCompletionBusy}
                      onCompleted={() =>
                        onChanged("Service marked as completed.")
                      }
                    />
                    <button
                      type="button"
                      disabled={working}
                      onClick={() => {
                        setError("");
                        setConfirmation("cancel");
                      }}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-error/25 px-3 py-2 text-xs text-error hover:bg-error/10"
                    >
                      <XCircle size={13} />
                      Cancel appointment
                    </button>
                  </div>
                </section>
              </>
            )}
            {row.status === "cancelled" && (
              <section className="rounded-lg border border-purple-light/15 bg-deep/25 p-4">
                <h3 className="mb-2 font-serif text-lg">Cancelled booking</h3>
                <p className="text-sm text-muted">
                  The appointment details are kept in the booking history.
                  Cancelled appointments cannot be reopened or reassigned.
                </p>
              </section>
            )}
            {row.status === "completed" && (
              <p className="rounded-lg border border-success/20 bg-success/5 p-4 text-xs text-success">
                This service is complete. Its status, schedule, and stylist
                attribution are preserved.
              </p>
            )}
            {!["completed", "no_show", "in_progress"].includes(row.status) && (
              <section className="rounded-lg border border-error/15 p-4">
                <details>
                  <summary className="cursor-pointer text-xs text-muted">
                    More actions
                  </summary>
                  <p className="my-3 text-xs text-muted">
                    Cancellation keeps the booking history. Permanent deletion
                    removes this appointment record.
                  </p>
                  <button
                    type="button"
                    disabled={working}
                    onClick={() => {
                      setError("");
                      setConfirmation("delete");
                    }}
                    className="inline-flex items-center gap-2 text-xs text-error"
                  >
                    <Trash2 size={12} />
                    Delete appointment
                  </button>
                </details>
              </section>
            )}
            {confirmation && (
              <section
                aria-label={
                  confirmation === "cancel"
                    ? "Confirm appointment cancellation"
                    : "Confirm appointment deletion"
                }
                className="rounded-lg border border-error/40 bg-error/10 p-4"
              >
                <h3 className="font-serif text-lg">
                  {confirmation === "cancel"
                    ? "Cancel this appointment?"
                    : "Permanently delete this appointment?"}
                </h3>
                <p className="my-3 text-xs leading-relaxed text-secondary">
                  {confirmation === "cancel"
                    ? "The record stays in the appointment history. This booking cannot be reopened after cancellation."
                    : "This cannot be undone. Records with payment receipts cannot be deleted."}
                </p>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    disabled={working}
                    className="inline-flex items-center gap-2 rounded-lg bg-error px-4 py-2 text-xs font-medium text-white"
                    onClick={() =>
                      confirmation === "cancel"
                        ? void change(
                            { status: "cancelled" },
                            "Appointment cancelled.",
                          )
                        : void remove()
                    }
                  >
                    {busy && <Loader2 size={12} className="animate-spin" />}
                    {confirmation === "cancel"
                      ? "Confirm cancellation"
                      : "Delete permanently"}
                  </button>
                  <button
                    type="button"
                    disabled={working}
                    className="studio-secondary-button"
                    onClick={() => setConfirmation(null)}
                  >
                    Keep appointment
                  </button>
                </div>
              </section>
            )}
          </div>
        </div>
      </div>
      <footer className="sticky bottom-0 flex items-center justify-between gap-3 border-t border-purple-light/15 bg-card px-5 py-4 sm:px-7">
        <p className="flex items-center gap-1.5 text-[11px] text-muted">
          <Clock size={12} />
          All appointment times use Philippine time
        </p>
        <button
          type="button"
          className="studio-secondary-button"
          disabled={working}
          onClick={onClose}
        >
          Close details
        </button>
      </footer>
    </dialog>
  );
}
