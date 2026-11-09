"use client";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { businessRequest } from "../lib/business/client";
import { salonDay } from "../lib/business/dates";
import { INVENTORY_REFERENCE } from "../lib/business/inventory-reference";
import { PageHeader, formatPeso, formatDate } from "./ui";
type Product = {
  id: string;
  productName: string;
  category: string;
  brand: string | null;
  sku?: string | null;
  itemType: "consumable" | "equipment";
  unit: string;
  currentStock: number;
  minimumThreshold: number;
  maximumStock?: number | null;
  purchaseCost?: number | null;
  sellingPrice?: number | null;
  supplierId?: string | null;
  supplierName?: string | null;
  location?: string | null;
  expirationDate?: string | null;
  active: boolean;
  imageUrl?: string | null;
  description?: string | null;
  expired?: boolean;
  expiringSoon?: boolean;
  estimatedQuantity?: number;
  status: string;
};
type Supplier = {
  id: string;
  name: string;
  contact?: string;
  email?: string;
  phone?: string;
  address?: string;
  notes?: string;
  active: boolean;
};
type Service = {
  id: string;
  name: string;
  groupLabel: string;
  serviceType: string;
};
type Modal = {
  kind: "product" | "movement" | "supplier" | "detail" | "remove";
  item?: Product;
  supplier?: Supplier;
  preset?: {
    name: string;
    purpose: string;
    category: string;
    equipment?: boolean;
  };
} | null;
const units = [
  "piece",
  "bottle",
  "tube",
  "pack",
  "pair",
  "set",
  "g",
  "kg",
  "ml",
  "l",
  "application",
];
const kinds = [
  "stock_in",
  "stock_out",
  "adjustment",
  "service_consumption",
  "correction",
  "damaged",
  "expired",
  "initial_stock",
];
const caption = (s: string) => s.replaceAll("_", " "),
  money = (v: number | null | undefined) =>
    v == null ? "—" : formatPeso(Number(v));
const inputStyle =
  "mt-1 w-full rounded border border-purple-light/25 bg-deep p-2 text-sm text-white";
function Field({
  label,
  value,
  onChange,
  type = "text",
  required = false,
  step,
  maxLength,
}: {
  label: string;
  value: string;
  onChange: (s: string) => void;
  type?: string;
  required?: boolean;
  step?: string;
  maxLength?: number;
}) {
  return (
    <label className="block text-xs text-secondary">
      {label}
      <input
        className={inputStyle}
        type={type}
        min={type === "number" ? "0" : undefined}
        step={step}
        value={value}
        required={required}
        maxLength={maxLength}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}
function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (s: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <label className="block text-xs text-secondary">
      {label}
      <select
        className={inputStyle}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}
function Stock({ item }: { item: Product }) {
  return (
    <div className="space-y-1">
      <span
        className={`inline-block rounded-full border px-2 py-1 text-xs ${!item.active ? "border-purple-light/30 text-muted" : item.expired || Number(item.currentStock) === 0 ? "border-error/40 text-error" : Number(item.currentStock) <= Number(item.minimumThreshold) ? "border-warning/40 text-warning" : "border-success/30 text-success"}`}
      >
        {!item.active
          ? "Inactive"
          : item.expired
            ? "Expired"
            : Number(item.currentStock) === 0
              ? "Out of stock"
              : Number(item.currentStock) <= Number(item.minimumThreshold)
                ? "Low stock"
                : "In stock"}
      </span>
      {item.expiringSoon && (
        <p className="text-xs text-warning">Expiring soon</p>
      )}
    </div>
  );
}
function Frame({
  title,
  close,
  children,
}: {
  title: string;
  close: () => void;
  children: ReactNode;
}) {
  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [close]);
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-3">
      <section
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-xl border border-purple-light/25 bg-deep p-5 shadow-xl"
      >
        <div className="mb-5 flex items-center justify-between gap-4">
          <h2 className="font-serif text-xl text-white">{title}</h2>
          <button
            type="button"
            aria-label="Close inventory dialog"
            onClick={close}
            className="studio-text-button"
          >
            Close
          </button>
        </div>
        {children}
      </section>
    </div>
  );
}

export function InventoryWorkspace({
  readOnly = false,
}: {
  readOnly?: boolean;
}) {
  const [historyProduct, setHistoryProduct] = useState("");
  const [categories, setCategories] = useState<string[]>([]);
  const [tab, setTab] = useState("products"),
    [items, setItems] = useState<Product[]>([]),
    [total, setTotal] = useState(0),
    [page, setPage] = useState(1),
    [q, setQ] = useState(""),
    [category, setCategory] = useState(""),
    [type, setType] = useState(""),
    [stock, setStock] = useState(""),
    [active, setActive] = useState("true"),
    [attention, setAttention] = useState(false),
    [sort, setSort] = useState("name");
  const [summary, setSummary] = useState<any>(null),
    [services, setServices] = useState<Service[]>([]),
    [suppliers, setSuppliers] = useState<Supplier[]>([]),
    [modal, setModal] = useState<Modal>(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [revision, setRevision] = useState(0);
  const refresh = () => {
    setRevision((r) => r + 1);
    window.dispatchEvent(new Event("inventory-updated"));
  };
  useEffect(() => {
    if (new URLSearchParams(window.location.search).get("attention") === "1")
      setAttention(true);
  }, []);
  useEffect(() => {
    setPage(1);
  }, [q, category, type, stock, active, attention, sort]);
  useEffect(() => {
    const c = new AbortController();
    setLoading(true);
    setError("");
    const params = new URLSearchParams({
      page: String(page),
      limit: "24",
      sort,
    });
    if (q) params.set("q", q);
    if (category) params.set("category", category);
    if (type) params.set("type", type);
    if (stock) params.set("stock", stock);
    if (active) params.set("active", active);
    if (attention) params.set("attention", "true");
    businessRequest("/api/inventory?" + params, { signal: c.signal })
      .then((d) => {
        setItems(d.inventory);
        setCategories(d.categories ?? []);
        setTotal(d.total);
      })
      .catch((e) => {
        if (!c.signal.aborted) setError(e.message);
      })
      .finally(() => {
        if (!c.signal.aborted) setLoading(false);
      });
    return () => c.abort();
  }, [q, category, type, stock, active, attention, sort, page, revision]);
  useEffect(() => {
    const c = new AbortController();
    businessRequest("/api/services", { signal: c.signal })
      .then((d) => setServices(d.services))
      .catch((e) => {
        if (!c.signal.aborted) setError(e.message);
      });
    if (!readOnly)
      Promise.all([
        businessRequest("/api/inventory/summary", { signal: c.signal }),
        businessRequest("/api/inventory/suppliers", { signal: c.signal }),
      ])
        .then(([s, p]) => {
          setSummary(s);
          setSuppliers(p.suppliers);
        })
        .catch((e) => {
          if (!c.signal.aborted) setError(e.message);
        });
    return () => c.abort();
  }, [revision, readOnly]);
  useEffect(() => {
    const timer = setInterval(() => {
      if (document.visibilityState === "visible") setRevision((r) => r + 1);
    }, 30000);
    return () => clearInterval(timer);
  }, []);
  const stats = summary?.stats;
  const tabs = readOnly
    ? ["products", "service supplies"]
    : [
        "products",
        "service supplies",
        "transactions",
        "suppliers",
        "reports",
        "reference catalog",
      ];
  const saved = (message: string) => {
    setModal(null);
    setNotice(message);
    refresh();
  };
  return (
    <div className="space-y-6">
      <PageHeader
        title={readOnly ? "Salon Supplies" : "Inventory & Supplies"}
        subtitle="Service supplies, reusable equipment, stock movements and replenishment."
      />
      {notice && (
        <p role="status" className="portal-alert">
          {notice}
        </p>
      )}
      {error && (
        <p role="alert" className="portal-alert">
          {error}{" "}
          <button onClick={refresh} type="button" className="underline">
            Retry
          </button>
        </p>
      )}
      {!readOnly && stats && (
        <>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {[
              ["Inventory products", stats.total],
              ["Consumable products", stats.consumables],
              ["Reusable equipment", stats.equipment],
              ["Inventory value", money(stats.value)],
              ["Low stock", stats.low],
              ["Out of stock", stats.out],
              ["Expired", stats.expired],
              ["Expiring soon", stats.expiring],
            ].map(([name, value]) => (
              <div key={String(name)} className="portal-panel p-4">
                <p className="text-xs text-muted">{name}</p>
                <p className="mt-2 text-2xl text-white">{value}</p>
              </div>
            ))}
          </div>
          <p className="text-xs text-muted">
            Value uses recorded purchase costs. {stats.unpriced} products have
            no purchase cost recorded.
          </p>
          {(stats.low + stats.out + stats.expired + stats.expiring > 0 ||
            summary.servicesAtRisk?.length > 0) && (
            <div className="portal-panel border-warning/30 p-4">
              <h2 className="font-serif text-lg text-warning">
                Supplies need attention
              </h2>
              <p className="mt-1 text-sm text-secondary">
                Review low stock, expiration dates and{" "}
                {summary.servicesAtRisk?.length ?? 0} services with insufficient
                supplies.
              </p>
              <button
                type="button"
                className="studio-secondary-button mt-3"
                onClick={() => {
                  setAttention(true);
                  setTab("products");
                }}
              >
                Review replenishment
              </button>
            </div>
          )}
          {!!summary.shortages?.length && (
            <div className="portal-panel p-4">
              <h2 className="text-warning">Recorded service shortages</h2>
              <p className="mb-2 text-xs text-muted">
                These completion records remain for review. Use linked
                correction transactions to reconcile actual stock.
              </p>
              <ul>
                {summary.shortages.slice(0, 8).map((r: any) => (
                  <li
                    key={r.appointment_id + r.inventory_id}
                    className="text-sm"
                  >
                    {r.product_name} · {Number(r.remaining ?? r.shortage)}{" "}
                    {r.unit} short · {r.serviceName}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
      {!readOnly && summary && (
        <details className="portal-panel p-4">
          <summary className="cursor-pointer font-serif text-lg">
            Recent inventory activity
          </summary>
          <div className="mt-4 grid gap-5 sm:grid-cols-2">
            <div>
              <h3 className="mb-2 text-sm text-white">
                Recently added products
              </h3>
              <ul className="space-y-1 text-sm text-secondary">
                {summary.recentProducts?.map((r: any) => (
                  <li key={r.id}>
                    {r.productName} · {formatDate(r.createdAt)}
                  </li>
                ))}
              </ul>
              <button
                type="button"
                className="mt-3 text-xs text-gold underline"
                onClick={() => {
                  setSort("newest");
                  setQ("");
                  setCategory("");
                  setType("");
                  setStock("");
                  setActive("");
                  setAttention(false);
                  setTab("products");
                }}
              >
                View recently added
              </button>
            </div>
            <div>
              <h3 className="mb-2 text-sm text-white">
                Recent stock-in / stock-out
              </h3>
              <ul className="space-y-1 text-sm text-secondary">
                {summary.recentMovements?.map((r: any) => (
                  <li key={r.id}>
                    {r.direction === "in" ? "+" : "−"}
                    {Number(r.quantity)} {r.unit || "legacy units"} ·{" "}
                    {r.productName} · {r.kind ? caption(r.kind) : r.direction}
                  </li>
                ))}
              </ul>
              <button
                type="button"
                className="mt-3 text-xs text-gold underline"
                onClick={() => {
                  setHistoryProduct("");
                  setTab("transactions");
                }}
              >
                Open stock history
              </button>
            </div>
          </div>
        </details>
      )}
      <nav
        className="portal-tabs flex flex-wrap gap-2"
        aria-label="Inventory sections"
      >
        {tabs.map((t) => (
          <button
            type="button"
            key={t}
            aria-pressed={tab === t}
            className="capitalize"
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </nav>
      {tab === "products" && (
        <section className="portal-panel p-4 sm:p-6">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <h2 className="font-serif text-xl text-white">Product register</h2>
            {!readOnly && (
              <button
                className="studio-primary-button"
                type="button"
                onClick={() => setModal({ kind: "product" })}
              >
                Add product
              </button>
            )}
          </div>
          <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Field
              label="Search name, brand or SKU"
              value={q}
              onChange={setQ}
            />
            <Select
              label="Product category"
              value={category}
              onChange={setCategory}
              options={[
                { value: "", label: "All categories" },
                ...Array.from(
                  new Set([
                    ...INVENTORY_REFERENCE.map((g) => g.category),
                    ...categories,
                    ...items.map((i) => i.category),
                  ]),
                ).map((v) => ({ value: v, label: v })),
              ]}
            />
            <Select
              label="Product type"
              value={type}
              onChange={setType}
              options={[
                { value: "", label: "All types" },
                { value: "consumable", label: "Consumable" },
                { value: "equipment", label: "Equipment" },
              ]}
            />
            <Select
              label="Stock status"
              value={stock}
              onChange={setStock}
              options={[
                { value: "", label: "All stock levels" },
                { value: "low", label: "Low stock" },
                { value: "out", label: "Out of stock" },
              ]}
            />
            <Select
              label="Product status"
              value={active}
              onChange={setActive}
              options={[
                { value: "", label: "Active and inactive" },
                { value: "true", label: "Active only" },
                { value: "false", label: "Inactive only" },
              ]}
            />
            <Select
              label="Sort products"
              value={sort}
              onChange={setSort}
              options={[
                { value: "name", label: "Product name" },
                { value: "stock", label: "Stock quantity" },
                ...(!readOnly
                  ? [{ value: "cost", label: "Purchase cost" }]
                  : []),
                { value: "newest", label: "Recently added" },
              ]}
            />
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={attention}
                onChange={(e) => setAttention(e.target.checked)}
              />
              Needs attention only
            </label>
          </div>
          {loading ? (
            <p role="status">Loading products…</p>
          ) : items.length === 0 ? (
            <p className="portal-empty">No products match these filters.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs text-muted">
                  <tr>
                    <th className="p-3">Product</th>
                    <th className="p-3">Stock / unit</th>
                    <th className="p-3">Status</th>
                    {!readOnly && <th className="p-3">Purchase cost</th>}
                    <th className="p-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((i) => (
                    <tr className="border-t border-purple-light/15" key={i.id}>
                      <td className="p-3">
                        <div className="flex items-center gap-3">
                          {i.imageUrl && (
                            <img
                              src={i.imageUrl}
                              alt=""
                              loading="lazy"
                              className="h-12 w-12 rounded object-cover"
                            />
                          )}
                          <div>
                            <button
                              type="button"
                              className="text-left text-white underline decoration-purple-light/30"
                              onClick={() =>
                                setModal({ kind: "detail", item: i })
                              }
                            >
                              {i.productName}
                            </button>
                            <p className="text-xs text-muted">
                              {i.brand || "No brand"} · {i.sku || "No SKU"}
                            </p>
                            <p className="text-xs text-muted">
                              {i.category} ·{" "}
                              {i.itemType === "equipment"
                                ? "Reusable equipment"
                                : "Consumable"}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="p-3">
                        <strong>
                          {Number(i.currentStock)} {i.unit}
                        </strong>
                        <p className="text-xs text-muted">
                          Min {Number(i.minimumThreshold)}
                          {i.maximumStock != null
                            ? " · Target " + Number(i.maximumStock)
                            : ""}
                        </p>
                      </td>
                      <td className="p-3">
                        <Stock item={i} />
                        {i.expirationDate && (
                          <p className="mt-1 text-xs text-muted">
                            Expires {i.expirationDate}
                          </p>
                        )}
                      </td>
                      {!readOnly && (
                        <td className="p-3">{money(i.purchaseCost)}</td>
                      )}
                      <td className="p-3">
                        <div className="flex flex-wrap gap-2">
                          {readOnly ? (
                            <button
                              onClick={() =>
                                setModal({ kind: "detail", item: i })
                              }
                            >
                              View
                            </button>
                          ) : (
                            <>
                              <button
                                className="text-gold"
                                onClick={() =>
                                  setModal({ kind: "product", item: i })
                                }
                              >
                                Edit
                              </button>
                              <button
                                className="text-gold"
                                onClick={() =>
                                  setModal({ kind: "movement", item: i })
                                }
                              >
                                Stock transaction
                              </button>
                              <button
                                className="text-muted"
                                onClick={() =>
                                  setModal({ kind: "remove", item: i })
                                }
                              >
                                Archive / remove
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="mt-5 flex items-center justify-between gap-3">
            <button
              type="button"
              disabled={page <= 1 || loading}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </button>
            <span className="text-xs text-muted">
              Page {page} · {total} products
            </span>
            <button
              type="button"
              disabled={page * 24 >= total || loading}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </section>
      )}
      {tab === "service supplies" && (
        <RequirementsEditor
          services={services}
          readOnly={readOnly}
          onSaved={refresh}
          revision={revision}
        />
      )}
      {tab === "transactions" && (
        <Ledger
          suppliers={suppliers}
          revision={revision}
          initialProduct={historyProduct}
        />
      )}
      {tab === "suppliers" && (
        <section className="portal-panel p-5">
          <div className="mb-5 flex justify-between">
            <h2 className="font-serif text-xl">Suppliers</h2>
            <button
              className="studio-primary-button"
              onClick={() => setModal({ kind: "supplier" })}
            >
              Add supplier
            </button>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {suppliers.map((s) => (
              <button
                key={s.id}
                onClick={() => setModal({ kind: "supplier", supplier: s })}
                className="rounded-lg border border-purple-light/20 p-4 text-left"
              >
                <strong>{s.name}</strong>
                <p className="text-xs text-muted">
                  {s.contact} {s.phone}
                </p>
                <p className="text-xs text-muted">
                  {s.email} · {s.active ? "Active" : "Inactive"}
                </p>
              </button>
            ))}
          </div>
          {!suppliers.length && <p>No suppliers recorded yet.</p>}
        </section>
      )}
      {tab === "reports" && (
        <Reports
          revision={revision}
          suppliers={suppliers}
          services={services}
          onSaved={refresh}
        />
      )}
      {tab === "reference catalog" && (
        <section className="portal-panel p-5">
          <h2 className="font-serif text-xl">Suggested salon catalog</h2>
          <p className="mt-2 text-sm text-muted">
            Reference only. Select an item to review its details and stock unit
            before saving. Nothing is added automatically.
          </p>
          {INVENTORY_REFERENCE.filter(
            (g) =>
              g.key === "G" ||
              g.key === "H" ||
              (g.key === "A" &&
                services.some((s) =>
                  ["hair", "treatment"].includes(s.serviceType),
                )) ||
              (g.key === "B" &&
                services.some((s) => s.serviceType === "nail")) ||
              (g.key === "C" &&
                services.some((s) => s.serviceType === "makeup")) ||
              (g.key === "D" &&
                services.some((s) => s.serviceType === "aesthetic")) ||
              (g.key === "E" &&
                services.some((s) => s.serviceType === "massage")) ||
              (g.key === "F" && services.some((s) => /wax/i.test(s.name))),
          ).map((g) => (
            <details
              key={g.key}
              className="mt-4 rounded-lg border border-purple-light/20 p-4"
            >
              <summary>{g.category}</summary>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                {g.products
                  .filter(
                    (p) =>
                      g.key !== "H" ||
                      (!(
                        /wax/i.test(p.name) &&
                        !services.some((s) => /wax/i.test(s.name))
                      ) &&
                        !(
                          /massage/i.test(p.name) &&
                          !services.some((s) => s.serviceType === "massage")
                        ) &&
                        !(
                          /facial/i.test(p.name) &&
                          !services.some((s) => s.serviceType === "aesthetic")
                        )),
                  )
                  .map((p) => (
                    <button
                      key={p.name}
                      className="rounded border border-purple-light/15 p-3 text-left"
                      onClick={() =>
                        setModal({
                          kind: "product",
                          preset: {
                            name: p.name,
                            purpose: p.purpose,
                            category: g.category,
                            equipment: g.key === "H",
                          },
                        })
                      }
                    >
                      <strong className="text-sm">{p.name}</strong>
                      <p className="text-xs text-muted">{p.purpose}</p>
                    </button>
                  ))}
              </div>
            </details>
          ))}
        </section>
      )}
      {modal && (
        <Frame
          title={
            modal.kind === "product"
              ? modal.item
                ? "Edit product"
                : "Add product"
              : modal.kind === "movement"
                ? "Record stock transaction"
                : modal.kind === "supplier"
                  ? modal.supplier
                    ? "Edit supplier"
                    : "Add supplier"
                  : modal.kind === "remove"
                    ? "Archive or remove product"
                    : "Product details"
          }
          close={() => setModal(null)}
        >
          {modal.kind === "product" && (
            <ProductForm
              item={modal.item}
              preset={modal.preset}
              suppliers={suppliers}
              onSaved={saved}
            />
          )}
          {modal.kind === "supplier" && (
            <SupplierForm item={modal.supplier} onSaved={saved} />
          )}
          {modal.kind === "movement" && modal.item && (
            <MovementForm
              item={modal.item}
              suppliers={suppliers}
              onSaved={saved}
            />
          )}
          {modal.kind === "remove" && modal.item && (
            <RemoveProduct item={modal.item} onSaved={saved} />
          )}
          {modal.kind === "detail" && modal.item && (
            <ProductDetail
              item={modal.item}
              readOnly={readOnly}
              onHistory={() => {
                setHistoryProduct(modal.item!.id);
                setModal(null);
                setTab("transactions");
              }}
            />
          )}
        </Frame>
      )}
    </div>
  );
}

function ProductForm({
  item,
  preset,
  suppliers,
  onSaved,
}: {
  item?: Product;
  preset?: NonNullable<Modal>["preset"];
  suppliers: Supplier[];
  onSaved: (s: string) => void;
}) {
  const [draft, setDraft] = useState<Record<string, string>>({
    productName: item?.productName ?? preset?.name ?? "",
    brand: item?.brand ?? "",
    category: item?.category ?? preset?.category ?? "",
    sku: item?.sku ?? "",
    itemType:
      item?.itemType ?? (preset?.equipment ? "equipment" : "consumable"),
    description: item?.description ?? preset?.purpose ?? "",
    unit: item?.unit ?? "piece",
    currentStock: String(item?.currentStock ?? 0),
    minimumThreshold: String(item?.minimumThreshold ?? 0),
    maximumStock: item?.maximumStock == null ? "" : String(item.maximumStock),
    purchaseCost: item?.purchaseCost == null ? "" : String(item.purchaseCost),
    sellingPrice: item?.sellingPrice == null ? "" : String(item.sellingPrice),
    supplierId: item?.supplierId ?? "",
    location: item?.location ?? "",
    expirationDate: item?.expirationDate ?? "",
    active: item?.active === false ? "false" : "true",
  });
  const [image, setImage] = useState<string | null | undefined>(undefined),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const set = (key: string) => (value: string) =>
    setDraft((d) => ({ ...d, [key]: value }));
  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      const body: any = {
        ...draft,
        active: draft.active === "true",
        minimumThreshold: Number(draft.minimumThreshold),
        maximumStock:
          draft.maximumStock === "" ? null : Number(draft.maximumStock),
        purchaseCost:
          draft.purchaseCost === "" ? null : Number(draft.purchaseCost),
        sellingPrice:
          draft.sellingPrice === "" ? null : Number(draft.sellingPrice),
        supplierId: draft.supplierId || null,
        expirationDate: draft.expirationDate || null,
      };
      if (item) {
        body.id = item.id;
        delete body.currentStock;
      } else body.currentStock = Number(draft.currentStock);
      if (image !== undefined) body.image = image;
      await businessRequest("/api/inventory", {
        method: item ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      onSaved(item ? "Product updated." : "Product added.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save product.");
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  return (
    <form onSubmit={save}>
      <fieldset disabled={busy} className="grid gap-4 sm:grid-cols-2">
        <Field
          label="Product name"
          value={draft.productName}
          onChange={set("productName")}
          required
          maxLength={255}
        />
        <Field
          label="Brand"
          value={draft.brand}
          onChange={set("brand")}
          maxLength={120}
        />
        <Field
          label="SKU / product code"
          value={draft.sku}
          onChange={set("sku")}
          maxLength={64}
        />
        <Field
          label="Category"
          value={draft.category}
          onChange={set("category")}
          required
          maxLength={100}
        />
        <Select
          label="Product type"
          value={draft.itemType}
          onChange={set("itemType")}
          options={[
            { value: "consumable", label: "Consumable" },
            { value: "equipment", label: "Reusable equipment" },
          ]}
        />
        <Select
          label="Stock unit"
          value={draft.unit}
          onChange={set("unit")}
          options={units.map((u) => ({ value: u, label: u }))}
        />
        {item ? (
          <p className="text-sm text-muted">
            Current stock: {Number(item.currentStock)} {item.unit}. Record a
            stock transaction to change it.
          </p>
        ) : (
          <Field
            label="Opening stock"
            value={draft.currentStock}
            onChange={set("currentStock")}
            type="number"
            step="0.001"
            required
          />
        )}
        <Field
          label="Minimum stock"
          value={draft.minimumThreshold}
          onChange={set("minimumThreshold")}
          type="number"
          step="0.001"
          required
        />
        <Field
          label="Maximum / replenishment target (optional)"
          value={draft.maximumStock}
          onChange={set("maximumStock")}
          type="number"
          step="0.001"
        />
        <Field
          label="Purchase cost per stock unit (PHP)"
          value={draft.purchaseCost}
          onChange={set("purchaseCost")}
          type="number"
          step="0.01"
        />
        <Field
          label="Selling price (optional, PHP)"
          value={draft.sellingPrice}
          onChange={set("sellingPrice")}
          type="number"
          step="0.01"
        />
        <Select
          label="Supplier"
          value={draft.supplierId}
          onChange={set("supplierId")}
          options={[
            { value: "", label: "Not specified" },
            ...suppliers
              .filter((s) => s.active || s.id === draft.supplierId)
              .map((s) => ({
                value: s.id,
                label: s.name + (s.active ? "" : " (inactive)"),
              })),
          ]}
        />
        <Field
          label="Storage location"
          value={draft.location}
          onChange={set("location")}
          maxLength={160}
        />
        <Field
          label="Expiration date"
          value={draft.expirationDate}
          onChange={set("expirationDate")}
          type="date"
        />
        <Select
          label="Product status"
          value={draft.active}
          onChange={set("active")}
          options={[
            { value: "true", label: "Active" },
            { value: "false", label: "Inactive" },
          ]}
        />
        <label className="block text-xs text-secondary sm:col-span-2">
          Description
          <textarea
            className={inputStyle}
            maxLength={2000}
            value={draft.description}
            onChange={(e) => set("description")(e.target.value)}
          />
        </label>
        <label className="block text-xs text-secondary">
          Product image (PNG/JPEG, up to 2 MB and 2048 pixels per side)
          <input
            className={inputStyle}
            type="file"
            accept="image/png,image/jpeg"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (!f) return;
              if (f.size > 2097152) {
                setError("Choose an image up to 2 MB.");
                return;
              }
              const r = new FileReader();
              r.onload = () => setImage(String(r.result));
              r.onerror = () => setError("Could not read this image.");
              r.readAsDataURL(f);
            }}
          />
        </label>
        <div>
          {(image ?? (image === undefined ? item?.imageUrl : null)) && (
            <img
              className="h-24 w-24 rounded object-contain"
              alt="Product preview"
              src={image ?? item?.imageUrl ?? ""}
            />
          )}
          <button
            type="button"
            className="text-xs text-muted underline"
            onClick={() => setImage(null)}
          >
            Remove image
          </button>
        </div>
      </fieldset>
      <p className="my-4 text-xs text-muted">
        Stock units and product type are locked after movements or service
        requirements exist. Reusable equipment is never deducted at service
        completion.
      </p>
      {error && (
        <p role="alert" className="portal-alert">
          {error}
        </p>
      )}
      <button className="studio-primary-button" type="submit" disabled={busy}>
        {busy ? "Saving…" : "Save product"}
      </button>
    </form>
  );
}

function SupplierForm({
  item,
  onSaved,
}: {
  item?: Supplier;
  onSaved: (s: string) => void;
}) {
  const [draft, setDraft] = useState({
      name: item?.name ?? "",
      contact: item?.contact ?? "",
      email: item?.email ?? "",
      phone: item?.phone ?? "",
      address: item?.address ?? "",
      notes: item?.notes ?? "",
      active: item?.active ?? true,
    }),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        if (busy) return;
        setBusy(true);
        try {
          await businessRequest("/api/inventory/suppliers", {
            method: item ? "PATCH" : "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ...draft, id: item?.id }),
          });
          onSaved("Supplier saved.");
        } catch (e) {
          setError(e instanceof Error ? e.message : "Could not save supplier.");
        } finally {
          setBusy(false);
        }
      }}
    >
      <fieldset disabled={busy} className="grid gap-4 sm:grid-cols-2">
        {(
          ["name", "contact", "email", "phone", "address", "notes"] as const
        ).map((key) => (
          <Field
            key={key}
            label={key === "name" ? "Supplier name" : caption(key)}
            required={key === "name"}
            type={key === "email" ? "email" : "text"}
            value={draft[key]}
            onChange={(v) => setDraft((d) => ({ ...d, [key]: v }))}
          />
        ))}
        <label className="text-sm">
          <input
            type="checkbox"
            checked={draft.active}
            onChange={(e) =>
              setDraft((d) => ({ ...d, active: e.target.checked }))
            }
          />{" "}
          Active supplier
        </label>
      </fieldset>
      {error && <p role="alert">{error}</p>}
      <button
        type="submit"
        disabled={busy}
        className="studio-primary-button mt-5"
      >
        Save supplier
      </button>
    </form>
  );
}

function MovementForm({
  item,
  suppliers,
  onSaved,
}: {
  item: Product;
  suppliers: Supplier[];
  onSaved: (s: string) => void;
}) {
  const [kind, setKind] = useState("stock_in"),
    [quantity, setQuantity] = useState(""),
    [adjusted, setAdjusted] = useState(String(item.currentStock)),
    [direction, setDirection] = useState("out"),
    [reason, setReason] = useState(""),
    [cost, setCost] = useState(
      item.purchaseCost == null ? "" : String(item.purchaseCost),
    ),
    [supplier, setSupplier] = useState(item.supplierId ?? ""),
    [reference, setReference] = useState(""),
    [date, setDate] = useState(salonDay()),
    [appointment, setAppointment] = useState(""),
    [appointments, setAppointments] = useState<any[]>([]),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const requestId = useRef(crypto.randomUUID()),
    lock = useRef(false);
  useEffect(() => {
    if (!["correction", "stock_out", "adjustment"].includes(kind)) return;
    const c = new AbortController();
    businessRequest("/api/appointments", { signal: c.signal })
      .then((d) =>
        setAppointments(
          d.appointments.filter(
            (a: any) => kind !== "correction" || a.status === "completed",
          ),
        ),
      )
      .catch((e) => {
        if (!c.signal.aborted) setError(e.message);
      });
    return () => c.abort();
  }, [kind]);
  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      await businessRequest("/api/inventory/transactions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: item.id,
          requestId: requestId.current,
          kind,
          direction:
            kind === "stock_in"
              ? "in"
              : kind === "correction"
                ? direction
                : "out",
          quantity: kind === "adjustment" ? undefined : Number(quantity),
          adjustedQuantity:
            kind === "adjustment" ? Number(adjusted) : undefined,
          previousQuantity:
            kind === "adjustment" ? Number(item.currentStock) : undefined,
          unit: item.unit,
          reason: reason || undefined,
          unitCost: kind === "stock_in" && cost !== "" ? Number(cost) : null,
          supplierId: kind === "stock_in" ? supplier || null : null,
          reference: reference || null,
          occurredAt: date + "T00:00:00+08:00",
          appointmentId: ["correction", "stock_out", "adjustment"].includes(
            kind,
          )
            ? appointment || null
            : null,
        }),
      });
      onSaved("Stock transaction recorded.");
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Could not save the transaction.",
      );
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  return (
    <form onSubmit={save}>
      <p className="mb-4 text-sm">
        {item.productName} · Recorded stock:{" "}
        <strong>
          {Number(item.currentStock)} {item.unit}
        </strong>
      </p>
      <fieldset disabled={busy} className="grid gap-4 sm:grid-cols-2">
        <Select
          label="Transaction type"
          value={kind}
          onChange={(k) => {
            setKind(k);
            requestId.current = crypto.randomUUID();
            setError("");
          }}
          options={kinds
            .filter(
              (k) => !["initial_stock", "service_consumption"].includes(k),
            )
            .map((k) => ({ value: k, label: caption(k) }))}
        />
        {kind === "adjustment" ? (
          <Field
            label="Adjusted physical quantity"
            value={adjusted}
            onChange={setAdjusted}
            type="number"
            step="0.001"
            required
          />
        ) : (
          <Field
            label={`Quantity (${item.unit})`}
            value={quantity}
            onChange={setQuantity}
            type="number"
            step="0.001"
            required
          />
        )}
        {kind === "stock_in" && (
          <>
            <Field
              label="Purchase cost per stock unit (PHP)"
              value={cost}
              onChange={setCost}
              type="number"
              step="0.01"
            />
            <Select
              label="Supplier"
              value={supplier}
              onChange={setSupplier}
              options={[
                { value: "", label: "Not specified" },
                ...suppliers
                  .filter((s) => s.active)
                  .map((s) => ({ value: s.id, label: s.name })),
              ]}
            />
          </>
        )}
        {kind === "correction" && (
          <Select
            label="Correction direction"
            value={direction}
            onChange={setDirection}
            options={[
              { value: "in", label: "Return to stock" },
              { value: "out", label: "Additional consumption" },
            ]}
          />
        )}
        <Field
          label="Date received / withdrawn"
          value={date}
          onChange={setDate}
          type="date"
          required
        />
        <Field
          label="Receipt / reference (optional)"
          value={reference}
          onChange={setReference}
          maxLength={160}
        />
        <label className="block text-xs text-secondary sm:col-span-2">
          Reason {kind === "stock_in" ? "(optional)" : "(required)"}
          <textarea
            className={inputStyle}
            required={kind !== "stock_in"}
            maxLength={1000}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
        </label>
        {["correction", "stock_out", "adjustment"].includes(kind) && (
          <Select
            label={
              kind === "correction"
                ? "Completed appointment (required)"
                : "Related appointment (optional)"
            }
            value={appointment}
            onChange={setAppointment}
            options={[
              { value: "", label: "Choose an appointment" },
              ...appointments.map((a) => ({
                value: a.id,
                label: `${a.client?.name ?? "Client"} · ${a.serviceName} · ${formatDate(a.appointmentDate)}`,
              })),
            ]}
          />
        )}
      </fieldset>
      <p className="my-4 text-xs text-muted">
        Configured service supplies are deducted automatically on completion.
        Use a linked correction to reconcile completed consumption. Adjustments
        compare the displayed previous balance with the current database
        balance.
      </p>
      {error && (
        <p role="alert" className="portal-alert">
          {error}
        </p>
      )}
      <button
        type="submit"
        disabled={busy || (kind === "correction" && !appointment)}
        className="studio-primary-button"
      >
        {busy ? "Recording…" : "Confirm transaction"}
      </button>
    </form>
  );
}

function RemoveProduct({
  item,
  onSaved,
}: {
  item: Product;
  onSaved: (s: string) => void;
}) {
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  return (
    <div>
      <p className="mb-4 text-sm">
        Remove {item.productName}? Products with stock history, usage or service
        links are archived instead. Existing history is retained.
      </p>
      {error && <p role="alert">{error}</p>}
      <button
        disabled={busy}
        className="studio-secondary-button"
        onClick={async () => {
          setBusy(true);
          try {
            const result = await businessRequest(
              "/api/inventory?id=" + encodeURIComponent(item.id),
              { method: "DELETE" },
            );
            onSaved(
              result.result === "archived"
                ? "Product archived; history retained."
                : "Unused product removed.",
            );
          } catch (e) {
            setError(
              e instanceof Error ? e.message : "Could not remove product.",
            );
          } finally {
            setBusy(false);
          }
        }}
      >
        Confirm archive / removal
      </button>
    </div>
  );
}
function ProductDetail({
  item,
  readOnly,
  onHistory,
}: {
  item: Product;
  readOnly: boolean;
  onHistory: () => void;
}) {
  return (
    <div className="space-y-4">
      {item.imageUrl && (
        <img
          src={item.imageUrl}
          alt={item.productName}
          className="h-40 w-40 rounded object-contain"
        />
      )}
      <h3 className="font-serif text-xl">{item.productName}</h3>
      <Stock item={item} />
      <p className="text-sm text-secondary">
        {item.description || "No description recorded."}
      </p>
      <dl className="grid grid-cols-2 gap-4 text-sm">
        {Object.entries({
          Category: item.category,
          Type: item.itemType,
          Brand: item.brand,
          SKU: item.sku,
          Stock: `${Number(item.currentStock)} ${item.unit}`,
          Minimum: item.minimumThreshold,
          Target: item.maximumStock,
          Expiration: item.expirationDate,
          ...(!readOnly
            ? {
                "Purchase cost": money(item.purchaseCost),
                "Selling price": money(item.sellingPrice),
                Supplier: item.supplierName,
                Location: item.location,
              }
            : {}),
        }).map(([k, v]) => (
          <div key={k}>
            <dt className="text-xs text-muted">{k}</dt>
            <dd>{v ?? "Not specified"}</dd>
          </div>
        ))}
      </dl>
      {!readOnly && (
        <button className="studio-secondary-button" onClick={onHistory}>
          Open transaction history
        </button>
      )}
    </div>
  );
}

function ItemPicker({
  value,
  onChange,
  label = "Product",
}: {
  value: string;
  onChange: (id: string, item?: Product) => void;
  label?: string;
}) {
  const [q, setQ] = useState(""),
    [rows, setRows] = useState<Product[]>([]);
  useEffect(() => {
    const c = new AbortController(),
      timer = setTimeout(() => {
        businessRequest("/api/inventory?limit=250&q=" + encodeURIComponent(q), {
          signal: c.signal,
        })
          .then((d) => setRows(d.inventory))
          .catch(() => {});
      }, 200);
    return () => {
      clearTimeout(timer);
      c.abort();
    };
  }, [q]);
  return (
    <div className="space-y-2">
      <Field label={label + " search"} value={q} onChange={setQ} />
      <Select
        label={label}
        value={value}
        onChange={(id) =>
          onChange(
            id,
            rows.find((r) => r.id === id),
          )
        }
        options={[
          { value: "", label: "Choose product" },
          ...rows.map((r) => ({
            value: r.id,
            label:
              r.productName + " · " + r.unit + (r.active ? "" : " (inactive)"),
          })),
        ]}
      />
    </div>
  );
}
function RequirementsEditor({
  services,
  readOnly,
  onSaved,
  revision,
}: {
  services: Service[];
  readOnly: boolean;
  onSaved: () => void;
  revision: number;
}) {
  const [service, setService] = useState(""),
    [rows, setRows] = useState<Product[]>([]),
    [chosen, setChosen] = useState(""),
    [quantity, setQuantity] = useState(""),
    [chosenItem, setChosenItem] = useState<Product>(),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    setError("");
    setNotice("");
    if (!service) {
      setRows([]);
      return;
    }
    const c = new AbortController();
    businessRequest(
      "/api/inventory/requirements?serviceId=" + encodeURIComponent(service),
      { signal: c.signal },
    )
      .then((d) => setRows(d.requirements))
      .catch((e) => {
        if (!c.signal.aborted) setError(e.message);
      });
    return () => c.abort();
  }, [service, revision]);
  return (
    <section className="portal-panel space-y-4 p-5">
      <h2 className="font-serif text-xl">Supplies by service</h2>
      <p className="text-sm text-muted">
        Quantities use each product's stock unit. Reusable tools are checked for
        availability but never consumed.
      </p>
      <Select
        label="Salon service"
        value={service}
        onChange={setService}
        options={[
          { value: "", label: "Choose a service" },
          ...services.map((s) => ({
            value: s.id,
            label: s.groupLabel + " · " + s.name,
          })),
        ]}
      />
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      {service && (
        <>
          <div className="space-y-3">
            {rows.map((r) => (
              <div
                className="grid gap-3 rounded border border-purple-light/20 p-3 sm:grid-cols-[1fr_140px_80px]"
                key={r.id}
              >
                <div>
                  <strong>{r.productName}</strong>
                  <p className="text-xs text-muted">
                    {r.itemType === "equipment"
                      ? "Reusable · not deducted"
                      : "Consumable"}{" "}
                    · {Number(r.currentStock)} {r.unit} in stock
                  </p>
                  <Stock item={r} />
                  {r.estimatedQuantity! > Number(r.currentStock) && (
                    <p className="text-xs text-warning">
                      Not enough for one service
                    </p>
                  )}
                </div>
                {readOnly ? (
                  <p>
                    {Number(r.estimatedQuantity)} {r.unit}
                  </p>
                ) : (
                  <Field
                    label={`Quantity (${r.unit}) for ${r.productName}`}
                    value={String(r.estimatedQuantity)}
                    onChange={(v) =>
                      setRows((items) =>
                        items.map((i) =>
                          i.id === r.id
                            ? { ...i, estimatedQuantity: Number(v) }
                            : i,
                        ),
                      )
                    }
                    type="number"
                    step="0.001"
                  />
                )}
                {!readOnly && (
                  <button
                    type="button"
                    className="text-error"
                    onClick={() =>
                      setRows((items) => items.filter((i) => i.id !== r.id))
                    }
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
          </div>
          {!rows.length && (
            <p>No product requirements configured for this service.</p>
          )}
          {!readOnly && (
            <>
              <div className="grid gap-3 rounded border border-purple-light/20 p-3 sm:grid-cols-2">
                <ItemPicker
                  value={chosen}
                  onChange={(id, item) => {
                    setChosen(id);
                    setChosenItem(item);
                  }}
                  label="Required product"
                />
                <Field
                  label={
                    "Estimated quantity" +
                    (chosenItem ? " (" + chosenItem.unit + ")" : "")
                  }
                  value={quantity}
                  onChange={setQuantity}
                  type="number"
                  step="0.001"
                />
                <button
                  type="button"
                  disabled={
                    !chosenItem ||
                    !Number(quantity) ||
                    rows.length >= 40 ||
                    rows.some((r) => r.id === chosen)
                  }
                  className="studio-secondary-button"
                  onClick={() => {
                    if (chosenItem)
                      setRows((r) => [
                        ...r,
                        { ...chosenItem, estimatedQuantity: Number(quantity) },
                      ]);
                    setChosen("");
                    setChosenItem(undefined);
                    setQuantity("");
                  }}
                >
                  Add requirement
                </button>
              </div>
              <button
                type="button"
                disabled={busy}
                className="studio-primary-button"
                onClick={async () => {
                  setBusy(true);
                  setError("");
                  try {
                    await businessRequest("/api/inventory/requirements", {
                      method: "PUT",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        serviceId: service,
                        requirements: rows.map((r) => ({
                          inventoryId: r.id,
                          quantity: Number(r.estimatedQuantity),
                          unit: r.unit,
                        })),
                      }),
                    });
                    setNotice("Service requirements saved.");
                    onSaved();
                  } catch (e) {
                    setError(
                      e instanceof Error
                        ? e.message
                        : "Could not save requirements.",
                    );
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                Save service requirements
              </button>
            </>
          )}
        </>
      )}
    </section>
  );
}

function Ledger({
  suppliers,
  revision,
  initialProduct = "",
}: {
  suppliers: Supplier[];
  revision: number;
  initialProduct?: string;
}) {
  const [product, setProduct] = useState(initialProduct),
    [kind, setKind] = useState(""),
    [category, setCategory] = useState(""),
    [supplier, setSupplier] = useState(""),
    [staff, setStaff] = useState(""),
    [from, setFrom] = useState(""),
    [to, setTo] = useState(""),
    [page, setPage] = useState(1),
    [data, setData] = useState<any>(null),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(false);
  useEffect(
    () => setPage(1),
    [product, kind, category, supplier, staff, from, to],
  );
  useEffect(() => {
    const c = new AbortController(),
      p = new URLSearchParams({ page: String(page), limit: "30" });
    for (const [k, v] of Object.entries({
      product,
      kind,
      category,
      supplier,
      staff,
      from,
      to,
    }))
      if (v) p.set(k, v);
    setLoading(true);
    setError("");
    businessRequest("/api/inventory/transactions?" + p, { signal: c.signal })
      .then(setData)
      .catch((e) => {
        if (!c.signal.aborted) setError(e.message);
      })
      .finally(() => {
        if (!c.signal.aborted) setLoading(false);
      });
    return () => c.abort();
  }, [product, kind, category, supplier, staff, from, to, page, revision]);
  return (
    <section className="portal-panel space-y-4 p-5">
      <h2 className="font-serif text-xl">Stock and purchase history</h2>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <ItemPicker
          label="History product"
          value={product}
          onChange={setProduct}
        />
        <Select
          label="Movement type"
          value={kind}
          onChange={setKind}
          options={[
            { value: "", label: "All movements" },
            ...kinds.map((k) => ({ value: k, label: caption(k) })),
          ]}
        />
        <Select
          label="History category"
          value={category}
          onChange={setCategory}
          options={[
            { value: "", label: "All categories" },
            ...(data?.categories ?? []).map((c: string) => ({
              value: c,
              label: c,
            })),
          ]}
        />
        <Select
          label="Supplier filter"
          value={supplier}
          onChange={setSupplier}
          options={[
            { value: "", label: "All suppliers" },
            ...suppliers.map((s) => ({ value: s.id, label: s.name })),
          ]}
        />
        <Select
          label="Staff member"
          value={staff}
          onChange={setStaff}
          options={[
            { value: "", label: "All staff" },
            ...(data?.staff ?? []).map((s: any) => ({
              value: s.id,
              label: s.name,
            })),
          ]}
        />
        <Field label="From date" value={from} onChange={setFrom} type="date" />
        <Field label="Through date" value={to} onChange={setTo} type="date" />
      </div>
      {error && <p role="alert">{error}</p>}
      {loading ? (
        <p role="status">Loading history…</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr>
                {[
                  "Date",
                  "Product / type",
                  "Quantity",
                  "Balance",
                  "Cost / supplier",
                  "Recorded by / reason",
                ].map((h) => (
                  <th className="p-2 text-xs text-muted" key={h}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data?.transactions?.map((t: any) => (
                <tr key={t.id} className="border-t border-purple-light/15">
                  <td className="p-2">
                    {formatDate(t.occurredAt || t.createdAt)}
                  </td>
                  <td className="p-2">
                    {t.productName}
                    <p className="text-xs text-muted">{caption(t.kind)}</p>
                    {t.appointmentId && (
                      <a
                        className="text-xs text-gold underline"
                        href={"/admin/appointments#booking-" + t.appointmentId}
                      >
                        Related appointment
                      </a>
                    )}
                  </td>
                  <td className="p-2">
                    {t.direction === "in" ? "+" : "−"}
                    {Number(t.quantity)} {t.unit || "legacy units"}
                  </td>
                  <td className="p-2">{Number(t.stockAfter)}</td>
                  <td className="p-2">
                    {money(t.totalCost)}
                    <p className="text-xs text-muted">
                      {t.supplierName || "—"}
                      {t.reference ? " · " + t.reference : ""}
                    </p>
                  </td>
                  <td className="p-2">
                    {t.staffName}
                    <p className="max-w-xs whitespace-pre-wrap text-xs text-muted">
                      {t.reason || "—"}
                    </p>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data?.transactions?.length && (
            <p className="py-6 text-muted">
              No transactions match these filters.
            </p>
          )}
        </div>
      )}
      <div className="flex justify-between">
        <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          Previous
        </button>
        <span>
          {data?.total ?? 0} records · Page {page}
        </span>
        <button
          disabled={!data || page * 30 >= data.total}
          onClick={() => setPage((p) => p + 1)}
        >
          Next
        </button>
      </div>
    </section>
  );
}

function Reports({
  revision,
  onSaved,
}: {
  revision: number;
  suppliers: Supplier[];
  services: Service[];
  onSaved: () => void;
}) {
  const [from, setFrom] = useState(""),
    [to, setTo] = useState(""),
    [data, setData] = useState<any>(null),
    [policy, setPolicy] = useState({
      shortagePolicy: "block",
      expiryWarningDays: 30,
      consumptionMode: "reported_only",
    }),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    const c = new AbortController(),
      p = new URLSearchParams();
    if (from) p.set("from", from);
    if (to) p.set("to", to);
    Promise.all([
      businessRequest("/api/inventory/reports?" + p, { signal: c.signal }),
      businessRequest("/api/inventory/policy", { signal: c.signal }),
    ])
      .then(([d, s]) => {
        setData(d);
        setPolicy(s.policy);
      })
      .catch((e) => {
        if (!c.signal.aborted) setError(e.message);
      });
    return () => c.abort();
  }, [revision, from, to]);
  return (
    <section className="portal-panel space-y-5 p-5">
      <h2 className="font-serif text-xl">Inventory reports & controls</h2>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field
          label="Report from"
          type="date"
          value={from}
          onChange={setFrom}
        />
        <Field label="Report through" type="date" value={to} onChange={setTo} />
      </div>
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      <p className="text-lg">
        Purchase expenses:{" "}
        <strong>{money(data?.purchaseExpenses?.total)}</strong>
      </p>
      <p className="text-xs text-muted">
        Received-stock costs in this date range; opening balances are excluded.{" "}
        {data?.purchaseExpenses?.unpriced ?? 0} receipts have no recorded cost.
      </p>
      <h3 className="font-serif text-lg">Most frequently consumed products</h3>
      {data?.consumption?.map((r: any) => (
        <div key={r.inventoryId + r.productName + r.unit} className="space-y-1">
          <div className="flex justify-between text-sm">
            <span>{r.productName}</span>
            <span>
              {Number(r.quantity)} {r.unit} · {r.uses} uses
            </span>
          </div>
          <div className="h-2 rounded bg-purple-light/10">
            <div
              className="h-2 rounded bg-gold/70"
              style={{
                width:
                  Math.max(
                    2,
                    (100 * r.uses) /
                      Math.max(...data.consumption.map((x: any) => x.uses), 1),
                  ) + "%",
              }}
            />
          </div>
        </div>
      ))}
      {!data?.consumption?.length && (
        <p className="text-muted">
          No recorded service consumption in this period.
        </p>
      )}
      <h3 className="font-serif text-lg">Consumption by service</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr>
              <th>Service</th>
              <th>Product</th>
              <th>Net consumption</th>
            </tr>
          </thead>
          <tbody>
            {data?.serviceUsage?.map((r: any, i: number) => (
              <tr key={i} className="border-t border-purple-light/15">
                <td className="p-2">{r.serviceName}</td>
                <td className="p-2">{r.productName}</td>
                <td className="p-2">
                  {Number(r.quantity)} {r.unit}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h3 className="font-serif text-lg">Consumption over time</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr>
              <th>Day (Philippine time)</th>
              <th>Unit</th>
              <th>Net quantity</th>
              <th>Recorded cost</th>
            </tr>
          </thead>
          <tbody>
            {data?.byDay?.map((r: any) => (
              <tr
                key={r.day + r.unit}
                className="border-t border-purple-light/15"
              >
                <td className="p-2">{r.day}</td>
                <td>{r.unit}</td>
                <td>{Number(r.quantity)}</td>
                <td>{money(r.cost)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h3 className="font-serif text-lg">Expired and damaged withdrawals</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr>
              <th>Product</th>
              <th>Reason type</th>
              <th>Quantity removed</th>
            </tr>
          </thead>
          <tbody>
            {data?.waste?.map((r: any) => (
              <tr key={r.productName + r.kind + r.unit}>
                <td>{r.productName}</td>
                <td>{r.kind}</td>
                <td>
                  {Number(r.quantity)} {r.unit}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h3 className="font-serif text-lg">Services requiring replenishment</h3>
      <ul className="text-sm">
        {data?.servicesAtRisk?.map((r: any) => (
          <li key={r.id}>
            {r.name} · {r.shortages} unavailable requirements
          </li>
        ))}
      </ul>
      <div className="space-y-4 rounded-lg border border-purple-light/25 p-4">
        <h3 className="font-serif text-lg">Stock recording and shortage policy</h3>
        <Select
          label="Stock deduction at service completion"
          value={policy.consumptionMode}
          onChange={(v) => setPolicy((p) => ({ ...p, consumptionMode: v }))}
          options={[
            {value: "reported_only", label: "Only products reported as used up (default)"},
            {value: "configured", label: "All configured service quantities"},
          ]}
        />
        <p className="text-xs text-muted">In reported-only mode, staff list only products that were used up and their quantities. Unlisted products keep their stock. Service requirements remain available for planning.</p>
        <Select
          label="When a completed service lacks supplies"
          value={policy.shortagePolicy}
          onChange={(v) => setPolicy((p) => ({ ...p, shortagePolicy: v }))}
          options={[
            {
              value: "block",
              label:
                "Block completion until supplies or actual usage are corrected",
            },
            {
              value: "consume_available",
              label:
                "Deduct available stock and record the shortage for admin review",
            },
          ]}
        />
        <Field
          label="Warn before expiration (days)"
          value={String(policy.expiryWarningDays)}
          onChange={(v) =>
            setPolicy((p) => ({ ...p, expiryWarningDays: Number(v) }))
          }
          type="number"
          step="1"
        />
        <p className="text-xs text-muted">
          Expired and inactive products are never consumed. The review policy
          records an unmet quantity without creating negative stock.
        </p>
        <button
          className="studio-primary-button"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            setError("");
            try {
              await businessRequest("/api/inventory/policy", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(policy),
              });
              setNotice("Inventory policy saved.");
              onSaved();
            } catch (e) {
              setError(
                e instanceof Error ? e.message : "Could not save policy.",
              );
            } finally {
              setBusy(false);
            }
          }}
        >
          Save inventory policy
        </button>
      </div>
    </section>
  );
}
