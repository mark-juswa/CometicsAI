'use client';
import { AppointmentServiceRecord } from '@/components/appointment-service-record';
import type { ServiceRecord } from '@/lib/business/workflow-types';
import { useAppointmentRefresh } from '@/lib/business/use-appointment-refresh';

import { AppointmentLookPreview, type AppointmentLook } from '@/components/appointment-look';

import { ServiceCompletion } from '@/components/service-completion';
import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Search, CalendarDays, Clock } from 'lucide-react';
import {
  PageHeader,
  Card,
  StatusBadge,
  EmptyState,
  Skeleton,
  formatDate,
  formatTime,
  formatPeso,
} from '@/components/ui';
import { type AppointmentStatus } from '@/db/schema';

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

type Range = 'upcoming' | 'past' | 'all';

export default function StylistAppointmentsPage() {
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [range, setRange] = useState<Range>('upcoming');
  const [busy, setBusy] = useState<string | null>(null);
  const [actionError, setActionError] = useState('');

  const load = () => {
    fetch('/api/appointments')
      .then((r) => r.json())
      .then((d) => setRows(d.appointments ?? []))
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  };
  useEffect(load, []);
  useAppointmentRefresh(load);

  const setStatus = async (id: string, status: AppointmentStatus) => {
    setBusy(id);
    setActionError('');
    try {
      const res = await fetch(`/api/appointments/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) throw new Error((await res.json()).error || 'Could not update the appointment.');
      if (res.ok) setRows((rs) => rs.map((r) => (r.id === id ? { ...r, status } : r)));
    } catch (cause) {
      setActionError(cause instanceof Error ? cause.message : 'Could not update the appointment.');
    } finally {
      setBusy(null);
    }
  };

  const now = Date.now();
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return rows
      .filter((r) => {
        const t = new Date(r.appointmentDate).getTime();
        if (range === 'upcoming') return t >= now && ['pending', 'confirmed'].includes(r.status);
        if (range === 'past') return t < now || ['cancelled', 'completed'].includes(r.status);
        return true;
      })
      .filter(
        (r) =>
          !q || r.serviceName.toLowerCase().includes(q) || r.client?.name.toLowerCase().includes(q),
      )
      .sort(
        (a, b) => new Date(a.appointmentDate).getTime() - new Date(b.appointmentDate).getTime(),
      );
  }, [rows, query, range, now]);

  return (
    <>
      <PageHeader
        title="My Appointments"
        subtitle={`${rows.length} appointments assigned to you`}
      />

      <div className="mb-6 flex flex-wrap gap-3">
        <div className="relative min-w-[220px] flex-1">
          <Search
            size={14}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted"
          />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search client or service…"
            className="w-full rounded-sm border border-purple-light/20 bg-surface/40 py-2.5 pl-9 pr-4 text-[13px] text-white placeholder-muted focus:border-purple-light focus:outline-none"
          />
        </div>

        <div className="flex gap-1 rounded-sm border border-purple-light/15 bg-surface/30 p-1">
          {(['upcoming', 'past', 'all'] as const).map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`relative rounded-sm px-4 py-2 text-[11px] font-medium capitalize tracking-[1px] transition-colors ${
                range === r ? 'text-white' : 'text-muted hover:text-secondary'
              }`}
            >
              {range === r && (
                <motion.span
                  layoutId="stylist-range"
                  className="absolute inset-0 rounded-sm bg-purple/30"
                />
              )}
              <span className="relative">{r}</span>
            </button>
          ))}
        </div>
      </div>

      {actionError && <p role="alert">{actionError}</p>}
      {loading ? (
        <div className="flex flex-col gap-3">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <EmptyState
            icon={CalendarDays}
            title="Nothing here"
            body="Try a different range or search."
          />
        </Card>
      ) : (
        <div className="flex flex-col gap-3">
          {filtered.map((r, i) => (
            <motion.div
              key={r.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: Math.min(i * 0.04, 0.25) }}
            >
              <Card className="flex flex-wrap items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="mb-2 flex flex-wrap items-center gap-3">
                    <h3 className="font-serif text-lg text-white">{r.serviceName}</h3>
                    <StatusBadge status={r.status} />
                  </div>
                  <p className="mb-1 text-[12px] text-secondary">
                    {r.client?.name ?? 'Unknown client'}
                  </p>
                  <p className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-muted">
                    <span className="flex items-center gap-1.5">
                      <CalendarDays size={11} />
                      {formatDate(r.appointmentDate)}
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Clock size={11} />
                      {formatTime(r.appointmentDate)}
                    </span>
                    <span className="text-white">
                      {r.totalPrice === null ? 'Price to be confirmed' : formatPeso(r.totalPrice)}
                    </span>
                  </p>
                  <AppointmentLookPreview look={r.look} />
                  <AppointmentServiceRecord record={r} />
                  {r.notes && (
                    <p className="mt-2 rounded-sm border border-purple-light/10 bg-surface/25 p-2.5 text-[12px] leading-relaxed text-secondary">
                      {r.notes}
                    </p>
                  )}
                </div>

                <div className="flex w-full flex-col items-stretch gap-2 lg:max-w-lg">
                  {['pending', 'confirmed'].includes(r.status) && (
                    <ServiceCompletion id={r.id} onCompleted={load} />
                  )}
                  <select
                    value={r.status}
                    onChange={(e) => setStatus(r.id, e.target.value as AppointmentStatus)}
                    disabled={busy === r.id || ['completed', 'cancelled'].includes(r.status)}
                    aria-label="Appointment status"
                    className="rounded-sm border border-purple-light/20 bg-surface/40 px-3 py-2 text-[11px] text-white focus:border-purple-light focus:outline-none disabled:opacity-50"
                  >
                    {(
                      [
                        'pending',
                        'confirmed',
                        'cancelled',
                        ...(r.status === 'completed' ? ['completed'] : []),
                      ] as AppointmentStatus[]
                    ).map((s) => (
                      <option key={s} value={s}>
                        {s.charAt(0).toUpperCase() + s.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </>
  );
}
