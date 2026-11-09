"use client";
import { useRef, useState } from "react";
import { businessRequest } from "../lib/business/client";
import { salonDateTime } from "../lib/business/dates";
import { ServiceCompletion } from "./service-completion";
import type { AppointmentStatus } from "../db/schema";
import type { ServiceRecord } from "../lib/business/workflow-types";

export function ServiceControls({
  id,
  status,
  appointmentDate,
  record,
  admin = false,
  onUpdated,
}: {
  id: string;
  status: AppointmentStatus;
  appointmentDate: string;
  record: ServiceRecord;
  admin?: boolean;
  onUpdated: () => void | Promise<void>;
}) {
  const [open, setOpen] = useState(false),
    [outcome, setOutcome] = useState(""),
    [reason, setReason] = useState(""),
    [date, setDate] = useState(""),
    [confirming, setConfirming] = useState(false),
    [completion, setCompletion] = useState(false),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const lock = useRef(false),
    arrived = !!record.tracking?.arrived_at,
    started = !!record.tracking?.started_at;
  const now = Date.now(),
    scheduled = Date.parse(appointmentDate),
    eligible =
      status === "confirmed" &&
      now >= scheduled - 1800000 &&
      (arrived || now < scheduled + 1800000);
  async function act(action: string) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      const appointmentDate =
        action === "restore" && date
          ? salonDateTime(date.slice(0, 10), date.slice(11, 16))
          : undefined;
      await businessRequest(`/api/appointments/${id}/service`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action,
          reason: reason.trim() || undefined,
          confirmed: true,
          appointmentDate,
        }),
      });
      setOpen(false);
      setConfirming(false);
      setOutcome("");
      setReason("");
      window.dispatchEvent(new Event("appointments-updated"));
      await onUpdated();
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "The service could not be updated.",
      );
    } finally {
      setBusy(false);
      lock.current = false;
    }
  }
  if (status === "completed" || status === "cancelled" || status === "pending")
    return null;
  return (
    <section
      className="my-3 space-y-3 rounded-lg border border-purple-light/20 p-4"
      aria-label="Service controls"
    >
      {status === "no_show" ? (
        <>
          <p>This appointment is marked No-Show. Its history is retained.</p>
          {admin ? (
            <>
              <label className="block">
                New appointment time (Philippine time)
                <input
                  aria-label="Restore appointment time"
                  type="datetime-local"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  disabled={busy}
                />
              </label>
              <label className="block">
                Restoration reason
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  maxLength={1000}
                  disabled={busy}
                />
              </label>
              <button
                type="button"
                disabled={busy || !date || !reason.trim()}
                onClick={() => {
                  setOutcome("restore");
                  setConfirming(true);
                }}
              >
                Restore / reschedule appointment
              </button>
            </>
          ) : (
            <p>
              Ask an administrator to restore or reschedule this appointment.
            </p>
          )}
        </>
      ) : (
        <>
          <div className="flex flex-wrap gap-2">
            {status === "confirmed" && !arrived && (
              <button
                type="button"
                className="studio-secondary-button"
                disabled={busy || !eligible}
                onClick={() => void act("arrive")}
              >
                Mark Customer Arrived
              </button>
            )}
            <button
              type="button"
              className="studio-primary-button"
              disabled={busy || !eligible}
              onClick={() => void act("start")}
            >
              Start Service
            </button>
            <button
              type="button"
              className="studio-secondary-button"
              disabled={busy}
              onClick={() => {
                setOpen(!open);
                setCompletion(false);
                setConfirming(false);
              }}
            >
              Stop Service
            </button>
          </div>
          {status === "confirmed" && !eligible && (
            <p className="text-xs text-muted">
              Arrival and start are available from 30 minutes before the
              scheduled start until the grace period ends. Recorded arrival
              protects the appointment.
            </p>
          )}
          {open && (
            <div className="space-y-3">
              <label className="block">
                Stop reason
                <select
                  aria-label="Stop reason"
                  value={outcome}
                  onChange={(e) => {
                    setOutcome(e.target.value);
                    setConfirming(false);
                    setCompletion(false);
                  }}
                  disabled={busy}
                >
                  <option value="">Choose an outcome</option>
                  <option value="completed" disabled={status !== "in_progress"}>
                    Service Completed
                  </option>
                  <option
                    value="no_show"
                    disabled={
                      arrived ||
                      started ||
                      now < scheduled ||
                      status === "in_progress"
                    }
                  >
                    Client Did Not Attend (No-Show)
                  </option>
                  <option value="cancel">Service Cancelled</option>
                  <option value="other">Other</option>
                </select>
              </label>
              {outcome && outcome !== "completed" && (
                <label className="block">
                  Explanation{outcome === "cancel" ? " (optional)" : ""}
                  <textarea
                    aria-label="Service outcome explanation"
                    maxLength={1000}
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    disabled={busy}
                  />
                </label>
              )}
              <button
                type="button"
                disabled={
                  busy ||
                  !outcome ||
                  (["other", "no_show"].includes(outcome) && !reason.trim())
                }
                onClick={() =>
                  outcome === "completed"
                    ? setCompletion(true)
                    : setConfirming(true)
                }
              >
                {outcome === "completed"
                  ? "Record completion"
                  : "Review outcome"}
              </button>
              {completion && (
                <ServiceCompletion
                  id={id}
                  initiallyOpen
                  onCompleted={async () => {
                    setCompletion(false);
                    setOpen(false);
                    window.dispatchEvent(new Event("appointments-updated"));
                    await onUpdated();
                  }}
                />
              )}
            </div>
          )}
        </>
      )}
      {confirming && (
        <div
          role="alertdialog"
          aria-label="Confirm service outcome"
          className="space-y-2 border border-gold/40 p-3"
        >
          <p>
            Save this outcome: {outcome.replaceAll("_", " ")}? {reason}
          </p>
          <button
            type="button"
            disabled={busy}
            onClick={() => void act(outcome)}
          >
            Confirm outcome
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => setConfirming(false)}
          >
            Back
          </button>
        </div>
      )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
