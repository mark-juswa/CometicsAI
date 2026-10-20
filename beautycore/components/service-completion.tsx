'use client';
import { useEffect, useRef, useState } from 'react';
import { businessRequest } from '../lib/business/client';
import { PRODUCT_UNITS } from '../lib/business/workflow-types';
type CatalogProduct = { id: string; productName: string; brand?: string | null };
type Line = {
  inventoryId: string;
  productName: string;
  brand: string;
  quantity: string;
  unit: string;
  unitCost: string;
};
const blank = (): Line => ({
  inventoryId: '',
  productName: '',
  brand: '',
  quantity: '',
  unit: '',
  unitCost: '',
});
export function ServiceCompletion({ id, onCompleted }: { id: string; onCompleted: () => void }) {
  const [open, setOpen] = useState(false);
  const [catalog, setCatalog] = useState<CatalogProduct[]>([]);
  const [lines, setLines] = useState<Line[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [catalogError, setCatalogError] = useState('');
  const lock = useRef(false);
  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    businessRequest('/api/inventory', { signal: controller.signal })
      .then((data) => setCatalog(data.inventory ?? []))
      .catch(() => {
        if (!controller.signal.aborted)
          setCatalogError(
            'Inventory could not be loaded. You can still enter the actual products by name.',
          );
      });
    return () => controller.abort();
  }, [open]);
  function update(index: number, patch: Partial<Line>) {
    setLines((current) => current.map((line, i) => (i === index ? { ...line, ...patch } : line)));
  }
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError('');
    try {
      await businessRequest(`/api/appointments/${id}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          products: lines.map((line) => ({
            inventoryId: line.inventoryId || null,
            productName: line.productName,
            brand: line.brand || null,
            quantity: line.quantity === '' ? null : Number(line.quantity),
            unit: line.unit || null,
            unitCost: line.unitCost === '' ? null : Number(line.unitCost),
          })),
        }),
      });
      setOpen(false);
      onCompleted();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not complete this service.');
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  if (!open)
    return (
      <button type="button" className="studio-secondary-button" onClick={() => setOpen(true)}>
        Mark as Completed
      </button>
    );
  return (
    <form
      onSubmit={submit}
      className="business-panel service-workflow-form"
      aria-label="Complete service"
    >
      <h3>Complete service</h3>
      <p className="text-sm text-secondary">
        Record the products actually used. Product lines, quantities and material costs are
        optional. Leave unknown values blank. Stock is updated separately by the admin.
      </p>
      {catalogError && <p role="status">{catalogError}</p>}
      {lines.map((line, index) => (
        <fieldset
          key={index}
          disabled={busy}
          className="my-3 grid gap-2 rounded border border-purple-light/20 p-3 sm:grid-cols-2"
        >
          <legend>Product {index + 1}</legend>
          <label>
            Inventory product
            <select
              value={line.inventoryId}
              onChange={(e) => {
                const item = catalog.find((product) => product.id === e.target.value);
                update(index, {
                  inventoryId: e.target.value,
                  ...(item ? { productName: item.productName, brand: item.brand ?? '' } : {}),
                });
              }}
            >
              <option value="">Unlisted product / enter name</option>
              {catalog.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.productName}
                  {item.brand ? ` (${item.brand})` : ''}
                </option>
              ))}
            </select>
          </label>
          <label>
            Product name
            <input
              required
              maxLength={255}
              value={line.productName}
              onChange={(e) => update(index, { productName: e.target.value })}
            />
          </label>
          <label>
            Brand
            <input
              maxLength={120}
              value={line.brand}
              onChange={(e) => update(index, { brand: e.target.value })}
            />
          </label>
          <label>
            Quantity used
            <input
              type="number"
              min="0.001"
              max="1000000"
              step="0.001"
              value={line.quantity}
              onChange={(e) => update(index, { quantity: e.target.value })}
            />
          </label>
          <label>
            Unit
            <select
              required={line.quantity !== '' || line.unitCost !== ''}
              value={line.unit}
              onChange={(e) => update(index, { unit: e.target.value })}
            >
              <option value="">Choose unit</option>
              {PRODUCT_UNITS.map((unit) => (
                <option key={unit} value={unit}>
                  {unit}
                </option>
              ))}
            </select>
          </label>
          <label>
            Material cost per selected unit (PHP)
            <input
              type="number"
              min="0"
              max="1000000"
              step="0.01"
              value={line.unitCost}
              onChange={(e) => update(index, { unitCost: e.target.value })}
            />
          </label>
          <button
            type="button"
            className="studio-text-button"
            onClick={() => setLines((current) => current.filter((_, i) => i !== index))}
          >
            Remove product {index + 1}
          </button>
        </fieldset>
      ))}
      <div className="my-3 flex flex-wrap gap-2">
        <button
          type="button"
          className="studio-secondary-button"
          disabled={busy || lines.length >= 20}
          onClick={() => setLines((current) => [...current, blank()])}
        >
          Add product used
        </button>
        <button type="submit" className="studio-primary-button" disabled={busy}>
          {busy ? 'Completing…' : 'Confirm completion'}
        </button>
        <button
          type="button"
          className="studio-secondary-button"
          disabled={busy}
          onClick={() => setOpen(false)}
        >
          Keep appointment open
        </button>
      </div>
      {error && <p role="alert">{error}</p>}
    </form>
  );
}
