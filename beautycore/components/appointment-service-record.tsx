'use client';
import { useRef, useState } from 'react';
import { businessRequest } from '../lib/business/client';
import type { AppointmentReview, ServiceRecord } from '../lib/business/workflow-types';
import { formatDate, formatTime } from './ui';
export function AppointmentServiceRecord({ record }: { record: ServiceRecord }) {
  return (
    <div className="mt-3 text-sm text-secondary">
      {record.completedAt && (
        <p>
          Completed {formatDate(record.completedAt)} at {formatTime(record.completedAt)}
        </p>
      )}
      {!!record.products?.length && (
        <div>
          <p className="font-semibold">Products used</p>
          <ul>
            {record.products.map((product, index) => (
              <li key={index}>
                {product.productName}
                {product.brand ? ` — ${product.brand}` : ''}
                {product.quantity !== null ? ` · ${product.quantity} ${product.unit}` : ''}
                {product.unitCost !== null ? ` · PHP ${product.unitCost} per ${product.unit}` : ''}
              </li>
            ))}
          </ul>
        </div>
      )}
      {record.review && <ReviewSummary review={record.review} />}
    </div>
  );
}
function ReviewSummary({ review }: { review: AppointmentReview }) {
  return (
    <div aria-label="Submitted review">
      <p>Client rating: {review.rating}/5</p>
      {review.comment && <p>{review.comment}</p>}
    </div>
  );
}
export function AppointmentReviewForm({
  id,
  review,
  onSubmitted,
}: {
  id: string;
  review?: AppointmentReview | null;
  onSubmitted: () => void;
}) {
  const [rating, setRating] = useState('');
  const [comment, setComment] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const lock = useRef(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError('');
    try {
      await businessRequest(`/api/appointments/${id}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating: Number(rating), comment: comment.trim() || null }),
      });
      setSubmitted(true);
      onSubmitted();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not submit your review.');
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  if (review) return null;
  if (submitted) return <p role="status">Your review has been submitted.</p>;
  return (
    <form
      onSubmit={submit}
      className="business-panel service-workflow-form"
      aria-label="Review completed appointment"
    >
      <h3>Rate your stylist</h3>
      <p className="text-sm text-secondary">
        One review per completed appointment. Check your review before submitting.
      </p>
      <label>
        Rating
        <select required value={rating} disabled={busy} onChange={(e) => setRating(e.target.value)}>
          <option value="">Choose 1–5</option>
          {[5, 4, 3, 2, 1].map((n) => (
            <option key={n} value={n}>
              {n} / 5
            </option>
          ))}
        </select>
      </label>
      <label>
        Review (optional)
        <textarea
          maxLength={1000}
          disabled={busy}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
      </label>
      <button type="submit" disabled={busy} className="studio-secondary-button">
        {busy ? 'Submitting…' : 'Submit review'}
      </button>
      {error && <p role="alert">{error}</p>}
    </form>
  );
}
