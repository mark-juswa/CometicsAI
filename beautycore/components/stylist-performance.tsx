'use client';
import { useEffect, useState } from 'react';
import { businessRequest } from '../lib/business/client';
import { salonDay } from '../lib/business/dates';
import { formatPeso } from './ui';
type Stylist = {
  id: string;
  name: string;
  completed: number;
  amount: number;
  unpriced: number;
  rating: number | null;
  reviews: number;
};
export function StylistPerformance() {
  const [from, setFrom] = useState(() => salonDay().slice(0, 7) + '-01');
  const [to, setTo] = useState(salonDay());
  const [sort, setSort] = useState('completed');
  const [rows, setRows] = useState<Stylist[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError('');
    businessRequest('/api/admin/stylist-performance?' + new URLSearchParams({ from, to }), {
      signal: controller.signal,
    })
      .then((data) => {
        if (!controller.signal.aborted) setRows(data.stylists);
      })
      .catch((cause) => {
        if (!controller.signal.aborted) {
          setRows([]);
          setError(cause.message);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [from, to]);
  const sorted = [...rows].sort(
    (a, b) =>
      (sort === 'rating'
        ? (b.rating ?? -1) - (a.rating ?? -1) || b.reviews - a.reviews || b.completed - a.completed
        : b.completed - a.completed) ||
      a.name.localeCompare(b.name) ||
      a.id.localeCompare(b.id),
  );
  return (
    <section className="business-panel" aria-labelledby="stylist-performance-title">
      <h2 id="stylist-performance-title">Stylist Performance</h2>
      <p className="text-sm text-secondary">
        Completed appointments by scheduled service date in Philippine time. Ratings come from
        reviews of those appointments. Amounts are recorded service values, not payments or net
        profit.
      </p>
      <div className="business-filters">
        <label>
          Performance from
          <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
        </label>
        <label>
          Performance through
          <input type="date" value={to} min={from} onChange={(e) => setTo(e.target.value)} />
        </label>
        <label>
          Sort stylists by
          <select value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="completed">Completed services</option>
            <option value="rating">Average client rating</option>
          </select>
        </label>
      </div>
      <p className="my-2 text-sm text-secondary">
        {sort === 'completed'
          ? 'Highest completed count first; ties use name.'
          : 'Highest average first; ties use review count, completed count, then name. Unrated stylists appear last. Compare review counts before drawing conclusions.'}
      </p>
      {error && <p role="alert">{error}</p>}
      {loading ? (
        <p role="status">Loading stylist performance…</p>
      ) : (
        !error && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr>
                  {[
                    'Stylist',
                    'Completed',
                    'Average rating',
                    'Reviews',
                    'Recorded amount',
                    'Unpriced',
                  ].map((name) => (
                    <th key={name} className="p-2">
                      {name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sorted.map((stylist) => (
                  <tr key={stylist.id}>
                    <td className="p-2">{stylist.name}</td>
                    <td className="p-2">{stylist.completed}</td>
                    <td className="p-2">
                      {stylist.rating === null
                        ? 'Unrated'
                        : `${Number(stylist.rating).toFixed(2)} / 5`}
                    </td>
                    <td className="p-2">{stylist.reviews}</td>
                    <td className="p-2">{formatPeso(Number(stylist.amount))}</td>
                    <td className="p-2">{stylist.unpriced}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!sorted.length && <p>No stylists found.</p>}
          </div>
        )
      )}
    </section>
  );
}
