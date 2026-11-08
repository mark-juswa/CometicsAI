"use client";
import { useEffect, useRef, useState } from "react";
import {
  CalendarDays,
  CheckCircle2,
  Users,
  Wallet,
  X,
  RefreshCw,
} from "lucide-react";
import { businessRequest } from "@/lib/business/client";
import {
  PortalMetrics,
  PortalPagination,
  PortalWorkspace,
} from "./portal-workspace";
import { EmptyState, Skeleton, formatDate, formatTime, formatPeso } from "./ui";
type History = {
  stylist: { id: string; name: string; isActive: boolean };
  services: {
    id: string;
    serviceName: string;
    appointmentDate: string;
    completedAt: string | null;
    totalPrice: number | null;
    clientName: string | null;
    durationMinutes: number;
    rating: number | null;
  }[];
  total: number;
  summary: {
    completed: number;
    amount: number;
    unpriced: number;
    clients: number;
    minutes: number;
  };
};
export function StylistServiceDialog({
  stylist,
  onClose,
}: {
  stylist: { id: string; name: string };
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null),
    [from, setFrom] = useState(""),
    [to, setTo] = useState(""),
    [page, setPage] = useState(1),
    [data, setData] = useState<History | null>(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [revision, setRevision] = useState(0);
  useEffect(() => {
    const element = dialog.current;
    element?.showModal();
    return () => element?.close();
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    setData(null);
    if (from && to && from > to) {
      setLoading(false);
      setError("The end date must be on or after the start date.");
      return () => controller.abort();
    }
    const params = new URLSearchParams({ page: String(page) });
    if (from) params.set("from", from);
    if (to) params.set("to", to);
    businessRequest(`/api/admin/stylists/${stylist.id}/services?${params}`, {
      signal: controller.signal,
    })
      .then((value) => {
        if (!controller.signal.aborted) setData(value);
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setError(cause.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [stylist.id, from, to, page, revision]);
  return (
    <dialog
      ref={dialog}
      aria-labelledby="stylist-services-title"
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      className="fixed inset-0 m-auto max-h-[92dvh] overflow-y-auto rounded-2xl border border-purple-light/25 bg-card p-0 text-white shadow-2xl backdrop:bg-black/70"
      style={{ width: "min(72rem, calc(100vw - 2rem))" }}
    >
      <PortalWorkspace>
        <header className="sticky top-0 z-10 flex items-center justify-between gap-4 border-b border-purple-light/20 bg-card px-6 py-5">
          <div>
            <p className="portal-eyebrow">Completed service history</p>
            <h2 id="stylist-services-title" className="font-serif text-2xl">
              {stylist.name}
            </h2>
          </div>
          <button
            type="button"
            aria-label="Close stylist service history"
            onClick={onClose}
            className="portal-button"
          >
            <X size={18} />
          </button>
        </header>
        <div className="p-5 sm:p-6">
          <p className="portal-help mb-5">
            Services completed by this stylist, with client, date, recorded
            amount and rating. All dates use Philippine time.
          </p>
          <div className="mb-5 flex flex-wrap items-end gap-3">
            <label className="text-xs text-secondary">
              Services from
              <input
                aria-label="Stylist services from"
                type="date"
                value={from}
                onChange={(event) => {
                  setFrom(event.target.value);
                  setPage(1);
                }}
              />
            </label>
            <label className="text-xs text-secondary">
              Services through
              <input
                aria-label="Stylist services through"
                type="date"
                value={to}
                onChange={(event) => {
                  setTo(event.target.value);
                  setPage(1);
                }}
              />
            </label>
            <button
              className="portal-button"
              onClick={() => {
                setFrom("");
                setTo("");
                setPage(1);
              }}
            >
              All dates
            </button>
            <button
              aria-label="Refresh stylist service history"
              className="portal-button"
              onClick={() => setRevision((value) => value + 1)}
            >
              <RefreshCw size={14} />
            </button>
          </div>
          {error ? (
            <p role="alert" className="portal-alert">
              {error}
            </p>
          ) : loading ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            data && (
              <>
                <PortalMetrics
                  items={[
                    {
                      label: "Completed services",
                      value: data.summary.completed,
                      icon: CheckCircle2,
                      note: "Within selected dates",
                    },
                    {
                      label: "Recorded service revenue",
                      value: formatPeso(data.summary.amount),
                      icon: Wallet,
                      note: "Before costs or compensation",
                    },
                    {
                      label: "Clients served",
                      value: data.summary.clients,
                      icon: Users,
                      note: "Unique clients in this period",
                    },
                    {
                      label: "Service hours",
                      value: (data.summary.minutes / 60).toLocaleString(
                        "en-PH",
                        { maximumFractionDigits: 1 },
                      ),
                      icon: CalendarDays,
                      note: "Catalog service durations",
                    },
                  ]}
                />
                {data.summary.unpriced > 0 && (
                  <p className="portal-help mb-4">
                    {data.summary.unpriced} completed services have unconfirmed
                    prices, excluded from monetary totals.
                  </p>
                )}
                <section className="portal-panel">
                  {!data.services.length ? (
                    <EmptyState
                      icon={CheckCircle2}
                      title="No completed services in this period"
                      body="Choose another date range or select All dates."
                    />
                  ) : (
                    <div className="portal-table-scroll">
                      <table className="portal-table">
                        <thead>
                          <tr>
                            <th>Service</th>
                            <th>Client</th>
                            <th>Scheduled visit</th>
                            <th>Recorded amount</th>
                            <th>Rating</th>
                          </tr>
                        </thead>
                        <tbody>
                          {data.services.map((service) => (
                            <tr key={service.id}>
                              <td>
                                <strong>{service.serviceName}</strong>
                                <span>{service.durationMinutes} minutes</span>
                                {service.completedAt && (
                                  <span>
                                    Completed {formatDate(service.completedAt)}
                                  </span>
                                )}
                              </td>
                              <td>
                                <strong>
                                  {service.clientName ?? "Unknown client"}
                                </strong>
                              </td>
                              <td>
                                <strong>
                                  {formatDate(service.appointmentDate)}
                                </strong>
                                <span>
                                  {formatTime(service.appointmentDate)}
                                </span>
                              </td>
                              <td>
                                <strong className="text-gold">
                                  {service.totalPrice === null
                                    ? "Unconfirmed"
                                    : formatPeso(service.totalPrice)}
                                </strong>
                              </td>
                              <td>
                                {service.rating
                                  ? `${service.rating} / 5`
                                  : "Not reviewed"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                  <PortalPagination
                    page={page}
                    pages={Math.max(1, Math.ceil(data.total / 12))}
                    total={data.total}
                    onChange={setPage}
                  />
                </section>
              </>
            )
          )}
        </div>
        <footer className="sticky bottom-0 border-t border-purple-light/15 bg-card px-6 py-4 text-right">
          <button className="portal-button" onClick={onClose}>
            Close history
          </button>
        </footer>
      </PortalWorkspace>
    </dialog>
  );
}
