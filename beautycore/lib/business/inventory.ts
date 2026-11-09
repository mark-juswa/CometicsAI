import sharp from "sharp";
import {
  BusinessError,
  PRIVATE,
  boundedJson,
  day,
  fail,
  id,
  mutationOrigin,
} from "./core";
import type { HistoryDependencies } from "./customer-history";
import { salonDay } from "./dates";
export const INVENTORY_UNITS = [
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
const fields = `i.id,i.product_name AS "productName",i.brand,i.category,i.current_stock::float8 AS "currentStock",i.minimum_threshold::float8 AS "minimumThreshold",i.unit_price AS "unitPrice",i.created_at AS "createdAt",i.last_restocked AS "lastRestocked",
 CASE WHEN i.current_stock=0 THEN 'out_of_stock' WHEN i.current_stock<=i.minimum_threshold THEN 'low_stock' ELSE 'in_stock' END AS status,
 d.sku,coalesce(d.item_type,'consumable') AS "itemType",d.description,coalesce(d.unit,'piece') AS unit,d.maximum_stock::float8 AS "maximumStock",d.purchase_cost::float8 AS "purchaseCost",coalesce(d.selling_price,i.unit_price)::float8 AS "sellingPrice",d.supplier_id AS "supplierId",s.name AS "supplierName",d.location,d.expiration_date::text AS "expirationDate",coalesce(d.active,true) AS active,
 (d.expiration_date<(now() AT TIME ZONE 'Asia/Manila')::date) AS expired,(d.expiration_date BETWEEN (now() AT TIME ZONE 'Asia/Manila')::date AND (now() AT TIME ZONE 'Asia/Manila')::date+(SELECT expiry_warning_days FROM inventory_policy)) AS "expiringSoon",CASE WHEN d.image_data IS NULL THEN NULL ELSE '/api/inventory/'||i.id||'/image' END AS "imageUrl"`;
const joins = `FROM inventory i LEFT JOIN inventory_details d ON d.inventory_id=i.id LEFT JOIN inventory_suppliers s ON s.id=d.supplier_id`;
function number(value: unknown, label: string, nullable = false, decimals = 3) {
  if (nullable && (value === null || value === "" || value === undefined))
    return null;
  if (
    typeof value !== "number" ||
    !Number.isFinite(value) ||
    value < 0 ||
    value > 1000000000 ||
    Math.abs(value * 10 ** decimals - Math.round(value * 10 ** decimals)) >
      0.00001
  )
    fail(`Enter a valid nonnegative ${label} (up to ${decimals} decimals).`);
  return value;
}
function text(value: unknown, label: string, max: number, required = false) {
  if (value == null || value === "") {
    if (required) fail(`${label} is required.`);
    return null;
  }
  if (typeof value !== "string" || value.length > max)
    fail(`${label} must be up to ${max} characters.`);
  return value.trim() || null;
}
async function access(
  request: Request,
  deps: HistoryDependencies,
  admin = false,
) {
  const actor = await deps.actor();
  if (!actor) fail("Sign in to continue.", 401);
  if (
    !["admin", "stylist"].includes(actor.role) ||
    (admin && actor.role !== "admin")
  )
    fail("Administrator access required.", 403);
  if (request.method !== "GET") mutationOrigin(request, deps.publicOrigin);
  return actor;
}
const json = (data: unknown, status = 200) =>
  Response.json(data, { status, headers: PRIVATE });
function sanitize(row: Record<string, unknown>, admin: boolean) {
  return admin
    ? row
    : {
        ...row,
        purchaseCost: undefined,
        supplierId: undefined,
        supplierName: undefined,
        location: undefined,
      };
}
function pagination(p: URLSearchParams) {
  const page = Number(p.get("page") ?? 1),
    limit = Number(p.get("limit") ?? 30);
  if (
    !Number.isSafeInteger(page) ||
    page < 1 ||
    !Number.isSafeInteger(limit) ||
    limit < 1 ||
    limit > 250
  )
    fail("Invalid page.");
  return { page, limit, offset: (page - 1) * limit };
}
function dates(p: URLSearchParams) {
  const from = p.get("from") ? day(p.get("from")) : null,
    to = p.get("to") ? day(p.get("to")) : null;
  if (from && to && from > to) fail("The end date must follow the start date.");
  return { from, to };
}
export async function inventoryApi(
  request: Request,
  section: string,
  deps: HistoryDependencies,
  identity?: string,
): Promise<Response> {
  try {
    const actor = await access(
      request,
      deps,
      request.method !== "GET" ||
        ["summary", "transactions", "suppliers", "policy", "reports"].includes(
          section,
        ),
    );
    const admin = actor.role === "admin",
      p = new URL(request.url).searchParams;
    if (section === "image") {
      id(identity);
      const [row] = await deps.query(
        "SELECT image_data FROM inventory_details WHERE inventory_id=$1",
        [identity],
      );
      const match =
        typeof row?.image_data === "string"
          ? /^data:(image\/(?:png|jpeg));base64,(.+)$/.exec(row.image_data)
          : null;
      if (!match) fail("Image not found.", 404);
      return new Response(Buffer.from(match[2], "base64"), {
        headers: {
          ...PRIVATE,
          "Content-Type": match[1],
          "X-Content-Type-Options": "nosniff",
        },
      });
    }
    if (section === "products" && request.method === "GET") {
      const { page, limit, offset } = pagination(p),
        params: unknown[] = [];
      const conditions: string[] = [];
      const add = (clause: string, value: unknown) => {
        params.push(value);
        conditions.push(clause.replaceAll("?", `$${params.length}`));
      };
      if (p.get("q"))
        add(
          "(i.product_name ILIKE '%'||?||'%' OR coalesce(i.brand,'') ILIKE '%'||?||'%' OR coalesce(d.sku,'') ILIKE '%'||?||'%')",
          p.get("q"),
        );
      if (p.get("category")) add("i.category=?", p.get("category"));
      if (p.get("type"))
        add("coalesce(d.item_type,'consumable')=?", p.get("type"));
      if (p.has("active"))
        add("coalesce(d.active,true)=?::boolean", p.get("active") === "true");
      if (p.get("stock") === "low")
        conditions.push(
          "i.current_stock>0 AND i.current_stock<=i.minimum_threshold",
        );
      if (p.get("stock") === "out") conditions.push("i.current_stock=0");
      if (p.get("attention") === "true")
        conditions.push(
          "coalesce(d.active,true) AND (i.current_stock<=i.minimum_threshold OR d.expiration_date<=(now() AT TIME ZONE 'Asia/Manila')::date+(SELECT expiry_warning_days FROM inventory_policy))",
        );
      const order: Record<string, string> = {
        name: "i.product_name",
        stock: "i.current_stock",
        cost: "d.purchase_cost NULLS LAST",
        newest: "i.created_at DESC",
      };
      const sort = order[p.get("sort") ?? "name"] ?? order.name;
      const where = conditions.length
        ? " WHERE " + conditions.join(" AND ")
        : "";
      const [rows, count] = await Promise.all([
        deps.query(
          `SELECT ${fields} ${joins}${where} ORDER BY ${sort},i.id LIMIT $${params.length + 1} OFFSET $${params.length + 2}`,
          [...params, limit, offset],
        ),
        deps.query(`SELECT count(*)::int AS total ${joins}${where}`, params),
      ]);
      return json({
        inventory: rows.map((r) => sanitize(r, admin)),
        categories: (
          await deps.query(
            "SELECT DISTINCT category FROM inventory ORDER BY category",
          )
        ).map((r) => r.category),
        total: count[0].total,
        page,
        limit,
      });
    }
    if (section === "products" && ["POST", "PATCH"].includes(request.method)) {
      const b = await boundedJson(request, 3 * 1024 * 1024);
      const allowed = [
        "id",
        "productName",
        "brand",
        "category",
        "currentStock",
        "minimumThreshold",
        "sku",
        "itemType",
        "description",
        "unit",
        "maximumStock",
        "purchaseCost",
        "sellingPrice",
        "supplierId",
        "location",
        "expirationDate",
        "active",
        "image",
        "unitPrice",
      ];
      if (Object.keys(b).some((k) => !allowed.includes(k)))
        fail("Unexpected product field.");
      const productId = request.method === "PATCH" ? id(b.id) : null;
      let previous: Record<string, unknown> = {};
      if (productId) {
        const rows = await deps.query(
          `SELECT ${fields} ${joins} WHERE i.id=$1`,
          [productId],
        );
        if (!rows[0]) fail("Product not found.", 404);
        previous = rows[0];
        if (b.currentStock !== undefined)
          fail("Use a stock transaction to change stock.");
      }
      const data = { ...previous, ...b };
      const unit = text(data.unit ?? "piece", "Unit", 32, true);
      if (!INVENTORY_UNITS.includes(unit!))
        fail("Choose a supported stock unit.");
      const type = data.itemType ?? "consumable";
      if (!["consumable", "equipment"].includes(String(type)))
        fail("Choose Consumable or Equipment.");
      const clean: Record<string, unknown> = {
        productName: text(data.productName, "Product name", 255, true),
        category: text(data.category, "Category", 100, true),
        brand: text(data.brand, "Brand", 120),
        sku: text(data.sku, "SKU", 64),
        itemType: type,
        description: text(data.description, "Description", 2000),
        unit,
        minimumThreshold: number(data.minimumThreshold ?? 0, "minimum stock"),
        maximumStock: number(data.maximumStock, "maximum stock", true),
        purchaseCost: number(data.purchaseCost, "purchase cost", true, 2),
        sellingPrice: number(
          data.sellingPrice ?? data.unitPrice,
          "selling price",
          true,
          2,
        ),
        supplierId: data.supplierId ? id(data.supplierId) : null,
        location: text(data.location, "Storage location", 160),
        expirationDate: data.expirationDate ? day(data.expirationDate) : null,
        active: data.active ?? true,
      };
      if (typeof clean.active !== "boolean")
        fail("Choose an active or inactive status.");
      if (request.method === "POST")
        clean.currentStock = number(data.currentStock ?? 0, "opening stock");
      if (b.image !== undefined) {
        if (b.image === null || b.image === "") clean.image = null;
        else {
          if (typeof b.image !== "string") fail("Choose a PNG or JPEG image.");
          const m =
            /^data:(image\/(?:png|jpeg));base64,([A-Za-z0-9+/]+={0,2})$/.exec(
              b.image,
            );
          if (!m) fail("Choose a PNG or JPEG image.");
          const bytes = Buffer.from(m[2], "base64");
          if (
            bytes.length > 2 * 1024 * 1024 ||
            bytes.toString("base64") !== m[2]
          )
            fail("Use an image up to 2 MB.", 413);
          try {
            const meta = await sharp(bytes, {
              limitInputPixels: 2048 * 2048,
            }).metadata();
            if (
              meta.width! > 2048 ||
              meta.height! > 2048 ||
              (meta.pages ?? 1) !== 1 ||
              `image/${meta.format}` !== m[1]
            )
              fail("Use a single image up to 2048 pixels per side.");
            await sharp(bytes).stats();
          } catch (e) {
            if (e instanceof BusinessError) throw e;
            fail("The product image could not be read.");
          }
          clean.image = b.image;
        }
      }
      const [saved] = await deps.query(
        "SELECT beautycore_inventory_save($1,$2,$3::jsonb) AS id",
        [actor.id, productId, JSON.stringify(clean)],
      );
      return json({ item: saved }, request.method === "POST" ? 201 : 200);
    }
    if (section === "products" && request.method === "DELETE") {
      const product = id(p.get("id"));
      const [result] = await deps.query(
        `SELECT beautycore_inventory_archive($1,$2) AS result`,
        [product, actor.id],
      );
      return json({ result: result.result });
    }
    if (section === "suppliers") {
      if (request.method === "GET")
        return json({
          suppliers: await deps.query(
            "SELECT * FROM inventory_suppliers ORDER BY name,id",
          ),
        });
      if (!["POST", "PATCH"].includes(request.method))
        fail("Operation not found.", 404);
      let b = await boundedJson(request);
      const supplier = request.method === "PATCH" ? id(b.id) : null;
      if (supplier) {
        const [existing] = await deps.query(
          "SELECT * FROM inventory_suppliers WHERE id=$1",
          [supplier],
        );
        if (!existing) fail("Supplier not found.", 404);
        b = { ...existing, ...b };
      }
      const values = [
        text(b.name, "Supplier name", 160, true),
        text(b.contact, "Contact person", 160),
        text(b.email, "Email", 255),
        text(b.phone, "Phone", 64),
        text(b.address, "Address", 500),
        text(b.notes, "Notes", 1000),
        b.active ?? true,
      ];
      if (values[2] && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(values[2])))
        fail("Enter a valid supplier email.");
      if (typeof values[6] !== "boolean") fail("Invalid supplier status.");
      const rows = await deps.query(
        supplier
          ? "UPDATE inventory_suppliers SET name=$1,contact=$2,email=$3,phone=$4,address=$5,notes=$6,active=$7 WHERE id=$8 RETURNING id"
          : "INSERT INTO inventory_suppliers(name,contact,email,phone,address,notes,active) VALUES($1,$2,$3,$4,$5,$6,$7) RETURNING id",
        supplier ? [...values, supplier] : values,
      );
      if (!rows[0]) fail("Supplier not found.", 404);
      return json({ supplier: rows[0] }, supplier ? 200 : 201);
    }
    if (section === "policy") {
      if (request.method === "GET")
        return json({
          policy: (
            await deps.query(
              'SELECT shortage_policy AS "shortagePolicy",expiry_warning_days AS "expiryWarningDays",consumption_mode AS "consumptionMode" FROM inventory_policy',
            )
          )[0],
        });
      const b = await boundedJson(request);
      if (
        !["block", "consume_available"].includes(String(b.shortagePolicy)) ||
        (b.consumptionMode !== undefined && !["reported_only", "configured"].includes(String(b.consumptionMode))) ||
        !Number.isInteger(b.expiryWarningDays) ||
        Number(b.expiryWarningDays) < 1 ||
        Number(b.expiryWarningDays) > 365
      )
        fail("Choose a valid shortage policy and expiry warning period.");
      await deps.query(
        "UPDATE inventory_policy SET shortage_policy=$1,expiry_warning_days=$2,consumption_mode=coalesce($3,consumption_mode) WHERE id=true",
        [b.shortagePolicy, b.expiryWarningDays, b.consumptionMode ?? null],
      );
      return json({ saved: true });
    }
    if (section === "requirements") {
      let service = p.get("serviceId");
      if (p.get("appointmentId")) {
        const appointment = id(p.get("appointmentId"));
        const [row] = await deps.query(
          `SELECT coalesce(x.service_id,(SELECT id FROM salon_services WHERE name=a.service_name AND service_type=a.service_type)) AS service FROM appointments a LEFT JOIN appointment_services x ON x.appointment_id=a.id WHERE a.id=$1 AND ($2='admin' OR a.stylist_id=$3)`,
          [appointment, actor.role, actor.id],
        );
        if (!row) fail("Appointment not found.", 404);
        service = String(row.service ?? "");
      }
      if (request.method === "GET") {
        const rows = service
          ? await deps.query(
              `SELECT ${fields},r.quantity::float8 AS "estimatedQuantity",r.service_id AS "serviceId" ${joins} JOIN service_inventory_requirements r ON r.inventory_id=i.id WHERE r.service_id=$1 ORDER BY i.product_name`,
              [service],
            )
          : [];
        return json({
          requirements: rows.map((r) => sanitize(r, admin)),
          serviceId: service || null,
          consumptionMode: (await deps.query("SELECT consumption_mode FROM inventory_policy WHERE id=true"))[0]?.consumption_mode ?? "reported_only",
        });
      }
      const b = await boundedJson(request, 65536);
      if (
        typeof b.serviceId !== "string" ||
        !Array.isArray(b.requirements) ||
        b.requirements.length > 40
      )
        fail("Choose a service and up to 40 requirements.");
      const rows = b.requirements.map((r: Record<string, unknown>) => ({
        inventoryId: id(r.inventoryId),
        quantity: number(r.quantity, "required quantity"),
        unit: text(r.unit, "Unit", 32, true),
      }));
      if (
        rows.some((r) => !r.quantity) ||
        new Set(rows.map((r) => r.inventoryId)).size !== rows.length
      )
        fail(
          "Each required product needs a positive quantity and must appear once.",
        );
      await deps.query(
        "SELECT beautycore_inventory_requirements($1,$2,$3::jsonb)",
        [actor.id, b.serviceId, JSON.stringify(rows)],
      );
      return json({ saved: true });
    }
    if (section === "transactions" && request.method === "POST") {
      const b = await boundedJson(request);
      const product = id(b.id);
      const kind = b.kind ?? (b.direction === "in" ? "stock_in" : "stock_out");
      const allowed = [
        "stock_in",
        "stock_out",
        "adjustment",
        "correction",
        "damaged",
        "expired",
      ];
      if (!allowed.includes(String(kind)))
        fail("Choose a valid stock transaction.");
      const clean: Record<string, unknown> = {
        kind,
        requestId: id(b.requestId),
        direction: b.direction,
        reason: text(
          b.reason ?? b.note,
          "Reason",
          1000,
          !["stock_in"].includes(String(kind)),
        ),
        unit: text(b.unit, "Unit", 32, true),
        unitCost: number(b.unitCost, "purchase cost", true, 2),
        supplierId: b.supplierId ? id(b.supplierId) : null,
        reference: text(b.reference, "Reference", 160),
        appointmentId: b.appointmentId ? id(b.appointmentId) : null,
      };
      if (kind === "adjustment") {
        clean.previousQuantity = number(
          b.previousQuantity,
          "previous quantity",
        );
        clean.adjustedQuantity = number(
          b.adjustedQuantity,
          "adjusted quantity",
        );
      } else clean.quantity = number(b.quantity, "quantity");
      if (kind !== "adjustment" && Number(clean.quantity) <= 0)
        fail("Enter a positive transaction quantity.");
      if (b.occurredAt) {
        if (
          typeof b.occurredAt !== "string" ||
          !/(?:Z|[+-]\d{2}:\d{2})$/.test(b.occurredAt) ||
          !Number.isFinite(Date.parse(b.occurredAt)) ||
          Date.parse(b.occurredAt) > Date.now() + 60000
        )
          fail(
            "Choose a valid received/withdrawal date that is not in the future.",
          );
        clean.occurredAt = new Date(b.occurredAt).toISOString();
      }
      const [row] = await deps.query(
        "SELECT beautycore_inventory_post($1,$2,$3::jsonb) AS id",
        [product, actor.id, JSON.stringify(clean)],
      );
      return json({ transaction: row }, 201);
    }
    if (["transactions", "reports", "summary"].includes(section))
      return inventoryReport(request, section, deps);
    fail("Operation not found.", 404);
  } catch (e) {
    if (e instanceof BusinessError) return json({ error: e.message }, e.status);
    const error = e as { code?: string; message?: string };
    const message = error.message ?? "";
    const friendly: Record<string, string> = {
      insufficient_stock: "Insufficient stock. No changes were saved.",
      stock_changed:
        "Stock changed. Refresh the product and review the adjustment.",
      unit_mismatch:
        "These units cannot be converted. Use the product stock unit.",
      quantity_precision: "The converted quantity needs more than 3 decimals.",
      request_conflict:
        "This request was already used for different transaction details.",
      product_unavailable: "Inactive or expired products cannot be consumed.",
      reason_required: "A reason is required.",
      product_not_found: "Product not found.",
      invalid_supplier:'Choose an active supplier.',
    };
    const match = Object.keys(friendly).find((k) => message.includes(k));
    return json(
      {
        error: match
          ? friendly[match]
          : error.code === "23505"
            ? "This SKU or entry already exists."
            : error.code === "22023" || error.code === "23514"
              ? message
              : "Inventory could not be updated. Please try again.",
      },
      error.code === "42501"
        ? 403
        : error.code === "22023"
          ? 400
          : error.code?.startsWith("23")
            ? 409
            : 503,
    );
  }
}

async function inventoryReport(
  request: Request,
  section: string,
  deps: HistoryDependencies,
) {
  const p = new URL(request.url).searchParams,
    { from, to } = dates(p),
    { page, limit, offset } = pagination(p);
  const values: unknown[] = [
    from,
    to,
    p.get("product") ? id(p.get("product")) : null,
    p.get("kind"),
    p.get("category"),
    p.get("supplier") ? id(p.get("supplier")) : null,
    p.get("staff") ? id(p.get("staff")) : null,
  ];
  const where = `($1::text IS NULL OR coalesce(d.occurred_at,t.created_at)>=($1::date::timestamp AT TIME ZONE 'Asia/Manila')) AND ($2::text IS NULL OR coalesce(d.occurred_at,t.created_at)<(($2::date+1)::timestamp AT TIME ZONE 'Asia/Manila')) AND ($3::uuid IS NULL OR t.inventory_id=$3) AND ($4::text IS NULL OR coalesce(d.kind,CASE WHEN t.direction='in' THEN 'stock_in' ELSE 'stock_out' END)=$4) AND ($5::text IS NULL OR coalesce(d.category,i.category)=$5) AND ($6::uuid IS NULL OR d.supplier_id=$6) AND ($7::uuid IS NULL OR t.recorded_by=$7)`;
  const ledger = `FROM inventory_transactions t LEFT JOIN inventory_transaction_details d ON d.transaction_id=t.id LEFT JOIN inventory i ON i.id=t.inventory_id LEFT JOIN users u ON u.id=t.recorded_by`;
  if (section === "transactions") {
    const [rows, count, staff, categories] = await Promise.all([
      deps.query(
        `SELECT t.id,t.inventory_id AS "inventoryId",t.product_name AS "productName",t.direction,t.quantity::float8 AS quantity,t.stock_after::float8 AS "stockAfter",t.created_at AS "createdAt",t.recorded_by AS "recordedBy",u.name AS "staffName",coalesce(d.kind,CASE WHEN t.direction='in' THEN 'stock_in' ELSE 'stock_out' END) AS kind,d.unit,coalesce(d.reason,t.note) AS reason,d.previous_quantity::float8 AS "previousQuantity",d.unit_cost::float8 AS "unitCost",(t.quantity*d.unit_cost)::float8 AS "totalCost",d.supplier_name AS "supplierName",d.reference,d.occurred_at AS "occurredAt",d.appointment_id AS "appointmentId",d.service_id AS "serviceId",d.category ${ledger} WHERE ${where} ORDER BY coalesce(d.occurred_at,t.created_at) DESC,t.id LIMIT $8 OFFSET $9`,
        [...values, limit, offset],
      ),
      deps.query(
        `SELECT count(*)::int AS total ${ledger} WHERE ${where}`,
        values,
      ),
      deps.query(
        "SELECT DISTINCT u.id,u.name FROM inventory_transactions t JOIN users u ON u.id=t.recorded_by ORDER BY u.name,u.id",
      ),
      deps.query(
        "SELECT DISTINCT coalesce(d.category,i.category) AS category FROM inventory_transactions t LEFT JOIN inventory_transaction_details d ON d.transaction_id=t.id LEFT JOIN inventory i ON i.id=t.inventory_id ORDER BY category",
      ),
    ]);
    return json({
      transactions: rows,
      total: count[0].total,
      page,
      limit,
      staff,
      categories: categories.map((c) => c.category).filter(Boolean),
    });
  }
  const [stats, risk, shortages] = await Promise.all([
    deps.query(
      `SELECT count(*)::int AS total,count(*) FILTER(WHERE coalesce(d.item_type,'consumable')='consumable')::int AS consumables,count(*) FILTER(WHERE d.item_type='equipment')::int AS equipment,coalesce(sum(i.current_stock*d.purchase_cost),0)::float8 AS value,count(*) FILTER(WHERE d.purchase_cost IS NULL)::int AS unpriced,count(*) FILTER(WHERE coalesce(d.active,true) AND i.current_stock>0 AND i.current_stock<=i.minimum_threshold)::int AS low,count(*) FILTER(WHERE coalesce(d.active,true) AND i.current_stock=0)::int AS out,count(*) FILTER(WHERE coalesce(d.active,true) AND d.expiration_date<(now() AT TIME ZONE 'Asia/Manila')::date)::int AS expired,count(*) FILTER(WHERE coalesce(d.active,true) AND d.expiration_date BETWEEN (now() AT TIME ZONE 'Asia/Manila')::date AND (now() AT TIME ZONE 'Asia/Manila')::date+(SELECT expiry_warning_days FROM inventory_policy))::int AS expiring ${joins}`,
    ),
    deps.query(
      `SELECT s.id,s.name,count(*)::int AS shortages FROM service_inventory_requirements r JOIN salon_services s ON s.id=r.service_id JOIN inventory i ON i.id=r.inventory_id LEFT JOIN inventory_details d ON d.inventory_id=i.id WHERE s.active AND (r.quantity>i.current_stock OR d.active=false OR d.expiration_date<(now() AT TIME ZONE 'Asia/Manila')::date) GROUP BY s.id,s.name ORDER BY s.name`,
    ),
    deps.query(
      `SELECT c.*,a.service_name AS "serviceName",u.name AS "staffName",greatest(c.shortage-coalesce((SELECT sum(CASE WHEN t.direction='out' THEN t.quantity ELSE -t.quantity END) FROM inventory_transactions t JOIN inventory_transaction_details d ON d.transaction_id=t.id WHERE t.inventory_id=c.inventory_id AND d.appointment_id=c.appointment_id AND d.kind='correction'),0),0)::float8 AS remaining FROM inventory_service_consumption c JOIN appointments a ON a.id=c.appointment_id JOIN users u ON u.id=c.recorded_by WHERE c.shortage>0 ORDER BY c.created_at DESC LIMIT 50`,
    ),
  ]);
  const unresolved = shortages.filter((s) => Number(s.remaining) > 0);
  if (section === "summary") {
    const [recentProducts, recentMovements] = await Promise.all([
      deps.query(
        'SELECT id,product_name AS "productName",category,created_at AT TIME ZONE \'UTC\' AS "createdAt" FROM inventory ORDER BY created_at DESC,id LIMIT 5',
      ),
      deps.query(
        'SELECT t.id,t.product_name AS "productName",t.direction,t.quantity::float8 AS quantity,t.created_at AS "createdAt",d.unit,d.kind FROM inventory_transactions t LEFT JOIN inventory_transaction_details d ON d.transaction_id=t.id ORDER BY t.created_at DESC,t.id LIMIT 8',
      ),
    ]);
    return json({
      stats: stats[0],
      servicesAtRisk: risk,
      shortages: unresolved,
      recentProducts,
      recentMovements,
    });
  }
  const [consumption, expenses, byDay, serviceUsage, waste] = await Promise.all(
    [
      deps.query(
        `SELECT t.inventory_id AS "inventoryId",t.product_name AS "productName",d.unit,count(*)::int AS uses,coalesce(sum(CASE WHEN t.direction='out' THEN t.quantity ELSE -t.quantity END),0)::float8 AS quantity,coalesce(sum(CASE WHEN t.direction='out' THEN t.quantity*d.unit_cost ELSE -t.quantity*d.unit_cost END),0)::float8 AS cost ${ledger} WHERE ${where} AND d.kind IN ('service_consumption','correction') GROUP BY t.inventory_id,t.product_name,d.unit ORDER BY uses DESC LIMIT 50`,
        values,
      ),
      deps.query(
        `SELECT coalesce(sum(t.quantity*d.unit_cost),0)::float8 AS total,count(*) FILTER(WHERE d.unit_cost IS NULL)::int AS unpriced ${ledger} WHERE ${where} AND d.kind='stock_in'`,
        values,
      ),
      deps.query(
        `SELECT (coalesce(d.occurred_at,t.created_at) AT TIME ZONE 'Asia/Manila')::date::text AS day,d.unit,sum(CASE WHEN t.direction='out' THEN t.quantity ELSE -t.quantity END)::float8 AS quantity,sum(CASE WHEN t.direction='out' THEN t.quantity*d.unit_cost ELSE -t.quantity*d.unit_cost END)::float8 AS cost ${ledger} WHERE ${where} AND d.kind IN ('service_consumption','correction') GROUP BY day,d.unit ORDER BY day DESC LIMIT 100`,
        values,
      ),
      deps.query(
        `SELECT s.name AS "serviceName",t.product_name AS "productName",d.unit,sum(CASE WHEN t.direction='out' THEN t.quantity ELSE -t.quantity END)::float8 AS quantity ${ledger} JOIN salon_services s ON s.id=d.service_id WHERE ${where} AND d.kind IN ('service_consumption','correction') GROUP BY s.name,t.product_name,d.unit ORDER BY s.name LIMIT 100`,
        values,
      ),
      deps.query(
        `SELECT t.product_name AS "productName",d.kind,d.unit,sum(t.quantity)::float8 AS quantity,sum(t.quantity*d.unit_cost)::float8 AS cost ${ledger} WHERE ${where} AND d.kind IN ('damaged','expired') GROUP BY t.product_name,d.kind,d.unit ORDER BY t.product_name LIMIT 100`,
        values,
      ),
    ],
  );
  return json({
    stats: stats[0],
    servicesAtRisk: risk,
    shortages: unresolved,
    consumption,
    purchaseExpenses: expenses[0],
    byDay,
    serviceUsage,
    waste,
    timeZone: "Asia/Manila",
  });
}
