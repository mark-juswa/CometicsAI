"use client";
import {
  PortalWorkspace,
  PortalMetrics,
  PortalPagination,
} from "@/components/portal-workspace";
import { businessRequest } from "@/lib/business/client";
import { salonDay } from "@/lib/business/dates";
import { AppointmentServiceRecord } from "@/components/appointment-service-record";
import type { ServiceRecord } from "@/lib/business/workflow-types";
import { useAppointmentRefresh } from "@/lib/business/use-appointment-refresh";

import {
  AppointmentLookPreview,
  type AppointmentLook,
} from "@/components/appointment-look";

import { ServiceCompletion } from "@/components/service-completion";
import { useState, useEffect, useMemo } from "react";
import {
  Search,
  CalendarDays,
  Clock,
  CheckCircle2,
  Users,
  ChevronDown,
} from "lucide-react";
import {
  PageHeader,
  StatusBadge,
  EmptyState,
  Skeleton,
  formatDate,
  formatTime,
  formatPeso,
} from "@/components/ui";
import { type AppointmentStatus } from "@/db/schema";

interface Row extends ServiceRecord {
  look?: AppointmentLook | null;
  id: string;
  serviceName: string;
  serviceType: string;
  appointmentDate: string;
  status: AppointmentStatus;
  totalPrice: number | null;
  notes: string | null;
  client: { id: string; name: string; email: string } | null;
}

type Range = "upcoming" | "past" | "all";

export default function StylistAppointmentsPage() {
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [range, setRange] = useState<Range>("upcoming");
  const [busy, setBusy] = useState<string | null>(null);
  const [actionError, setActionError] = useState("");
  const [dateFilter, setDateFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [completionBusy, setCompletionBusy] = useState(false);
  useEffect(() => setPage(1), [query, range, dateFilter, statusFilter]);

  const load = () => {
    businessRequest("/api/appointments")
      .then((d) => setRows(d.appointments ?? []))
      .catch((e) => setActionError(e.message))
      .finally(() => setLoading(false));
  };
  useEffect(load, []);
  useAppointmentRefresh(load);

  const setStatus = async (id: string, status: AppointmentStatus) => {
    if (busy || completionBusy) return;
    setBusy(id);
    setActionError("");
    try {
      const res = await fetch(`/api/appointments/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      if (!res.ok)
        throw new Error(
          (await res.json()).error || "Could not update the appointment.",
        );
      if (res.ok) {
        const data = await res.json();
        setRows((rs) =>
          rs.map((r) =>
            r.id === id ? { ...r, status: data.appointment.status } : r,
          ),
        );
      }
    } catch (cause) {
      setActionError(
        cause instanceof Error
          ? cause.message
          : "Could not update the appointment.",
      );
    } finally {
      setBusy(null);
    }
  };

  const now = Date.now();
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return rows
      .filter((r) => {
        if (dateFilter && salonDay(new Date(r.appointmentDate)) !== dateFilter)
          return false;
        if (statusFilter !== "all" && r.status !== statusFilter) return false;
        const t = new Date(r.appointmentDate).getTime();
        if (range === "upcoming")
          return t >= now && ["pending", "confirmed"].includes(r.status);
        if (range === "past")
          return t < now || ["cancelled", "completed"].includes(r.status);
        return true;
      })
      .filter(
        (r) =>
          !q ||
          r.serviceName.toLowerCase().includes(q) ||
          r.client?.name.toLowerCase().includes(q),
      )
      .sort(
        (a, b) =>
          new Date(a.appointmentDate).getTime() -
          new Date(b.appointmentDate).getTime(),
      );
  }, [rows, query, range, now, dateFilter, statusFilter]);

  const pages = Math.max(1, Math.ceil(filtered.length / 10)),
    current = Math.min(page, pages),
    visible = filtered.slice((current - 1) * 10, current * 10);
  return (
    <PortalWorkspace>
      <PageHeader
        title="My Appointments"
        subtitle="Your assigned visits, client references, and service records in one place."
      />
      <PortalMetrics
        items={[
          {
            label: "Today",
            value: loading
              ? "—"
              : rows.filter(
                  (r) =>
                    salonDay(new Date(r.appointmentDate)) === salonDay() &&
                    r.status !== "cancelled",
                ).length,
            icon: CalendarDays,
            note: "Scheduled visits · Philippine time",
          },
          {
            label: "Upcoming",
            value: loading
              ? "—"
              : rows.filter(
                  (r) =>
                    Date.parse(r.appointmentDate) >= now &&
                    ["pending", "confirmed"].includes(r.status),
                ).length,
            icon: Clock,
            note: "Pending and confirmed",
          },
          {
            label: "Completed",
            value: loading
              ? "—"
              : rows.filter((r) => r.status === "completed").length,
            icon: CheckCircle2,
            note: "Your completed services",
          },
          {
            label: "Clients",
            value: loading
              ? "—"
              : new Set(rows.map((r) => r.client?.id).filter(Boolean)).size,
            icon: Users,
            note: "From your assigned bookings",
          },
        ]}
      />
      {actionError && (
        <p role="alert" className="portal-alert">
          {actionError}
        </p>
      )}
      <section className="portal-panel">
        <div className="portal-panel-heading">
          <div>
            <h2>Your schedule</h2>
            <p>
              Open a visit to view its selected look, notes, and service
              actions.
            </p>
          </div>
          <span className="portal-pill">{rows.length} assigned</span>
        </div>
        <div className="portal-tabs" aria-label="Appointment range">
          {(["upcoming", "past", "all"] as const).map((value) => (
            <button
              key={value}
              aria-pressed={range === value}
              className="capitalize"
              onClick={() => setRange(value)}
            >
              {value}
            </button>
          ))}
        </div>
        <div className="portal-toolbar">
          <label className="portal-search">
            <Search size={16} />
            <input
              aria-label="Search appointments"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search client or service"
            />
          </label>
          <label className="text-xs text-muted">
            Appointment date
            <input
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
            />
          </label>
          <label className="text-xs text-muted">
            Status
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              {["all", "pending", "confirmed", "completed", "cancelled"].map(
                (value) => (
                  <option key={value} value={value}>
                    {value === "all" ? "All statuses" : value}
                  </option>
                ),
              )}
            </select>
          </label>
          <button
            className="portal-button"
            onClick={() => {
              setQuery("");
              setDateFilter("");
              setStatusFilter("all");
              setRange("upcoming");
            }}
          >
            Reset
          </button>
        </div>
        {loading ? (
          <div className="p-5 space-y-3">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </div>
        ) : !visible.length ? (
          <EmptyState
            icon={CalendarDays}
            title="No visits in this view"
            body="Try another range or reset your filters."
          />
        ) : (
          visible.map((r) => (
            <details key={r.id} className="portal-record">
              <summary
                aria-label={
                  "View visit: " +
                  r.serviceName +
                  ", " +
                  (r.client?.name ?? "Unknown client")
                }
              >
                <div className="flex flex-wrap items-center gap-4">
                  <div className="w-24 shrink-0 rounded-lg border border-purple-light/20 bg-surface/30 p-3 text-center">
                    <p className="text-xs text-muted">
                      {formatDate(r.appointmentDate)}
                    </p>
                    <p className="mt-2 text-sm text-gold">
                      {formatTime(r.appointmentDate)}
                    </p>
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="text-base text-white">{r.serviceName}</h3>
                    <p className="mt-1 text-xs text-muted">
                      {r.client?.name ?? "Unknown client"}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <StatusBadge status={r.status} />
                    <span className="text-xs text-muted">
                      {r.totalPrice === null
                        ? "Price to be confirmed"
                        : formatPeso(r.totalPrice)}
                    </span>
                  </div>
                  <ChevronDown size={17} className="text-gold" />
                </div>
              </summary>
              <div className="mt-5 grid gap-5 border-t border-purple-light/15 pt-5 lg:grid-cols-2">
                <div>
                  <h4 className="portal-section-title mb-3">Visit details</h4>
                  <p className="portal-help">
                    {r.client?.email ?? "No client email available"}
                  </p>
                  <AppointmentLookPreview look={r.look} />
                  <AppointmentServiceRecord record={r} />
                  {r.notes && (
                    <p className="mt-4 whitespace-pre-wrap rounded-lg bg-surface/30 p-4 text-sm text-secondary">
                      {r.notes}
                    </p>
                  )}
                </div>
                <div>
                  {["pending", "confirmed"].includes(r.status) ? (
                    <div className="rounded-lg border border-purple-light/20 p-4">
                      <h4 className="portal-section-title mb-3">
                        Manage service
                      </h4>
                      <p className="portal-help mb-4">
                        Record products used when completing the visit.
                      </p>
                      <ServiceCompletion
                        id={r.id}
                        disabled={!!busy}
                        onCompleted={load}
                        onBusyChange={setCompletionBusy}
                      />
                      <label className="mt-4 block text-xs text-muted">
                        Appointment status
                        <select
                          aria-label="Appointment status"
                          value={r.status}
                          onChange={(e) => {
                            if (
                              e.target.value !== "cancelled" ||
                              confirm(
                                "Cancel this appointment? This cannot be undone.",
                              )
                            )
                              void setStatus(
                                r.id,
                                e.target.value as AppointmentStatus,
                              );
                          }}
                          disabled={!!busy || completionBusy}
                        >
                          <option value="pending">Pending</option>
                          <option value="confirmed">Confirmed</option>
                          <option value="cancelled">Cancelled</option>
                        </select>
                      </label>
                    </div>
                  ) : (
                    <p className="portal-help rounded-lg border border-purple-light/15 p-4">
                      This visit is {r.status}. Its service history is
                      preserved.
                    </p>
                  )}
                </div>
              </div>
            </details>
          ))
        )}
        <PortalPagination
          page={current}
          pages={pages}
          total={filtered.length}
          onChange={setPage}
        />
      </section>
    </PortalWorkspace>
  );
}
