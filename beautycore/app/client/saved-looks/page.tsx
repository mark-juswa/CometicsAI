'use client';
import { LookInformation } from '@/components/look-information';
import { featureFromType } from '@/lib/business/look-information';
import Image from 'next/image';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { PageHeader, Card } from '@/components/ui';
import { businessRequest, type SavedLook } from '@/lib/business/client';
export default function SavedLooksPage() {
  const [looks, setLooks] = useState<SavedLook[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [feature, setFeature] = useState('');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);
  const [busy, setBusy] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError('');
    const params = new URLSearchParams({ page: String(page) });
    if (feature) params.set('feature', feature);
    if (from) params.set('from', from);
    if (to) params.set('to', to);
    businessRequest('/api/saved-looks?' + params, { signal: controller.signal })
      .then((data) => {
        if (controller.signal.aborted) return;
        setLooks(data.looks);
        setTotal(data.total);
        if (!data.looks.length && page > 1) setPage(page - 1);
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setError(cause.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [page, feature, from, to, refresh]);
  async function remove(look: SavedLook) {
    if (
      !confirm(
        'Remove from My Saved Looks? Existing appointments will keep this reference for your stylist.',
      )
    )
      return;
    setBusy(look.id);
    setError('');
    try {
      await businessRequest(`/api/saved-looks/${look.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ saved: false }),
      });
      setRefresh((v) => v + 1);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not remove the look.');
    } finally {
      setBusy('');
    }
  }
  return (
    <>
      <PageHeader
        title="My Saved Looks"
        subtitle="Your saved previews, ready to revisit or bring to an appointment."
      />
      <section className="business-panel">
        <div className="business-filters">
          <label>
            Feature
            <select
              value={feature}
              onChange={(e) => {
                setFeature(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All features</option>
              <option value="hairstyle">Hairstyle</option>
              <option value="makeup">Makeup</option>
              <option value="nails">Nails</option>
            </select>
          </label>
          <label>
            Saved from
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
            Saved through
            <input
              type="date"
              value={to}
              onChange={(e) => {
                setTo(e.target.value);
                setPage(1);
              }}
            />
          </label>
        </div>
        <p className="text-sm text-secondary">
          Removing a look from this gallery keeps it attached to appointments already booked.
        </p>
      </section>
      {error && (
        <p role="alert" className="studio-alert">
          {error}
        </p>
      )}
      {loading ? (
        <p role="status">Loading saved looks…</p>
      ) : error ? null : !looks.length ? (
        <Card>
          <p>No saved looks yet. Save a completed preview from any AI studio or Consultation.</p>
        </Card>
      ) : (
        <div className="saved-gallery">
          {looks.map((look) => (
            <article className="business-panel" key={look.id}>
              <div className="relative mb-4 h-64">
                <Image
                  src={look.imageUrl}
                  fill
                  unoptimized
                  sizes="(max-width: 900px) 100vw, 33vw"
                  alt={look.styleName}
                  className="object-contain"
                />
              </div>
              <h2>{look.styleName}</h2>
              <LookInformation saved feature={featureFromType(look.styleType)} styleId={look.styleId} details={look.lookDetails} />
              <p className="text-sm text-secondary">
                {look.styleType === 'nail'
                  ? 'Nails'
                  : look.styleType === 'hair'
                    ? 'Hairstyle'
                    : 'Makeup'}{' '}
                · {new Date(look.savedAt).toLocaleDateString('en-PH', { timeZone: 'Asia/Manila' })}
              </p>
              <div className="mt-4 flex flex-wrap gap-3">
                <Link className="studio-primary-button" href={`/booking?look=${look.id}`}>
                  Book This Look
                </Link>
                <a
                  className="studio-secondary-button"
                  href={look.imageUrl}
                  target="_blank"
                  rel="noreferrer"
                >
                  View image
                </a>
                <a
                  className="studio-secondary-button"
                  href={look.imageUrl}
                  download={`andreas-${look.styleId}`}
                >
                  Download
                </a>
                <button
                  type="button"
                  className="studio-secondary-button"
                  disabled={busy === look.id}
                  onClick={() => void remove(look)}
                >
                  Remove from Saved
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
      <div className="business-pagination">
        <button disabled={loading || page === 1} onClick={() => setPage(page - 1)}>
          Previous
        </button>
        <span>
          Page {page} · {total} saved looks
        </span>
        <button disabled={loading || page * 12 >= total} onClick={() => setPage(page + 1)}>
          Next
        </button>
      </div>
    </>
  );
}
