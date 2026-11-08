'use client';
import Link from 'next/link';
import { businessRequest } from '@/lib/business/client';

import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Search, Users, Mail, CalendarDays } from 'lucide-react';
import {
  PageHeader,
  Card,
  EmptyState,
  Skeleton,
  formatDate,
  formatPeso,
} from '@/components/ui';

interface ClientRow {
  id: string;
  name: string;
  email: string;
  avatar: string | null;
  createdAt: string;
  appointmentCount: number;
  totalSpent: number;
  phone: string | null;
  isActive: boolean;
}

export default function AdminClientsPage() {
  const [rows, setRows] = useState<ClientRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('all');
  const [sort, setSort] = useState('newest');
  const [error, setError] = useState('');

  useEffect(() => {
    businessRequest('/api/users?role=client')
      .then((d) => setRows(d.users ?? []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return rows.filter(r => (!q || `${r.name} ${r.email} ${r.phone||''}`.toLowerCase().includes(q)) && (filter==='all'||filter==='active'&&r.isActive||filter==='inactive'&&!r.isActive||filter==='booked'&&r.appointmentCount>0||filter==='unbooked'&&r.appointmentCount===0)).sort((a,b)=>sort==='name'?a.name.localeCompare(b.name):sort==='spent'?Number(b.totalSpent)-Number(a.totalSpent):Date.parse(b.createdAt)-Date.parse(a.createdAt));
  }, [rows, query, filter, sort]);

  const initials = (name: string) =>
    name
      .split(' ')
      .map((n) => n[0])
      .slice(0, 2)
      .join('')
      .toUpperCase();

  return (
    <>
      <PageHeader title="Clients" subtitle={`${rows.length} registered clients`} />
      {error&&<p role="alert" className="mb-4 text-error">{error}</p>}
      <div className="mb-4 grid max-w-xl gap-3 sm:grid-cols-2"><label className="text-xs text-muted">Clients<select value={filter} onChange={e=>setFilter(e.target.value)}><option value="all">All clients</option><option value="active">Active accounts</option><option value="inactive">Inactive accounts</option><option value="booked">With bookings</option><option value="unbooked">No bookings yet</option></select></label><label className="text-xs text-muted">Sort by<select value={sort} onChange={e=>setSort(e.target.value)}><option value="newest">Newest accounts</option><option value="name">Client name</option><option value="spent">Completed service value</option></select></label></div>

      <div className="relative mb-6 max-w-md">
        <Search
          size={14}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted"
        />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by name or email…"
          className="w-full rounded-sm border border-purple-light/20 bg-surface/40 py-2.5 pl-9 pr-4 text-[13px] text-white placeholder-muted focus:border-purple-light focus:outline-none"
        />
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-40 w-full" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <EmptyState
            icon={Users}
            title={query ? 'No clients match' : 'No clients yet'}
            body={query ? 'Try a different search.' : undefined}
          />
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((c, i) => (
            <motion.div
              key={c.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: Math.min(i * 0.04, 0.3) }}
            >
              <Link href={`/admin/clients/${c.id}`} className="block h-full rounded focus-visible:outline focus-visible:outline-gold hover:ring-1 hover:ring-purple-light"><Card className="h-full">
                <div className="mb-4 flex items-center gap-3">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-purple text-[13px] font-semibold text-white">
                    {initials(c.name)}
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-[14px] font-medium text-white">{c.name}</p>
                    <p className="flex items-center gap-1 truncate text-[11px] text-muted">
                      <Mail size={10} />
                      {c.email}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 border-t border-purple-light/10 pt-4">
                  <div>
                    <p className="mb-0.5 text-[10px] uppercase tracking-wide text-muted">
                      Bookings
                    </p>
                    <p className="text-[15px] text-white">{c.appointmentCount}</p>
                  </div>
                  <div>
                    <p className="mb-0.5 text-[10px] uppercase tracking-wide text-muted">
                      Completed value
                    </p>
                    <p className="text-[15px] text-gold">{formatPeso(c.totalSpent)}</p>
                  </div>
                </div>

                <p className="mt-4 flex items-center gap-1.5 text-[10px] text-muted">
                  <CalendarDays size={10} />
                  Joined {formatDate(c.createdAt)}
                </p>
              </Card></Link>
            </motion.div>
          ))}
        </div>
      )}
    </>
  );
}
