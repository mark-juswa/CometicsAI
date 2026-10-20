'use client';
import { useEffect, useState } from 'react';
import { businessRequest } from '../lib/business/client';
export function AdminBookingControls({
  id,
  stylistId,
  lockedAssignment = false,
  totalPrice,
  onUpdated,
  stylists,
}: {
  id: string;
  lockedAssignment?: boolean;
  stylistId: string | null;
  totalPrice: number | null;
  onUpdated: () => void;
  stylists: { id: string; name: string }[];
}) {
  const [stylist, setStylist] = useState(stylistId ?? '');
  const [amount, setAmount] = useState(totalPrice === null ? '' : String(totalPrice));
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    setStylist(stylistId ?? '');
    setAmount(totalPrice === null ? '' : String(totalPrice));
  }, [stylistId, totalPrice]);
  async function save() {
    if (busy) return;
    setBusy(true);
    setMessage('');
    try {
      await businessRequest(`/api/appointments/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...(!lockedAssignment ? { stylistId: stylist || null } : {}),
          totalPrice: amount === '' ? null : Number(amount),
        }),
      });
      setMessage(
        lockedAssignment ? 'Recorded amount saved.' : 'Assignment and recorded amount saved.',
      );
      onUpdated();
    } catch (cause) {
      setMessage(cause instanceof Error ? cause.message : 'Could not update booking.');
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="booking-admin-controls">
      <label>
        Assigned stylist
        <select
          disabled={lockedAssignment}
          value={stylist}
          onChange={(e) => setStylist(e.target.value)}
        >
          <option value="">Unassigned</option>
          {stylists.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        Recorded amount (whole pesos)
        <input
          type="number"
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
        disabled={busy}
        onClick={() => void save()}
      >
        {busy ? 'Saving…' : lockedAssignment ? 'Save recorded amount' : 'Save assignment / amount'}
      </button>
      {message && (
        <p role="status" className="text-sm">
          {message}
        </p>
      )}
    </div>
  );
}
