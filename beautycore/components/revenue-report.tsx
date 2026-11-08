"use client";
import { useCallback, useEffect, useId, useState } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  CalendarDays,
  RefreshCw,
  Wallet,
} from "lucide-react";
import { businessRequest } from "@/lib/business/client";
import { salonDay } from "@/lib/business/dates";
import {
  revenueWindow,
  REVENUE_PERIODS,
  type RevenuePeriod,
  type RevenueReport,
  type RevenueBucket,
} from "@/lib/business/revenue-periods";
import { useAppointmentRefresh } from "@/lib/business/use-appointment-refresh";
import { Card, Skeleton, formatPeso } from "@/components/ui";
const names: Record<RevenuePeriod, string> = {
  day: "Daily",
  week: "Weekly",
  month: "Monthly",
  year: "Yearly",
};

export function useRevenueReport(period: RevenuePeriod, date: string) {
  const [report, setReport] = useState<RevenueReport | null>(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [revision, setRevision] = useState(0);
  const refresh = useCallback(() => setRevision((value) => value + 1), []);
  useAppointmentRefresh(refresh);
  useEffect(() => {
    const controller = new AbortController();
    setError("");
    setReport(null);
    setLoading(true);
    try {
      revenueWindow(period, date);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Choose a valid reporting date.",
      );
      setLoading(false);
      return;
    }
    businessRequest(
      "/api/admin/stylist-performance?" + new URLSearchParams({ period, date }),
      { signal: controller.signal },
    )
      .then((data) => {
        if (!controller.signal.aborted) setReport(data);
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setError(cause.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [period, date, revision]);
  return { report, loading, error, refresh };
}

export function RevenuePeriodControls({
  period,
  date,
  onPeriod,
  onDate,
  periods = REVENUE_PERIODS,
  label = "Revenue",
}: {
  period: RevenuePeriod;
  date: string;
  onPeriod: (value: RevenuePeriod) => void;
  onDate: (value: string) => void;
  periods?: readonly RevenuePeriod[];
  label?: string;
}) {
  const dateId = useId();
  return (
    <div className="flex flex-wrap items-end gap-3">
      <div
        role="group"
        aria-label={`${label} period`}
        className="inline-flex flex-wrap gap-1 rounded-lg border border-purple-light/20 bg-deep/60 p-1"
      >
        {periods.map((value) => (
          <button
            key={value}
            type="button"
            aria-pressed={period === value}
            onClick={() => onPeriod(value)}
            className={`rounded-md px-3 py-2 text-xs font-medium transition-colors sm:px-4 ${period === value ? "bg-gold text-deep shadow-sm" : "text-muted hover:bg-surface/60 hover:text-white"}`}
          >
            {names[value]}
          </button>
        ))}
      </div>
      <label htmlFor={dateId} className="min-w-0 text-[11px] text-muted">
        <span className="flex items-center gap-1.5">
          <CalendarDays size={12} />
          Reference date · Philippine time
        </span>
        <input
          id={dateId}
          aria-label={`${label} reference date`}
          type="date"
          min="1900-01-01"
          max="2200-12-31"
          value={date}
          onChange={(e) => onDate(e.target.value)}
          className="mt-1.5 max-w-[200px]"
        />
      </label>
    </div>
  );
}

function RevenueChart({
  series,
  period,
}: {
  series: RevenueBucket[];
  period: RevenuePeriod;
}) {
  const [selectedKey, setSelectedKey] = useState("");
  const selected =
    series.find((row) => row.key === selectedKey) ??
    [...series].reverse().find((row) => row.amount > 0) ??
    series[0];
  const maximum = Math.max(1, ...series.map((row) => row.amount));
  return (
    <div className="min-w-0">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2 text-xs">
        <span className="text-muted">
          {period === "day"
            ? "Hourly"
            : period === "year"
              ? "Monthly"
              : "Daily"}{" "}
          revenue
        </span>
        <span className="text-muted">
          Peak{" "}
          {formatPeso(
            maximum === 1 && series.every((row) => row.amount === 0)
              ? 0
              : maximum,
          )}
        </span>
      </div>
      <div className="overflow-x-auto">
        <div
          className={`flex h-44 items-stretch gap-1 border-b border-purple-light/20 pt-2 ${series.length > 16 ? "min-w-[540px]" : "min-w-[300px]"}`}
          aria-label="Revenue trend chart"
        >
          {series.map((row, index) => (
            <button
              key={row.key}
              type="button"
              title={`${row.label}: ${formatPeso(row.amount)} · ${row.completed} completed services`}
              aria-label={`${row.label}: ${formatPeso(row.amount)}, ${row.completed} completed services`}
              aria-pressed={selected?.key === row.key}
              onClick={() => setSelectedKey(row.key)}
              className="group flex h-full min-w-0 flex-1 flex-col items-center justify-end rounded-t focus-visible:outline-gold"
            >
              <span className="flex min-h-0 w-full flex-1 items-end px-0.5">
                <span
                  className={`mx-auto block w-full max-w-8 rounded-t transition-colors ${row.amount === 0 ? "bg-purple-light/15" : selected?.key === row.key ? "bg-gold" : "bg-purple-light/65 group-hover:bg-gold/80"}`}
                  style={{
                    height:
                      row.amount === 0
                        ? "2px"
                        : `${Math.max(2, (row.amount / maximum) * 100)}%`,
                  }}
                />
              </span>
              <span className="mt-2 block h-5 text-[9px] text-muted">
                {series.length <= 12 ||
                index % Math.ceil(series.length / 7) === 0 ||
                index === series.length - 1
                  ? period === "day"
                    ? row.label.slice(0, 2)
                    : row.label
                  : ""}
              </span>
            </button>
          ))}
        </div>
      </div>
      {selected && (
        <p
          className="mt-3 flex min-h-6 flex-wrap items-center justify-between gap-2 text-xs"
          aria-live="polite"
        >
          <span className="text-secondary">
            {selected.label} · {selected.completed} completed{" "}
            {selected.completed === 1 ? "service" : "services"}
          </span>
          <span className="font-medium text-gold">
            {formatPeso(selected.amount)}
          </span>
        </p>
      )}
    </div>
  );
}

export function RevenueOverview() {
  const [period, setPeriod] = useState<RevenuePeriod>("month"),
    [date, setDate] = useState(salonDay);
  const { report, loading, error, refresh } = useRevenueReport(period, date);
  const summary = report?.summary;
  return (
    <Card className="mb-6 overflow-hidden border-purple-light/25">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-5">
        <div>
          <p className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[2px] text-gold">
            <Wallet size={14} />
            Business performance
          </p>
          <h2 className="font-serif text-2xl text-white">Total Revenue</h2>
        </div>
        <RevenuePeriodControls
          period={period}
          date={date}
          onPeriod={setPeriod}
          onDate={setDate}
        />
      </div>
      {error && (
        <div
          role="alert"
          className="rounded border border-error/30 bg-error/5 p-4 text-sm text-error"
        >
          {error}
          <button type="button" className="ml-3 underline" onClick={refresh}>
            Try again
          </button>
        </div>
      )}
      {loading ? (
        <div
          aria-label="Loading revenue"
          className="grid gap-6 lg:grid-cols-[.8fr_1.2fr]"
        >
          <Skeleton className="h-52 w-full" />
          <Skeleton className="h-52 w-full" />
        </div>
      ) : report && summary ? (
        <>
          <div className="grid gap-7 lg:grid-cols-[.8fr_1.2fr]">
            <div>
              <p className="text-sm text-secondary">{report.window.label}</p>
              <p
                className="mt-3 break-words font-serif text-4xl font-semibold tracking-tight text-white sm:text-5xl"
                aria-label="Selected period revenue"
              >
                {formatPeso(summary.amount)}
              </p>
              <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
                <span
                  className={`inline-flex items-center gap-1 rounded-full border px-2 py-1 ${summary.amount === summary.previousAmount ? "border-purple-light/20 text-muted" : summary.amount > summary.previousAmount ? "border-success/20 bg-success/10 text-success" : "border-error/20 bg-error/10 text-error"}`}
                >
                  {summary.amount ===
                  summary.previousAmount ? null : summary.amount >
                    summary.previousAmount ? (
                    <ArrowUpRight size={13} />
                  ) : (
                    <ArrowDownRight size={13} />
                  )}{" "}
                  {summary.amount === summary.previousAmount
                    ? "No change"
                    : summary.changePercent === null
                      ? formatPeso(
                          Math.abs(summary.amount - summary.previousAmount),
                        )
                      : `${Math.abs(summary.changePercent)}%`}
                </span>
                <span className="text-muted">
                  vs previous {period} · {formatPeso(summary.previousAmount)}
                </span>
              </div>
              <div className="mt-6 grid grid-cols-2 gap-4 border-t border-purple-light/15 pt-4">
                <div>
                  <p className="text-[10px] uppercase tracking-wide text-muted">
                    Completed services
                  </p>
                  <p className="mt-1 font-serif text-2xl text-white">
                    {summary.completed}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-wide text-muted">
                    Average service value
                  </p>
                  <p className="mt-1 font-serif text-2xl text-white">
                    {formatPeso(
                      summary.completed - summary.unpriced > 0
                        ? Math.round(
                            summary.amount /
                              (summary.completed - summary.unpriced),
                          )
                        : 0,
                    )}
                  </p>
                </div>
              </div>
            </div>
            <RevenueChart series={report.series} period={period} />
          </div>
          {summary.completed === 0 && (
            <p
              role="status"
              className="mt-4 rounded border border-purple-light/15 bg-deep/40 p-3 text-sm text-muted"
            >
              No completed services in this period. Choose another reference
              date or period.
            </p>
          )}
          {summary.unpriced > 0 && (
            <p className="mt-4 text-xs text-warning">
              {summary.unpriced} completed{" "}
              {summary.unpriced === 1 ? "service has" : "services have"} no
              recorded price and contribute no amount to this total.
            </p>
          )}
          <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-purple-light/15 pt-4 text-[11px] text-muted">
            <p>
              Completed-service values by scheduled service date · Asia/Manila
              <br />
              <span className="text-secondary">
                All-time revenue: {formatPeso(summary.allTimeAmount)}
              </span>
              {summary.unassignedAmount > 0 && (
                <span>
                  {" "}
                  · Includes {formatPeso(summary.unassignedAmount)} from
                  unassigned services
                </span>
              )}
            </p>
            <button
              type="button"
              onClick={refresh}
              className="inline-flex items-center gap-1.5 rounded border border-purple-light/20 px-3 py-1.5 text-xs text-secondary hover:bg-surface/40"
            >
              <RefreshCw size={12} />
              Refresh revenue
            </button>
          </div>
        </>
      ) : null}
    </Card>
  );
}
