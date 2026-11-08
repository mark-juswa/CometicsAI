"use client";
import { useEffect, useRef, useState } from "react";
import { businessRequest } from "../lib/business/client";
export function AdminBookingControls({
  id,
  stylistId,
  lockedAssignment = false,
  totalPrice,
  onUpdated,
  stylists,
  disabled = false,
  onBusyChange,
}: {
  id: string;
  lockedAssignment?: boolean;
  stylistId: string | null;
  totalPrice: number | null;
  onUpdated: () => void | Promise<void>;
  stylists: { id: string; name: string; disabled?: boolean }[];
  disabled?: boolean;
  onBusyChange?: (busy: boolean) => void;
}) {
  const [stylist, setStylist] = useState(stylistId ?? "");
  const [amount, setAmount] = useState(
    totalPrice === null ? "" : String(totalPrice),
  );
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const lock = useRef(false);

  useEffect(() => {
    setStylist(stylistId ?? "");
    setAmount(totalPrice === null ? "" : String(totalPrice));
  }, [stylistId, totalPrice]);
  async function save() {
    if (lock.current || disabled) return;
    lock.current = true;
    setBusy(true);
    onBusyChange?.(true);
    setMessage("");
    setError("");
    try {
      if (
        amount.trim() !== "" &&
        (!Number.isInteger(Number(amount)) ||
          Number(amount) < 0 ||
          Number(amount) > 100000000)
      )
        throw new Error(
          "Enter a whole-peso amount between 0 and 100,000,000, or leave it empty for an unconfirmed price.",
        );
      await businessRequest(`/api/appointments/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...(!lockedAssignment ? { stylistId: stylist || null } : {}),
          totalPrice: amount.trim() === "" ? null : Number(amount),
        }),
      });
      setMessage(
        lockedAssignment
          ? "Recorded amount saved."
          : "Assignment and recorded amount saved.",
      );
      await onUpdated();
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Could not update booking.",
      );
    } finally {
      setBusy(false);
      lock.current = false;
      onBusyChange?.(false);
    }
  }
  return (
    <div className="space-y-4">
      <label className="block text-xs text-secondary">
        Assigned stylist
        <select
          disabled={lockedAssignment || disabled || busy}
          value={stylist}
          onChange={(e) => setStylist(e.target.value)}
        >
          <option value="">Unassigned</option>
          {stylists.map((s) => (
            <option key={s.id} value={s.id} disabled={s.disabled}>
              {s.name}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-xs text-secondary">
        Recorded amount (whole pesos)
        <input
          type="number"
          disabled={disabled || busy}
          min="0"
          max="100000000"
          step="1"
          placeholder="Price to be confirmed"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
      </label>
      <button
        type="button"
        className="studio-secondary-button"
        disabled={disabled || busy}
        onClick={() => void save()}
      >
        {busy
          ? "Saving…"
          : lockedAssignment
            ? "Save recorded amount"
            : "Save assignment / amount"}
      </button>
      {message && (
        <p role="status" className="text-xs text-success">
          {message}
        </p>
      )}
      {error && (
        <p role="alert" className="text-xs text-error">
          {error}
        </p>
      )}
    </div>
  );
}
