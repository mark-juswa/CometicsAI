"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  CalendarDays,
  CheckCircle2,
  Clock,
  Search,
  SlidersHorizontal,
  UserRound,
  RefreshCw,
} from "lucide-react";
import { AdminAppointmentDialog } from "@/components/admin-appointment-dialog";
import {
  PageHeader,
  StatusBadge,
  EmptyState,
  Skeleton,
  formatDate,
  formatTime,
  formatPeso,
} from "@/components/ui";
import {
  PortalWorkspace,
  PortalMetrics,
  PortalPagination,
} from "@/components/portal-workspace";
import { businessRequest } from "@/lib/business/client";
import { useAppointmentRefresh } from "@/lib/business/use-appointment-refresh";
import {
  appointmentCounts,
  filterAppointments,
  DEFAULT_APPOINTMENT_FILTERS,
  type AppointmentFilters,
  type AdminAppointment,
  type AdminStylistOption,
} from "@/lib/business/appointment-list";
import { appointmentStatusEnum } from "@/db/schema";

export default function AdminAppointmentsPage() {
  const [rows, setRows] = useState<AdminAppointment[]>([]),
    [stylists, setStylists] = useState<AdminStylistOption[]>([]),
    [directoryReady, setDirectoryReady] = useState(false);
  const [loading, setLoading] = useState(true),
    [refreshing, setRefreshing] = useState(false),
    [error, setError] = useState(""),
    [directoryError, setDirectoryError] = useState(""),
    [notice, setNotice] = useState("");
  const [filters, setFilters] = useState<AppointmentFilters>({
      ...DEFAULT_APPOINTMENT_FILTERS,
    }),
    [advanced, setAdvanced] = useState(false),
    [page, setPage] = useState(1),
    [selected, setSelected] = useState<string | null>(null);
  const request = useRef(0);
  const load = useCallback(async () => {
    const version = ++request.current;
    setRefreshing(true);
    try {
      const data = await businessRequest("/api/appointments");
      if (version === request.current) {
        setRows(data.appointments ?? []);
        setError("");
      }
    } catch (cause) {
      if (version === request.current)
        setError(
          cause instanceof Error
            ? cause.message
            : "Could not load appointments.",
        );
    } finally {
      if (version === request.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, []);
  useEffect(() => {
    void load();
    let active = true;
    businessRequest("/api/stylists?manage=true")
      .then((data) => {
        if (active) {
          setStylists(data.stylists ?? []);
          setDirectoryReady(true);
        }
      })
      .catch(() => {
        if (active)
          setDirectoryError(
            "The stylist directory could not be loaded. Assignment changes are temporarily unavailable.",
          );
      });
    return () => {
      active = false;
      request.current++;
    };
  }, [load]);
  useAppointmentRefresh(load);
  const counts = appointmentCounts(rows),
    filtered = useMemo(
      () => filterAppointments(rows, filters),
      [rows, filters],
    );
  const pages = Math.max(1, Math.ceil(filtered.length / 12)),
    current = Math.min(page, pages),
    visible = filtered.slice((current - 1) * 12, current * 12),
    appointment = rows.find((row) => row.id === selected);
  const update = (patch: Partial<AppointmentFilters>) => {
    setFilters((previous) => ({ ...previous, ...patch }));
    setPage(1);
  };
  const changed = async (message: string) => {
    await load();
    setNotice(message);
  };
  return (
    <PortalWorkspace>
      <PageHeader
        title="Appointments"
        subtitle="A clear view of every visit, from booking to completion."
      />
      <PortalMetrics
        items={[
          {
            label: "Scheduled today",
            value: loading ? "—" : counts.today,
            icon: CalendarDays,
            note: "Philippine time",
          },
          {
            label: "Upcoming visits",
            value: loading ? "—" : counts.upcoming,
            icon: Clock,
            note: "Pending and confirmed",
          },
          {
            label: "Needs assignment",
            value: loading ? "—" : counts.unassigned,
            icon: UserRound,
            note: "Active bookings",
          },
          {
            label: "Completed services",
            value: loading ? "—" : counts.completed,
            icon: CheckCircle2,
            note: "All recorded visits",
          },
        ]}
      />
      {error && (
        <div role="alert" className="portal-alert">
          {error}{" "}
          <button onClick={() => void load()} className="underline">
            Try again
          </button>
        </div>
      )}
      {directoryError && (
        <p role="alert" className="portal-alert">
          {directoryError}
        </p>
      )}
      {notice && (
        <p role="status" className="portal-notice">
          {notice}
        </p>
      )}
      <section className="portal-panel">
        <div className="portal-panel-heading">
          <div>
            <h2>Booking register</h2>
            <p>{rows.length} bookings · times shown in the Philippines</p>
          </div>
          <button
            className="portal-button"
            disabled={refreshing}
            onClick={() => void load()}
          >
            <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
        <div className="portal-tabs" aria-label="Appointment views">
          {(
            [
              ["all", "All bookings"],
              ["today", "Today"],
              ["upcoming", "Upcoming"],
              ["unassigned", "Needs assignment"],
            ] as const
          ).map(([value, label]) => (
            <button
              key={value}
              aria-pressed={filters.view === value}
              onClick={() =>
                update({
                  view: value,
                  sort: value === "upcoming" ? "soonest" : filters.sort,
                })
              }
            >
              {label}
            </button>
          ))}
        </div>
        <div className="portal-toolbar">
          <label className="portal-search">
            <Search size={16} />
            <input
              aria-label="Search appointments"
              placeholder="Search client, service, or stylist"
              value={filters.query}
              onChange={(event) => update({ query: event.target.value })}
            />
          </label>
          <select
            aria-label="Filter by status"
            value={filters.status}
            onChange={(event) =>
              update({
                status: event.target.value as AppointmentFilters["status"],
              })
            }
          >
            <option value="all">All statuses</option>
            {appointmentStatusEnum.enumValues.map((value) => (
              <option key={value} value={value}>
                {value[0].toUpperCase() + value.slice(1)}
              </option>
            ))}
          </select>
          <button
            className="portal-button"
            aria-expanded={advanced}
            onClick={() => setAdvanced((value) => !value)}
          >
            <SlidersHorizontal size={14} />
            Filters
          </button>
        </div>
        {advanced && (
          <div className="portal-filter-grid">
            <label>
              From date
              <input
                type="date"
                value={filters.from}
                onChange={(event) => update({ from: event.target.value })}
              />
            </label>
            <label>
              Through date
              <input
                type="date"
                value={filters.to}
                onChange={(event) => update({ to: event.target.value })}
              />
            </label>
            <label>
              Service
              <select
                aria-label="Filter by service"
                value={filters.service}
                onChange={(event) => update({ service: event.target.value })}
              >
                <option value="all">All services</option>
                {[...new Set(rows.map((row) => row.serviceType))]
                  .sort()
                  .map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
              </select>
            </label>
            <label>
              Stylist
              <select
                aria-label="Filter by stylist"
                value={filters.stylist}
                onChange={(event) => update({ stylist: event.target.value })}
              >
                <option value="all">All stylists</option>
                <option value="unassigned">Unassigned</option>
                {stylists.map((stylist) => (
                  <option key={stylist.id} value={stylist.id}>
                    {stylist.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Sort by
              <select
                value={filters.sort}
                onChange={(event) =>
                  update({
                    sort: event.target.value as AppointmentFilters["sort"],
                  })
                }
              >
                <option value="latest">Latest scheduled first</option>
                <option value="soonest">Earliest scheduled first</option>
                <option value="client">Client name</option>
              </select>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={filters.unpriced}
                onChange={(event) => update({ unpriced: event.target.checked })}
              />
              Amount unconfirmed
            </label>
          </div>
        )}
        <div className="flex items-center justify-between gap-3 px-5 py-3 text-xs text-muted">
          <p>{filtered.length} matching bookings</p>
          <button
            className="text-gold hover:underline"
            onClick={() => {
              setFilters({ ...DEFAULT_APPOINTMENT_FILTERS });
              setPage(1);
            }}
          >
            Reset filters
          </button>
        </div>
        {filters.from && filters.to && filters.from > filters.to && (
          <p role="alert" className="portal-alert mx-5">
            The end date must be on or after the start date.
          </p>
        )}
        {loading ? (
          <div className="p-5 space-y-3">
            {[0, 1, 2].map((value) => (
              <Skeleton key={value} className="h-20 w-full" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={CalendarDays}
            title="No appointments match"
            body="Choose another view or reset the filters."
          />
        ) : (
          <div className="portal-table-scroll">
            <table className="portal-table">
              <thead>
                <tr>
                  <th>Visit</th>
                  <th>Client</th>
                  <th>Service & stylist</th>
                  <th>Recorded amount</th>
                  <th>Status</th>
                  <th>
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {visible.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <strong>{formatDate(row.appointmentDate)}</strong>
                      <span>
                        {formatTime(row.appointmentDate)} ·{" "}
                        {row.durationMinutes ?? 60} min
                      </span>
                    </td>
                    <td>
                      <strong>{row.client?.name ?? "Unknown client"}</strong>
                      <span>{row.client?.email ?? "Email unavailable"}</span>
                    </td>
                    <td>
                      <strong>{row.serviceName}</strong>
                      <span className={!row.stylistId ? "text-gold" : ""}>
                        {row.stylist?.name ?? "Needs assignment"}
                      </span>
                    </td>
                    <td>
                      <strong className="text-gold">
                        {row.totalPrice === null
                          ? "Unconfirmed"
                          : formatPeso(row.totalPrice)}
                      </strong>
                    </td>
                    <td>
                      <StatusBadge status={row.status} />
                    </td>
                    <td>
                      <button
                        className="portal-button"
                        aria-label={`View details for ${row.serviceName}, ${row.client?.name ?? "unknown client"}`}
                        onClick={() => {
                          setNotice("");
                          setSelected(row.id);
                        }}
                      >
                        View details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <PortalPagination
          page={current}
          pages={pages}
          total={filtered.length}
          onChange={setPage}
        />
      </section>
      {appointment && (
        <AdminAppointmentDialog
          key={appointment.id}
          appointment={appointment}
          stylists={stylists}
          directoryReady={directoryReady}
          onClose={() => setSelected(null)}
          onChanged={changed}
          onDeleted={async (id) => {
            setRows((previous) => previous.filter((row) => row.id !== id));
            setSelected(null);
            await changed("Appointment deleted.");
          }}
        />
      )}
    </PortalWorkspace>
  );
}
