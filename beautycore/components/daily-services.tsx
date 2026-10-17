'use client';
import { useEffect, useState } from 'react';
import { businessRequest } from '../lib/business/client';
import { salonDay } from '../lib/business/dates';
import { formatPeso, formatTime } from './ui';
type Summary = {
  serviceDay: string;
  stylistId: string | null;
  stylistName: string;
  completed: number;
  pending: number;
  confirmed: number;
  cancelled: number;
  unpriced: number;
  amount: number;
};
type Detail = {
  id: string;
  serviceDay: string;
  stylistName: string;
  clientName: string;
  serviceName: string;
  appointmentDate: string;
  status: string;
  totalPrice: number | null;
};
type Report = {
  summaries: Summary[];
  rows: Detail[];
  amount: number;
  unpriced: number;
  total: number;
};
export function DailyServices() {
  const [from, setFrom] = useState(salonDay());
  const [to, setTo] = useState(salonDay());
  const [stylist, setStylist] = useState('');
  const [status, setStatus] = useState('all');
  const [page, setPage] = useState(1);
  const [stylists, setStylists] = useState<{ id: string; name: string }[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    businessRequest('/api/stylists')
      .then((data) => {
        if (active) setStylists(data.stylists);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);
  useEffect(() => {
    const c = new AbortController();
    setLoading(true);
    setError('');
    const params = new URLSearchParams({ from, to, status, page: String(page) });
    if (stylist) params.set('stylist', stylist);
    businessRequest('/api/admin/daily-services?' + params, { signal: c.signal })
      .then((data) => {
        if (!c.signal.aborted) setReport(data);
      })
      .catch((cause) => {
        if (!c.signal.aborted) {
          setError(cause.message);
          setReport(null);
        }
      })
      .finally(() => {
        if (!c.signal.aborted) setLoading(false);
      });
    return () => c.abort();
  }, [from, to, stylist, status, page]);
  return (
    <section className="business-panel" aria-labelledby="daily-services-title">
      <h2 id="daily-services-title">Daily Services by Stylist</h2>
      <p className="mb-4 text-sm text-secondary">
        Scheduled service dates in Philippine time (Asia/Manila). Amounts are recorded
        completed-service values, not payments received.
      </p>
      <div className="business-filters">
        <label>
          From date
          <input
            type="date"
            value={from}
            onChange={(e) => {
              setFrom(e.target.value);
              setPage(1);
            }}
          />
        </label>
        <label>
          Through date
          <input
            type="date"
            value={to}
            min={from}
            onChange={(e) => {
              setTo(e.target.value);
              setPage(1);
            }}
          />
        </label>
        <label>
          Stylist
          <select
            value={stylist}
            onChange={(e) => {
              setStylist(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All stylists</option>
            <option value="unassigned">Unassigned</option>
            {stylists.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Status
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
          >
            {['all', 'pending', 'confirmed', 'completed', 'cancelled'].map((s) => (
              <option key={s} value={s}>
                {s === 'all' ? 'All statuses' : s}
              </option>
            ))}
          </select>
        </label>
      </div>
      {error && (
        <p role="alert" className="studio-alert">
          {error}
        </p>
      )}
      {loading ? (
        <p role="status">Loading daily services…</p>
      ) : (
        report && (
          <>
            <p className="mb-4">
              <strong>{formatPeso(Number(report.amount))}</strong> recorded completed-service amount
              · {report.unpriced} completed service(s) awaiting a recorded price.
            </p>
            {!report.summaries.length ? (
              <p>No services match these filters.</p>
            ) : (
              <div className="business-table-wrap">
                <table className="business-table">
                  <caption className="sr-only">Daily service totals by stylist</caption>
                  <thead>
                    <tr>
                      {[
                        'Service date',
                        'Stylist',
                        'Completed',
                        'Pending',
                        'Confirmed',
                        'Cancelled',
                        'Unpriced completed',
                        'Recorded amount',
                      ].map((h) => (
                        <th key={h} scope="col">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {report.summaries.map((s) => (
                      <tr key={s.serviceDay + (s.stylistId ?? 'unassigned')}>
                        <td>{s.serviceDay}</td>
                        <td>{s.stylistName}</td>
                        <td>{s.completed}</td>
                        <td>{s.pending}</td>
                        <td>{s.confirmed}</td>
                        <td>{s.cancelled}</td>
                        <td>{s.unpriced}</td>
                        <td>{formatPeso(Number(s.amount))}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <details className="mt-5" open>
              <summary className="cursor-pointer text-gold">
                Service details ({report.total})
              </summary>
              <div className="business-table-wrap">
                <table className="business-table">
                  <thead>
                    <tr>
                      {[
                        'Service date',
                        'Time',
                        'Stylist',
                        'Client',
                        'Service',
                        'Status',
                        'Recorded amount',
                      ].map((h) => (
                        <th key={h} scope="col">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {report.rows.map((row) => (
                      <tr key={row.id}>
                        <td>{row.serviceDay}</td>
                        <td>{formatTime(row.appointmentDate)}</td>
                        <td>{row.stylistName}</td>
                        <td>{row.clientName}</td>
                        <td>{row.serviceName}</td>
                        <td>{row.status}</td>
                        <td>
                          {row.totalPrice === null
                            ? 'Price to be confirmed'
                            : formatPeso(row.totalPrice)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
            <div className="business-pagination">
              <button disabled={page === 1} onClick={() => setPage(page - 1)}>
                Previous services
              </button>
              <span>
                Page {page} · {report.total} services
              </span>
              <button disabled={page * 12 >= report.total} onClick={() => setPage(page + 1)}>
                Next services
              </button>
            </div>
          </>
        )
      )}
    </section>
  );
}
