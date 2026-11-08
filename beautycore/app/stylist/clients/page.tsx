"use client";
import { PortalWorkspace, PortalMetrics } from "@/components/portal-workspace";
import { businessRequest } from "@/lib/business/client";

import { useState, useEffect, useMemo } from "react";
import {
  Search,
  Users,
  Mail,
  CalendarDays,
  Repeat,
  CheckCircle2,
  Wallet,
} from "lucide-react";
import {
  PageHeader,
  Card,
  EmptyState,
  Skeleton,
  formatDate,
  formatPeso,
} from "@/components/ui";
import type { AppointmentStatus } from "@/db/schema";

interface Row {
  id: string;
  serviceName: string;
  appointmentDate: string;
  status: AppointmentStatus;
  totalPrice: number | null;
  client: { id: string; name: string; email: string } | null;
}

interface ClientSummary {
  id: string;
  name: string;
  email: string;
  visits: number;
  lastVisit: string;
  totalSpent: number;
  services: string[];
}

/**
 * Stylists see clients derived from their own appointments, not the full
 * directory — they should only know about people they actually serve.
 */
export default function StylistClientsPage() {
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("recent");

  useEffect(() => {
    businessRequest("/api/appointments")
      .then((d) => setRows(d.appointments ?? []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const clients = useMemo(() => {
    const map = new Map<string, ClientSummary>();

    for (const r of rows) {
      if (!r.client) continue;
      const existing = map.get(r.client.id);

      if (existing) {
        existing.visits += 1;
        if (r.status === "completed") existing.totalSpent += r.totalPrice ?? 0;
        if (new Date(r.appointmentDate) > new Date(existing.lastVisit)) {
          existing.lastVisit = r.appointmentDate;
        }
        if (!existing.services.includes(r.serviceName)) {
          existing.services.push(r.serviceName);
        }
      } else {
        map.set(r.client.id, {
          id: r.client.id,
          name: r.client.name,
          email: r.client.email,
          visits: 1,
          lastVisit: r.appointmentDate,
          totalSpent: r.status === "completed" ? (r.totalPrice ?? 0) : 0,
          services: [r.serviceName],
        });
      }
    }

    return Array.from(map.values()).sort(
      (a, b) =>
        new Date(b.lastVisit).getTime() - new Date(a.lastVisit).getTime(),
    );
  }, [rows]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return clients
      .filter(
        (c) =>
          !q ||
          c.name.toLowerCase().includes(q) ||
          c.email.toLowerCase().includes(q),
      )
      .sort((a, b) =>
        sort === "name"
          ? a.name.localeCompare(b.name)
          : sort === "visits"
            ? b.visits - a.visits
            : Date.parse(b.lastVisit) - Date.parse(a.lastVisit),
      );
  }, [clients, query, sort]);

  const initials = (name: string) =>
    name
      .split(" ")
      .map((n) => n[0])
      .slice(0, 2)
      .join("")
      .toUpperCase();

  return (
    <PortalWorkspace>
      <PageHeader
        title="My Clients"
        subtitle="People connected to your assigned appointments."
      />
      {error && (
        <p role="alert" className="portal-alert">
          {error}
        </p>
      )}
      <PortalMetrics
        items={[
          {
            label: "Your clients",
            value: loading ? "—" : clients.length,
            icon: Users,
            note: "Assigned bookings only",
          },
          {
            label: "Returning clients",
            value: loading ? "—" : clients.filter((c) => c.visits > 1).length,
            icon: Repeat,
            note: "More than one assigned booking",
          },
          {
            label: "Completed visits",
            value: loading
              ? "—"
              : rows.filter((r) => r.status === "completed").length,
            icon: CheckCircle2,
            note: "Services you completed",
          },
          {
            label: "Recorded service revenue",
            value: loading
              ? "—"
              : formatPeso(clients.reduce((sum, c) => sum + c.totalSpent, 0)),
            icon: Wallet,
            note: "Completed amounts · before any costs",
          },
        ]}
      />
      <section className="portal-panel">
        <div className="portal-panel-heading">
          <div>
            <h2>Client directory</h2>
            <p>
              Only appointments assigned to you contribute to these summaries.
            </p>
          </div>
          <span className="portal-pill">{filtered.length} clients</span>
        </div>
        <div className="portal-toolbar">
          <label className="portal-search">
            <Search size={16} />
            <input
              value={query}
              aria-label="Search clients"
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search name or email"
            />
          </label>
          <select
            aria-label="Sort clients"
            value={sort}
            onChange={(e) => setSort(e.target.value)}
          >
            <option value="recent">Latest scheduled first</option>
            <option value="name">Name A–Z</option>
            <option value="visits">Most bookings</option>
          </select>
        </div>
        {loading ? (
          <div className="p-5">
            <Skeleton className="h-48 w-full" />
          </div>
        ) : !filtered.length ? (
          <EmptyState
            icon={Users}
            title="No clients found"
            body="Your assigned clients will appear here. Try another search."
          />
        ) : (
          <div className="portal-table-scroll">
            <table className="portal-table">
              <thead>
                <tr>
                  <th>Client</th>
                  <th>Bookings</th>
                  <th>Latest scheduled visit</th>
                  <th>Services</th>
                  <th>Completed-service amount</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((c) => (
                  <tr key={c.id}>
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-purple/40 text-xs text-gold">
                          {initials(c.name)}
                        </div>
                        <div>
                          <strong>{c.name}</strong>
                          <span className="mt-1 block text-xs text-muted">
                            {c.email}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <strong>{c.visits}</strong>
                      <span>assigned to you</span>
                    </td>
                    <td>
                      <strong>{formatDate(c.lastVisit)}</strong>
                    </td>
                    <td>
                      <div className="flex min-w-40 max-w-72 flex-wrap gap-1.5">
                        {c.services.map((name) => (
                          <span key={name} className="portal-pill">
                            {name}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td>
                      <strong className="text-gold">
                        {formatPeso(c.totalSpent)}
                      </strong>
                      <span>Recorded completed amounts</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </PortalWorkspace>
  );
}
