"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { businessRequest } from "@/lib/business/client";
import {
  Card,
  PageHeader,
  Skeleton,
  EmptyState,
  StatusBadge,
  formatDate,
  formatTime,
  formatPeso,
} from "@/components/ui";
import type { AppointmentStatus } from "@/db/schema";
type Appointment = {
  id: string;
  serviceName: string;
  serviceType: string;
  appointmentDate: string;
  status: AppointmentStatus;
  totalPrice: number | null;
  paidAmount: number;
  stylistName: string | null;
};
type Receipt = {
  id: string;
  appointmentId: string;
  amount: number;
  method: string;
  reference: string | null;
  createdAt: string;
  serviceName: string;
  recordedBy: string;
};
type Client = {
  name: string;
  email: string;
  phone: string | null;
  isActive: boolean;
  createdAt: string;
};
type Summary = {
  bookings: number;
  completed: number;
  completedValue: number;
  paymentsReceived: number;
};
export function ClientHistory({ clientId }: { clientId: string }) {
  const [client, setClient] = useState<Client | null>(null),
    [rows, setRows] = useState<Appointment[]>([]),
    [receipts, setReceipts] = useState<Receipt[]>([]),
    [summary, setSummary] = useState<Summary | null>(null),
    [q, setQuery] = useState(""),
    [status, setStatus] = useState("all"),
    [from, setFrom] = useState(""),
    [to, setTo] = useState(""),
    [page, setPage] = useState(1),
    [total, setTotal] = useState(0),
    [reload, setReload] = useState(0),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [message, setMessage] = useState("");
  const [paymentFor, setPaymentFor] = useState(""),
    [amount, setAmount] = useState(""),
    [method, setMethod] = useState("cash"),
    [reference, setReference] = useState(""),
    [busy, setBusy] = useState(false);
  const lock = useRef(false),
    requestId = useRef("");
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    const params = new URLSearchParams({ q, status, page: String(page) });
    if (from) params.set("from", from);
    if (to) params.set("to", to);
    businessRequest(`/api/admin/clients/${clientId}?${params}`)
      .then((d) => {
        if (active) {
          setClient(d.client);
          setRows(d.appointments);
          setReceipts(d.payments);
          setSummary(d.summary);
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
  }, [clientId, q, status, from, to, page, reload]);
  function choosePayment(row: Appointment) {
    setPaymentFor(row.id);
    setAmount(
      String(Math.max(0, Number(row.totalPrice) - Number(row.paidAmount))),
    );
    setMethod("cash");
    setReference("");
    requestId.current = crypto.randomUUID();
  }
  async function recordPayment(event: React.FormEvent) {
    event.preventDefault();
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      await businessRequest(`/api/admin/clients/${clientId}/payments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          appointmentId: paymentFor,
          requestId: requestId.current,
          amount: Number(amount),
          method,
          reference,
        }),
      });
      setPaymentFor("");
      setMessage("Payment receipt recorded.");
      setReload((x) => x + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not record payment.");
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  return (
    <>
      <Link
        className="mb-4 inline-block text-sm text-gold underline"
        href="/admin/clients"
      >
        ← All clients
      </Link>
      <PageHeader
        title={client?.name || "Client Details"}
        subtitle="Account information, service history, and recorded payments."
      />
      {error && (
        <p
          role="alert"
          className="mb-4 rounded border border-error/30 bg-error/10 p-4 text-sm text-error"
        >
          {error}
        </p>
      )}
      {message && (
        <p role="status" className="mb-4 text-sm text-success">
          {message}
        </p>
      )}
      {client && (
        <div className="mb-6 grid gap-4 md:grid-cols-2">
          <Card>
            <h2 className="mb-3 font-serif text-xl">Account details</h2>
            <dl className="grid grid-cols-[auto_1fr] gap-x-5 gap-y-2 text-sm">
              <dt className="text-muted">Email</dt>
              <dd className="break-all">{client.email}</dd>
              <dt className="text-muted">Phone</dt>
              <dd>{client.phone || "Not provided"}</dd>
              <dt className="text-muted">Account</dt>
              <dd className={client.isActive ? "text-success" : "text-warning"}>
                {client.isActive ? "Active" : "Inactive"}
              </dd>
              <dt className="text-muted">Joined</dt>
              <dd>{formatDate(client.createdAt)}</dd>
            </dl>
          </Card>
          <Card>
            <h2 className="mb-3 font-serif text-xl">
              Service and payment summary
            </h2>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-muted">Appointments</dt>
                <dd className="text-xl">{summary?.bookings ?? 0}</dd>
              </div>
              <div>
                <dt className="text-muted">Completed services</dt>
                <dd className="text-xl">{summary?.completed ?? 0}</dd>
              </div>
              <div>
                <dt className="text-muted">Completed service value</dt>
                <dd className="text-lg">
                  {formatPeso(Number(summary?.completedValue ?? 0))}
                </dd>
              </div>
              <div>
                <dt className="text-muted">Payments received</dt>
                <dd className="text-lg text-gold">
                  {formatPeso(Number(summary?.paymentsReceived ?? 0))}
                </dd>
              </div>
            </dl>
            <p className="mt-3 text-xs text-muted">
              Service prices and actual payment receipts are recorded
              separately. Historical payments without receipts are shown as not
              recorded.
            </p>
          </Card>
        </div>
      )}
      <Card>
        <h2 className="mb-4 font-serif text-xl">
          Appointments and previous services
        </h2>
        <div className="mb-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <label className="text-xs text-secondary">
            Search service or stylist
            <input
              value={q}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(1);
              }}
              placeholder="Service or stylist"
            />
          </label>
          <label className="text-xs text-secondary">
            Appointment status
            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(1);
              }}
            >
              {["all", "pending", "confirmed", "completed", "cancelled"].map(
                (s) => (
                  <option value={s} key={s}>
                    {s === "all" ? "All statuses" : s}
                  </option>
                ),
              )}
            </select>
          </label>
          <label className="text-xs text-secondary">
            From
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
            Through
            <input
              type="date"
              value={to}
              onChange={(e) => {
                setTo(e.target.value);
                setPage(1);
              }}
            />
          </label>
        </div>
        {loading ? (
          <Skeleton className="h-48 w-full" />
        ) : rows.length === 0 ? (
          <EmptyState
            title="No matching appointments"
            body="Try another service, date, or status."
          />
        ) : (
          <div className="space-y-4">
            {rows.map((row) => {
              const paid = Number(row.paidAmount);
              const outstanding =
                row.totalPrice === null
                  ? null
                  : Math.max(0, Number(row.totalPrice) - paid);
              return (
                <article
                  key={row.id}
                  className="rounded-lg border border-purple-light/20 p-4"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="text-lg">{row.serviceName}</h3>
                      <p className="mt-2 text-sm text-muted">
                        {formatDate(row.appointmentDate)} ·{" "}
                        {formatTime(row.appointmentDate)} ·{" "}
                        {row.stylistName || "Unassigned stylist"}
                      </p>
                    </div>
                    <StatusBadge status={row.status} />
                  </div>
                  <dl className="mt-4 grid grid-cols-2 gap-4 text-sm lg:grid-cols-4">
                    <div>
                      <dt className="text-muted">Service price</dt>
                      <dd>
                        {row.totalPrice === null
                          ? "Not priced"
                          : formatPeso(Number(row.totalPrice))}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-muted">Payment amount</dt>
                      <dd>{formatPeso(paid)}</dd>
                    </div>
                    <div>
                      <dt className="text-muted">Payment status</dt>
                      <dd
                        className={
                          outstanding === 0 ? "text-success" : "text-warning"
                        }
                      >
                        {row.totalPrice === null
                          ? "Awaiting price"
                          : outstanding === 0
                            ? "Paid"
                            : paid > 0
                              ? "Partially paid"
                              : "No payment recorded"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-muted">Balance</dt>
                      <dd>
                        {outstanding === null
                          ? "Not priced"
                          : formatPeso(outstanding)}
                      </dd>
                    </div>
                  </dl>
                  {row.status !== "cancelled" &&
                    outstanding !== null &&
                    outstanding > 0 && (
                      <button
                        type="button"
                        className="studio-secondary-button mt-4"
                        onClick={() => choosePayment(row)}
                      >
                        Record payment
                      </button>
                    )}
                  {paymentFor === row.id && (
                    <form
                      onSubmit={recordPayment}
                      className="mt-4 rounded border border-gold/30 p-4"
                    >
                      <p className="mb-3 text-sm text-secondary">
                        Record a payment already received for this appointment.
                      </p>
                      <fieldset
                        disabled={busy}
                        className="grid gap-3 sm:grid-cols-3"
                      >
                        <label className="text-xs">
                          Amount (whole pesos)
                          <input
                            required
                            type="number"
                            min="1"
                            max={outstanding ?? 0}
                            step="1"
                            value={amount}
                            onChange={(e) => setAmount(e.target.value)}
                          />
                        </label>
                        <label className="text-xs">
                          Method
                          <select
                            value={method}
                            onChange={(e) => setMethod(e.target.value)}
                          >
                            {["cash", "card", "bank", "other"].map((m) => (
                              <option key={m}>{m}</option>
                            ))}
                          </select>
                        </label>
                        <label className="text-xs">
                          Receipt/reference (optional)
                          <input
                            maxLength={160}
                            value={reference}
                            onChange={(e) => setReference(e.target.value)}
                          />
                        </label>
                        <button className="studio-primary-button" type="submit">
                          {busy ? "Recording…" : "Save payment receipt"}
                        </button>
                        <button
                          className="studio-secondary-button"
                          type="button"
                          onClick={() => setPaymentFor("")}
                        >
                          Cancel
                        </button>
                      </fieldset>
                    </form>
                  )}
                </article>
              );
            })}
          </div>
        )}
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <button
            className="studio-secondary-button"
            disabled={loading || page === 1}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </button>
          <span className="text-sm">
            Page {page} · {total} appointments
          </span>
          <button
            className="studio-secondary-button"
            disabled={loading || page * 12 >= total}
            onClick={() => setPage(page + 1)}
          >
            Next
          </button>
        </div>
      </Card>
      <Card className="mt-6">
        <h2 className="mb-3 font-serif text-xl">
          Payment receipts for these appointments
        </h2>
        {receipts.length === 0 ? (
          <p className="text-sm text-muted">
            No payment receipts have been recorded for the appointments on this
            page.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead>
                <tr>
                  <th>Service</th>
                  <th>Received</th>
                  <th>Amount</th>
                  <th>Method / reference</th>
                  <th>Recorded by</th>
                </tr>
              </thead>
              <tbody>
                {receipts.map((r) => (
                  <tr key={r.id}>
                    <td>{r.serviceName}</td>
                    <td>{formatDate(r.createdAt)}</td>
                    <td className="text-gold">
                      {formatPeso(Number(r.amount))}
                    </td>
                    <td>
                      {r.method}
                      {r.reference ? ` · ${r.reference}` : ""}
                    </td>
                    <td>{r.recordedBy}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
}
