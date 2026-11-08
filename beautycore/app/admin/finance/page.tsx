"use client";
import { useEffect, useState } from "react";
import { businessRequest } from "@/lib/business/client";
import { Skeleton, formatPeso } from "@/components/ui";
import {
  BarChart3,
  Receipt,
  Scissors,
  Users,
  ArrowUpRight,
} from "lucide-react";
import { PaymentHistory } from "@/components/payment-history";
import { StylistPerformance } from "@/components/stylist-performance";
import { DailyServices } from "@/components/daily-services";
import { RevenueOverview } from "@/components/revenue-report";
import { PortalWorkspace } from "@/components/portal-workspace";
import Link from "next/link";
const sections = [
  {
    id: "revenue",
    title: "Revenue overview",
    icon: BarChart3,
    description:
      "Explore completed-service revenue by day, week, month, or year. Compare periods and inspect the chart for each date.",
  },
  {
    id: "payments",
    title: "Payment receipts",
    icon: Receipt,
    description:
      "Review recorded payment receipts separately from the service amounts shown in revenue reports.",
  },
  {
    id: "services",
    title: "Daily services",
    icon: Scissors,
    description:
      "Review the actual services completed on a chosen date, including recorded amounts and products used.",
  },
  {
    id: "team",
    title: "Team performance",
    icon: Users,
    description:
      "Compare completed services and recorded revenue attributed to each stylist over a selected date range.",
  },
] as const;
export default function AdminFinancePage() {
  const [active, setActive] =
    useState<(typeof sections)[number]["id"]>("revenue");
  const section = sections.find((section) => section.id === active)!;
  return (
    <PortalWorkspace className="finance-workspace">
      <header className="portal-hero">
        <div>
          <p className="portal-eyebrow">Business overview</p>
          <h1>Finance</h1>
          <p>
            Understand service revenue, review receipts, and follow your team’s
            contribution in one place.
          </p>
        </div>
        <Link href="/admin/stylists" className="portal-button">
          Stylist earnings
          <ArrowUpRight size={15} />
        </Link>
      </header>
      <nav className="finance-navigation" aria-label="Finance reports">
        {sections.map((item) => (
          <button
            key={item.id}
            aria-pressed={active === item.id}
            onClick={() => setActive(item.id)}
          >
            <item.icon size={20} />
            <span>{item.title}</span>
            <ArrowUpRight size={14} />
          </button>
        ))}
      </nav>
      <div className="mb-6">
        <h2 className="portal-section-title">{section.title}</h2>
        <p className="portal-help mt-2 max-w-3xl">{section.description}</p>
      </div>
      <div key={active}>
        {active === "revenue" ? (
          <>
            <RevenueOverview />
            <FinanceInsights />
          </>
        ) : active === "payments" ? (
          <PaymentHistory />
        ) : active === "services" ? (
          <DailyServices />
        ) : (
          <StylistPerformance />
        )}
      </div>
      <p className="portal-help rounded-xl border border-purple-light/15 p-4">
        Service revenue uses recorded amounts on completed appointments. Receipt
        totals reflect payments entered separately. Unconfirmed prices are
        excluded from monetary totals.
      </p>
    </PortalWorkspace>
  );
}

function FinanceInsights() {
  const [data, setData] = useState<{
    statusBreakdown: { status: string; n: number }[];
    topServices: { serviceName: string; serviceType?:string; bookings: number; revenue: number }[];
  } | null>(null);
  const [error, setError] = useState(""),
    [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setError("");
    businessRequest("/api/admin/stats", { signal: controller.signal })
      .then((value) => {
        if (!controller.signal.aborted) setData(value);
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setError(cause.message);
      });
    return () => controller.abort();
  }, [revision]);
  if (error)
    return (
      <p role="alert" className="portal-alert">
        {error}{" "}
        <button
          className="underline"
          onClick={() => setRevision((value) => value + 1)}
        >
          Retry service insights
        </button>
      </p>
    );
  if (!data) return <Skeleton className="mb-6 h-48 w-full" />;
  const total = data.statusBreakdown.reduce(
      (sum, row) => sum + Number(row.n),
      0,
    ),
    max = Math.max(1, ...data.topServices.map((row) => row.revenue));
  const colours: Record<string, string> = {
    completed: "bg-info",
    confirmed: "bg-success",
    pending: "bg-warning",
    cancelled: "bg-error",
  };
  return (
    <div className="portal-grid">
      <section className="portal-panel">
        <div className="portal-panel-heading">
          <div>
            <h2>Service performance</h2>
            <p>Popular services · all-time completed-service revenue</p>
          </div>
        </div>
        <div className="portal-inset space-y-5">
          {data.topServices.length ? (
            data.topServices.map((service, index) => (
              <div key={service.serviceType+':'+service.serviceName}>
                <div className="mb-2 flex items-start justify-between gap-4 text-sm">
                  <span className="text-secondary">
                    <span className="mr-3 text-xs text-muted">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    {service.serviceName}
                  </span>
                  <span className="text-gold">
                    {formatPeso(service.revenue)}
                  </span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-purple/20">
                  <div
                    className="h-full rounded-full bg-gold/70"
                    style={{ width: (service.revenue / max) * 100 + "%" }}
                  />
                </div>
                <p className="mt-2 text-[11px] text-muted">
                  {service.bookings} bookings across all statuses
                </p>
              </div>
            ))
          ) : (
            <p className="portal-help">No service bookings recorded yet.</p>
          )}
        </div>
      </section>
      <section className="portal-panel">
        <div className="portal-panel-heading">
          <div>
            <h2>Booking status</h2>
            <p>{total} bookings across all dates</p>
          </div>
        </div>
        <div className="portal-inset">
          <div
            aria-hidden="true"
            className="mb-6 flex h-3 overflow-hidden rounded-full bg-surface/50"
          >
            {data.statusBreakdown.map((row) => (
              <span
                key={row.status}
                className={colours[row.status] ?? "bg-purple-light"}
                style={{
                  width: (total ? (Number(row.n) / total) * 100 : 0) + "%",
                }}
              />
            ))}
          </div>
          <ul className="space-y-4">
            {["completed", "confirmed", "pending", "cancelled"].map(
              (status) => {
                const count = Number(
                  data.statusBreakdown.find((row) => row.status === status)
                    ?.n ?? 0,
                );
                return (
                  <li
                    key={status}
                    className="flex items-center justify-between border-b border-purple-light/10 pb-4 text-sm last:border-0"
                  >
                    <span className="flex items-center gap-3 capitalize text-secondary">
                      <span
                        className={"h-2 w-2 rounded-full " + colours[status]}
                      />
                      {status}
                    </span>
                    <span className="text-white">
                      {count}
                      <span className="ml-3 text-xs text-muted">
                        {total ? Math.round((count / total) * 100) : 0}%
                      </span>
                    </span>
                  </li>
                );
              },
            )}
          </ul>
        </div>
      </section>
    </div>
  );
}
