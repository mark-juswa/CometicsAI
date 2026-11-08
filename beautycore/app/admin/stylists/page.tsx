"use client";

import { useMemo, useState } from "react";
import {
  ArrowUpRight,
  CheckCircle2,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Users,
  Wallet,
} from "lucide-react";
import {
  Card,
  EmptyState,
  PageHeader,
  Skeleton,
  formatPeso,
} from "@/components/ui";
import {
  RevenuePeriodControls,
  useRevenueReport,
} from "@/components/revenue-report";
import { StylistAccountDialog } from "@/components/stylist-account-dialog";
import { StylistServiceDialog } from "@/components/stylist-service-dialog";
import { salonDay } from "@/lib/business/dates";
import type {
  RevenuePeriod,
  RevenueStylist,
} from "@/lib/business/revenue-periods";

const specialtyNames: Record<string, string> = {
  hair: "Hair",
  nail: "Nails",
  makeup: "Makeup",
  treatment: "Treatments",
  massage: "Massage",
  aesthetic: "Aesthetics",
};
const initials = (name: string) =>
  name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

export default function AdminStylistsPage() {
  const [history, setHistory] = useState<{ id: string; name: string } | null>(
    null,
  );
  const [period, setPeriod] = useState<RevenuePeriod>("month"),
    [date, setDate] = useState(salonDay);
  const { report, loading, error, refresh } = useRevenueReport(period, date);
  const [search, setSearch] = useState(""),
    [status, setStatus] = useState("all"),
    [sort, setSort] = useState("earnings");
  const [editor, setEditor] = useState<{
      stylist: RevenueStylist | null;
    } | null>(null),
    [notice, setNotice] = useState("");
  const rows = report?.stylists ?? [];
  const filtered = useMemo(
    () =>
      rows
        .filter((row) => {
          const matches =
            `${row.name} ${row.email} ${row.specialties.map((value) => specialtyNames[value] || value).join(" ")}`
              .toLowerCase()
              .includes(search.trim().toLowerCase());
          return (
            matches &&
            (status === "all" ||
              (status === "available" && row.isActive && row.workAvailable) ||
              (status === "unavailable" &&
                row.isActive &&
                !row.workAvailable) ||
              (status === "inactive" && !row.isActive))
          );
        })
        .sort(
          (a, b) =>
            (sort === "name"
              ? a.name.localeCompare(b.name)
              : sort === "completed"
                ? b.completed - a.completed
                : b.amount - a.amount) ||
            a.name.localeCompare(b.name) ||
            a.id.localeCompare(b.id),
        ),
    [rows, search, status, sort],
  );
  const teamAmount = rows.reduce((sum, row) => sum + row.amount, 0),
    completed = rows.reduce((sum, row) => sum + row.completed, 0),
    unpriced = rows.reduce((sum, row) => sum + row.unpriced, 0);
  const reference = new Date(
    (report?.window.date ?? salonDay()) + "T00:00:00Z",
  );
  const dayLabel = new Intl.DateTimeFormat("en-PH", {
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  }).format(reference);
  const monthLabel = new Intl.DateTimeFormat("en-PH", {
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(reference);
  const yearLabel = reference.getUTCFullYear();
  const figures = [
    {
      label: "Team service earnings",
      value: formatPeso(teamAmount),
      note: report?.window.label || "Selected period",
      icon: Wallet,
      accent: "text-gold",
    },
    {
      label: "Completed services",
      value: String(completed),
      note: unpriced
        ? `${unpriced} awaiting a recorded price`
        : "During the selected period",
      icon: CheckCircle2,
      accent: "text-success",
    },
    {
      label: "Available to work",
      value: String(
        rows.filter((row) => row.isActive && row.workAvailable).length,
      ),
      note: "Current work availability",
      icon: ArrowUpRight,
      accent: "text-info",
    },
    {
      label: "Active accounts",
      value: String(rows.filter((row) => row.isActive).length),
      note: `${rows.length} stylists in the roster`,
      icon: Users,
      accent: "text-purple-glow",
    },
  ];
  return (
    <>
      <PageHeader
        title="Stylists"
        subtitle="A clear view of your team, their service earnings, and work availability."
        action={
          <button
            type="button"
            onClick={() => {
              setNotice("");
              setEditor({ stylist: null });
            }}
            className="inline-flex items-center gap-2 rounded-lg bg-gold px-4 py-2.5 text-sm font-semibold text-deep hover:bg-gold-hover"
          >
            <Plus size={16} />
            Add stylist
          </button>
        }
      />
      {notice && (
        <p
          role="status"
          className="mb-5 rounded-lg border border-success/25 bg-success/10 px-4 py-3 text-sm text-success"
        >
          {notice}
        </p>
      )}
      <Card className="mb-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-[2px] text-gold">
              Team earnings
            </p>
            <h2 className="font-serif text-xl">
              {report?.window.label || "Choose a reporting period"}
            </h2>
          </div>
          <RevenuePeriodControls
            label="Stylist earnings"
            period={period}
            date={date}
            onPeriod={setPeriod}
            onDate={setDate}
            periods={["day", "month", "year"]}
          />
        </div>
      </Card>
      {error && (
        <p
          role="alert"
          className="mb-5 rounded-lg border border-error/30 bg-error/5 p-4 text-sm text-error"
        >
          {error}
          <button type="button" className="ml-3 underline" onClick={refresh}>
            Try again
          </button>
        </p>
      )}
      <div className="mb-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {loading
          ? Array.from({ length: 4 }, (_, index) => (
              <Skeleton key={index} className="h-32 w-full" />
            ))
          : figures.map((figure) => (
              <Card key={figure.label} className="relative">
                <div className="mb-4 flex items-center justify-between gap-3">
                  <p className="text-[10px] font-medium uppercase tracking-wider text-muted">
                    {figure.label}
                  </p>
                  <figure.icon size={15} className={figure.accent} />
                </div>
                <p className={`font-serif text-3xl ${figure.accent}`}>
                  {report ? figure.value : "—"}
                </p>
                <p className="mt-2 text-[11px] text-muted">
                  {report ? figure.note : "Report unavailable"}
                </p>
              </Card>
            ))}
      </div>
      <Card>
        <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="font-serif text-xl">Your team</h2>
            <p className="mt-1 text-xs text-muted">
              Day, month, and year figures follow the selected reference date.
            </p>
          </div>
          <button
            type="button"
            disabled={loading}
            onClick={refresh}
            className="inline-flex items-center gap-2 rounded-lg border border-purple-light/20 px-3 py-2 text-xs text-secondary hover:bg-surface/40"
          >
            <RefreshCw size={12} />
            Refresh
          </button>
        </div>
        <div className="mb-6 grid gap-3 md:grid-cols-[minmax(0,1fr)_190px_180px]">
          <label className="relative text-xs text-muted">
            <span className="sr-only">Search stylists</span>
            <Search
              size={14}
              className="pointer-events-none absolute left-3 top-[18px] text-muted"
            />
            <input
              aria-label="Search stylists"
              type="search"
              placeholder="Search name, email, or specialty"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </label>
          <label className="text-xs text-muted">
            <span className="sr-only">Filter stylist status</span>
            <select
              aria-label="Filter stylist status"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="all">All staff</option>
              <option value="available">Available to work</option>
              <option value="unavailable">Not available</option>
              <option value="inactive">Inactive accounts</option>
            </select>
          </label>
          <label className="text-xs text-muted">
            <span className="sr-only">Sort stylists</span>
            <select
              aria-label="Sort stylists"
              value={sort}
              onChange={(e) => setSort(e.target.value)}
            >
              <option value="earnings">Highest earnings</option>
              <option value="completed">Most services</option>
              <option value="name">Name A–Z</option>
            </select>
          </label>
        </div>
        {loading ? (
          <div className="space-y-3">
            {[0, 1, 2].map((index) => (
              <Skeleton key={index} className="h-20 w-full" />
            ))}
          </div>
        ) : error ? (
          <p className="rounded-lg border border-purple-light/15 p-5 text-sm text-muted">
            The team report is unavailable. Choose a valid date or try
            refreshing.
          </p>
        ) : !filtered.length ? (
          <EmptyState
            icon={Users}
            title={
              rows.length
                ? "No stylists match these filters"
                : "No stylists yet"
            }
            body={
              rows.length
                ? "Try another name, specialty, or status."
                : "Add a stylist to start managing your team and their earnings."
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] text-left">
              <thead>
                <tr>
                  <th>Stylist</th>
                  <th>Specialties</th>
                  <th>Work status</th>
                  <th className={period === "day" ? "text-gold" : ""}>
                    Day
                    <span className="mt-1 block text-[9px] font-normal normal-case tracking-normal text-muted">
                      {dayLabel}
                    </span>
                  </th>
                  <th className={period === "month" ? "text-gold" : ""}>
                    Month
                    <span className="mt-1 block text-[9px] font-normal normal-case tracking-normal text-muted">
                      {monthLabel}
                    </span>
                  </th>
                  <th className={period === "year" ? "text-gold" : ""}>
                    Year
                    <span className="mt-1 block text-[9px] font-normal normal-case tracking-normal text-muted">
                      {yearLabel}
                    </span>
                  </th>
                  <th>
                    <span className="sr-only">Manage account</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <div className="flex items-center gap-3">
                        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-purple-light/20 bg-purple/15 text-xs font-semibold text-secondary">
                          {initials(row.name)}
                        </span>
                        <div className="min-w-0">
                          <button
                            type="button"
                            onClick={() => setHistory(row)}
                            aria-label={`View services by ${row.name}`}
                            className="text-left text-sm font-medium text-white underline decoration-gold/40 underline-offset-4 hover:text-gold"
                          >
                            {row.name}
                          </button>
                          <p
                            className="mt-0.5 max-w-[210px] truncate text-[11px] text-muted"
                            title={row.email}
                          >
                            {row.email}
                          </p>
                          <p className="mt-1 text-[10px] text-muted">
                            {row.completed} completed · selected period
                            {row.unpriced > 0 && (
                              <span className="text-warning">
                                {" "}
                                · {row.unpriced} unpriced
                              </span>
                            )}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div className="flex max-w-[170px] flex-wrap gap-1.5">
                        {row.specialties.length ? (
                          row.specialties.map((value) => (
                            <span
                              key={value}
                              className="rounded-md border border-purple-light/15 bg-purple/10 px-2 py-1 text-[10px] text-secondary"
                            >
                              {specialtyNames[value] || value}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-warning">
                            No specialties assigned
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      <span
                        className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-1 text-[10px] ${!row.isActive ? "border-warning/25 bg-warning/10 text-warning" : row.workAvailable ? "border-success/20 bg-success/10 text-success" : "border-purple-light/20 bg-surface/20 text-muted"}`}
                      >
                        <span className="h-1.5 w-1.5 rounded-full bg-current" />
                        {!row.isActive
                          ? "Inactive account"
                          : row.workAvailable
                            ? "Available"
                            : "Not available"}
                      </span>
                    </td>
                    <td
                      className={`whitespace-nowrap text-sm tabular-nums ${period === "day" ? "bg-gold/5 font-semibold text-gold" : "text-secondary"}`}
                    >
                      {formatPeso(row.dayAmount)}
                    </td>
                    <td
                      className={`whitespace-nowrap text-sm tabular-nums ${period === "month" ? "bg-gold/5 font-semibold text-gold" : "text-secondary"}`}
                    >
                      {formatPeso(row.monthAmount)}
                    </td>
                    <td
                      className={`whitespace-nowrap text-sm tabular-nums ${period === "year" ? "bg-gold/5 font-semibold text-gold" : "text-secondary"}`}
                    >
                      {formatPeso(row.yearAmount)}
                    </td>
                    <td>
                      <button
                        type="button"
                        aria-label={`Edit ${row.name}`}
                        onClick={() => {
                          setNotice("");
                          setEditor({ stylist: row });
                        }}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-purple-light/20 px-3 py-1.5 text-xs text-secondary hover:border-gold/40 hover:text-gold"
                      >
                        <Pencil size={12} />
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="mt-5 flex flex-wrap justify-between gap-2 border-t border-purple-light/15 pt-4 text-[11px] text-muted">
          <p>
            {filtered.length} of {rows.length} stylists · Completed-service
            revenue · Philippine time
          </p>
          <p>Payroll and commission are not configured.</p>
        </div>
        {!!report?.summary.unassignedAmount && (
          <p className="mt-2 text-xs text-muted">
            {formatPeso(report.summary.unassignedAmount)} from unassigned
            completed services is included in salon revenue separately.
          </p>
        )}
      </Card>
      {history && (
        <StylistServiceDialog
          key={history.id}
          stylist={history}
          onClose={() => setHistory(null)}
        />
      )}
      {editor && (
        <StylistAccountDialog
          key={editor.stylist?.id || "new"}
          stylist={editor.stylist}
          onClose={() => setEditor(null)}
          onSaved={(message) => {
            setEditor(null);
            setNotice(message);
            refresh();
          }}
        />
      )}
    </>
  );
}
