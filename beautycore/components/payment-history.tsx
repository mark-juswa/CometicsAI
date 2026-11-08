"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { businessRequest } from "@/lib/business/client";
import {
  Card,
  EmptyState,
  Skeleton,
  formatDate,
  formatPeso,
} from "@/components/ui";
type Payment = {
  id: string;
  amount: number;
  method: string;
  reference: string | null;
  createdAt: string;
  serviceName: string;
  clientId: string;
  clientName: string;
  stylistName: string | null;
  totalPrice: number | null;
};
export function PaymentHistory() {
  const [rows, setRows] = useState<Payment[]>([]),
    [query, setQuery] = useState(""),
    [method, setMethod] = useState("all"),
    [from, setFrom] = useState(""),
    [to, setTo] = useState(""),
    [page, setPage] = useState(1),
    [total, setTotal] = useState(0),
    [amount, setAmount] = useState(0),
    [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    const params = new URLSearchParams({
      q: query,
      method,
      page: String(page),
    });
    if (from) params.set("from", from);
    if (to) params.set("to", to);
    businessRequest("/api/admin/payments?" + params)
      .then((d) => {
        if (active) {
          setRows(d.payments);
          setTotal(d.total);
          setAmount(d.amount);
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
  }, [query, method, from, to, page]);
  return (
    <Card className="mb-6">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-serif text-xl">Payments received</h2>
          <p className="mt-2 text-xs text-muted">
            Actual receipts recorded against appointments. Open a client record
            to record a payment.
          </p>
        </div>
        <p className="font-serif text-2xl text-gold">{formatPeso(amount)}</p>
      </div>
      <div className="mb-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <label className="text-xs text-muted">
          Search
          <input
            type="search"
            placeholder="Client, service, or receipt"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(1);
            }}
          />
        </label>
        <label className="text-xs text-muted">
          Method
          <select
            value={method}
            onChange={(e) => {
              setMethod(e.target.value);
              setPage(1);
            }}
          >
            {["all", "cash", "card", "bank", "other"].map((m) => (
              <option key={m} value={m}>
                {m === "all" ? "All methods" : m}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs text-muted">
          Received from
          <input
            type="date"
            value={from}
            onChange={(e) => {
              setFrom(e.target.value);
              setPage(1);
            }}
          />
        </label>
        <label className="text-xs text-muted">
          Received through
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
      {error && (
        <p role="alert" className="mb-4 text-sm text-error">
          {error}
        </p>
      )}
      {loading ? (
        <Skeleton className="h-36 w-full" />
      ) : !rows.length ? (
        <EmptyState
          title="No matching payment receipts"
          body="Previous service prices remain in service reports. They are not counted as receipts unless a payment was recorded."
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead>
              <tr>
                <th>Client / service</th>
                <th>Stylist</th>
                <th>Received</th>
                <th>Service price</th>
                <th>Payment received</th>
                <th>Method / reference</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td>
                    <Link
                      href={`/admin/clients/${row.clientId}`}
                      className="text-gold underline"
                    >
                      {row.clientName}
                    </Link>
                    <p className="mt-1 text-xs text-secondary">
                      {row.serviceName}
                    </p>
                  </td>
                  <td>{row.stylistName || "Unassigned"}</td>
                  <td>{formatDate(row.createdAt)}</td>
                  <td>
                    {formatPeso(
                      row.totalPrice === null ? null : Number(row.totalPrice),
                    )}
                  </td>
                  <td className="text-success">
                    {formatPeso(Number(row.amount))}
                  </td>
                  <td>
                    {row.method}
                    {row.reference && (
                      <p className="mt-1 text-xs text-muted">{row.reference}</p>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="mt-5 flex items-center justify-center gap-3">
        <button
          className="studio-secondary-button"
          disabled={loading || page === 1}
          onClick={() => setPage(page - 1)}
        >
          Previous
        </button>
        <span className="text-sm">
          Page {page} · {total} receipts
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
  );
}
