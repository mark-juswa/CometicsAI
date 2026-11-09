"use client";
import { useEffect, useRef, useState } from "react";
import { businessRequest } from "../lib/business/client";
import { PRODUCT_UNITS } from "../lib/business/workflow-types";
type CatalogProduct = {
  id: string;
  productName: string;
  brand?: string | null;
  unit?: string;
  itemType?: string;
};
type Line = {
  configured?: boolean;
  consumeStock?: boolean;
  adjustmentReason?: string;
  inventoryId: string;
  productName: string;
  brand: string;
  quantity: string;
  unit: string;
  unitCost: string;
};
const blank = (): Line => ({
  inventoryId: "",
  productName: "",
  brand: "",
  quantity: "",
  unit: "",
  unitCost: "",
});
export function ServiceCompletion({
  id,
  onCompleted,
  disabled = false,
  initiallyOpen = false,
  onBusyChange,
}: {
  id: string;
  onCompleted: () => void | Promise<void>;
  disabled?: boolean;
  initiallyOpen?: boolean;
  onBusyChange?: (busy: boolean) => void;
}) {
  const [open, setOpen] = useState(initiallyOpen);
  const [catalog, setCatalog] = useState<CatalogProduct[]>([]);
  const [lines, setLines] = useState<Line[]>([]);
  const [reportedOnly, setReportedOnly] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [requirementsLoading, setRequirementsLoading] = useState(false);
  const [requirementsError, setRequirementsError] = useState("");
  const [requirementsRevision, setRequirementsRevision] = useState(0);
  const [catalogError, setCatalogError] = useState("");
  const lock = useRef(false);
  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setRequirementsLoading(true);
    setRequirementsError("");
    businessRequest(
      "/api/inventory/requirements?appointmentId=" + encodeURIComponent(id),
      { signal: controller.signal },
    )
      .then((data) => {
        if (!controller.signal.aborted) {
          const onlyReported = data.consumptionMode !== "configured";
          setReportedOnly(onlyReported);
          setLines(
            onlyReported ? [] : data.requirements.map((r: any) => ({
              inventoryId: r.id,
              productName: r.productName,
              brand: r.brand ?? "",
              quantity: String(r.estimatedQuantity),
              unit: r.unit,
              unitCost: "",
              configured: true,
              consumeStock: true,
              adjustmentReason: "",
            })),
          );
        }
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setRequirementsError(
            "Service requirements could not be loaded. Retry before completing this service.",
          );
      })
      .finally(() => {
        if (!controller.signal.aborted) setRequirementsLoading(false);
      });
    businessRequest("/api/inventory?limit=250&active=true", {
      signal: controller.signal,
    })
      .then((data) => setCatalog(data.inventory ?? []))
      .catch(() => {
        if (!controller.signal.aborted)
          setCatalogError(
            "Inventory could not be loaded. You can still enter the actual products by name.",
          );
      });
    return () => controller.abort();
  }, [open, id, requirementsRevision]);
  function update(index: number, patch: Partial<Line>) {
    setLines((current) =>
      current.map((line, i) => (i === index ? { ...line, ...patch } : line)),
    );
  }
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (lock.current || disabled) return;
    lock.current = true;
    setBusy(true);
    onBusyChange?.(true);
    setError("");
    try {
      await businessRequest(`/api/appointments/${id}/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          products: lines.map((line) => ({
            inventoryId: line.inventoryId || null,
            consumeStock: line.consumeStock === true,
            adjustmentReason: line.adjustmentReason || null,
            productName: line.productName,
            brand: line.brand || null,
            quantity: line.quantity === "" ? null : Number(line.quantity),
            unit: line.unit || null,
            unitCost: line.unitCost === "" ? null : Number(line.unitCost),
          })),
        }),
      });
      window.dispatchEvent(new Event("inventory-updated"));
      setOpen(false);
      await onCompleted();
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Could not complete this service.",
      );
    } finally {
      lock.current = false;
      setBusy(false);
      onBusyChange?.(false);
    }
  }
  if (!open)
    return (
      <button
        type="button"
        className="studio-secondary-button"
        disabled={disabled || busy}
        onClick={() => setOpen(true)}
      >
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
        {reportedOnly ? "Only add products that were used up during this service and their quantities. You do not need to list every product used. Only the reported quantities are deducted when completion is confirmed. Leave this empty if nothing was used up. Reusable tools are not deducted." : "Record the products actually used. Configured consumables are deducted when you confirm completion. Tools are never consumed. Explain actual quantity changes."}
      </p>
      {requirementsLoading && (
        <p role="status">Loading configured service supplies…</p>
      )}
      {requirementsError && (
        <p role="alert">
          {requirementsError}{" "}
          <button
            type="button"
            onClick={() => setRequirementsRevision((r) => r + 1)}
          >
            Retry service supplies
          </button>
        </p>
      )}
      {catalogError && <p role="status">{catalogError}</p>}
      {lines.map((line, index) => (
        <fieldset
          key={index}
          disabled={busy || disabled}
          className="my-3 grid gap-2 rounded border border-purple-light/20 p-3 sm:grid-cols-2"
        >
          <legend>Product {index + 1}</legend>
          <label>
            Inventory product
            <select
              value={line.inventoryId}
              required={reportedOnly}
              disabled={line.configured}
              onChange={(e) => {
                const item = catalog.find(
                  (product) => product.id === e.target.value,
                );
                update(index, {
                  inventoryId: e.target.value,
                  ...(item
                    ? {
                        productName: item.productName,
                        brand: item.brand ?? "",
                        unit: item.unit ?? "",
                        consumeStock: reportedOnly,
                      }
                    : {}),
                });
              }}
            >
              <option value="">{reportedOnly ? "Choose a product that was used up" : "Unlisted product / enter name"}</option>
              {catalog.filter(item => !reportedOnly || item.itemType !== "equipment").map((item) => (
                <option key={item.id} value={item.id}>
                  {item.productName}
                  {item.brand ? ` (${item.brand})` : ""}
                </option>
              ))}
            </select>
          </label>
          {!reportedOnly && <><label>
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
          </label></>}
          <label>
            {reportedOnly ? "Quantity used up" : "Quantity used"}
            <input
              type="number"
              required={reportedOnly}
              min={line.configured ? "0" : "0.001"}
              max="1000000"
              step="0.001"
              value={line.quantity}
              onChange={(e) => update(index, { quantity: e.target.value })}
            />
          </label>
          <label>
            Unit
            <select
              disabled={reportedOnly}
              required={line.quantity !== "" || line.unitCost !== ""}
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
          {!reportedOnly && <><label>
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
          <label className="sm:col-span-2">
            Reason for actual quantity change (required when different from the
            estimate)
            <input
              maxLength={1000}
              value={line.adjustmentReason ?? ""}
              onChange={(e) =>
                update(index, { adjustmentReason: e.target.value })
              }
            />
          </label></>}
          {!reportedOnly && !line.configured && line.inventoryId && (
            <label>
              <input
                type="checkbox"
                checked={line.consumeStock ?? false}
                onChange={(e) =>
                  update(index, { consumeStock: e.target.checked })
                }
              />{" "}
              Deduct this additional product from stock (quantity and reason
              required)
            </label>
          )}
          {line.configured && (
            <p className="text-xs text-muted">
              Configured requirement. Set quantity to zero and explain if it was
              not used.
            </p>
          )}
          <button
            type="button"
            disabled={line.configured}
            className="studio-text-button"
            onClick={() =>
              setLines((current) => current.filter((_, i) => i !== index))
            }
          >
            Remove product {index + 1}
          </button>
        </fieldset>
      ))}
      <div className="my-3 flex flex-wrap gap-2">
        <button
          type="button"
          className="studio-secondary-button"
          disabled={
            busy ||
            disabled ||
            requirementsLoading ||
            !!requirementsError ||
            lines.length >= 50
          }
          onClick={() => setLines((current) => [...current, blank()])}
        >
          {reportedOnly ? "Add finished product" : "Add product used"}
        </button>
        <button
          type="submit"
          className="studio-primary-button"
          disabled={
            busy || disabled || requirementsLoading || !!requirementsError
          }
        >
          {busy ? "Completing…" : "Confirm completion"}
        </button>
        <button
          type="button"
          className="studio-secondary-button"
          disabled={busy || disabled}
          onClick={() => setOpen(false)}
        >
          Keep appointment open
        </button>
      </div>
      {error && <p role="alert">{error}</p>}
    </form>
  );
}
