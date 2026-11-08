import { NextResponse } from 'next/server';
import { eq, asc } from 'drizzle-orm';
import { db, databaseSql } from '@/db';
import { inventory, type ProductStatus } from '@/db/schema';
import { requireRole } from '@/lib/auth';
import { mutationOrigin } from '@/lib/business/core';

/** Keeps `status` consistent with the stock numbers. */
function deriveStatus(stock: number, threshold: number): ProductStatus {
  if (stock <= 0) return 'out_of_stock';
  if (stock <= threshold) return 'low_stock';
  return 'in_stock';
}
function whole(value: unknown, min: number, max: number) {
  return typeof value === 'number' && Number.isSafeInteger(value) && value >= min && value <= max;
}

/** GET /api/inventory — admin and stylists can read. */
export async function GET() {
  try {
    const session = await requireRole(['admin', 'stylist']);
    if (!session) {
      return NextResponse.json({ error: 'Not allowed.' }, { status: 403 });
    }
    const rows = await db
      .select()
      .from(inventory)
      .orderBy(asc(inventory.category), asc(inventory.productName));

    return NextResponse.json({ inventory: rows });
  } catch (error) {
    console.error('[api/inventory GET]', error);
    return NextResponse.json({ error: 'Could not load inventory.' }, { status: 500 });
  }
}

/** POST /api/inventory — admin only. */
export async function POST(req: Request) {
  try {
    const session = await requireRole(['admin']);
    if (!session) {
      return NextResponse.json({ error: 'Admins only.' }, { status: 403 });
    }
    mutationOrigin(req, process.env.RENDER_EXTERNAL_URL);

    const body = await req.json();
    const productName = typeof body.productName === 'string' ? body.productName.trim() : '';
    const category = typeof body.category === 'string' ? body.category.trim() : '';
    if (body.brand != null && (typeof body.brand !== 'string' || body.brand.trim().length > 120))
      return NextResponse.json({ error: 'Brand must be up to 120 characters.' }, { status: 400 });

    if (!productName || !category) {
      return NextResponse.json(
        { error: 'Product name and category are required.' },
        { status: 400 },
      );
    }

    const currentStock = body.currentStock ?? 0;
    const minimumThreshold = body.minimumThreshold ?? 10;
    const unitPrice = body.unitPrice ?? null;

    if (!whole(currentStock, 0, 10000000) || !whole(minimumThreshold, 0, 10000000) || (unitPrice !== null && !whole(unitPrice, 0, 100000000))) {
      return NextResponse.json({ error: 'Stock, threshold, and price must be valid nonnegative whole numbers.' }, { status: 400 });
    }
    const [created] = await databaseSql.query(
      'SELECT * FROM beautycore_create_inventory_item($1,$2,$3,$4,$5,$6,$7)',
      [productName, typeof body.brand === 'string' ? body.brand.trim() || null : null, category, currentStock, minimumThreshold, unitPrice, session.userId],
    );
    const item = created ? await db.query.inventory.findFirst({ where: eq(inventory.id, String(created.id)) }) : null;

    return NextResponse.json({ item }, { status: 201 });
  } catch (error) {
    console.error('[api/inventory POST]', error);
    return NextResponse.json({ error: 'Could not add product.' }, { status: 500 });
  }
}

/** PATCH /api/inventory — update stock or details. Admin only. */
export async function PATCH(req: Request) {
  try {
    const session = await requireRole(['admin']);
    if (!session) {
      return NextResponse.json({ error: 'Admins only.' }, { status: 403 });
    }
    mutationOrigin(req, process.env.RENDER_EXTERNAL_URL);

    const body = await req.json();
    const id = String(body.id ?? '');
    if (!id) {
      return NextResponse.json({ error: 'Product id is required.' }, { status: 400 });
    }

    const existing = await db.query.inventory.findFirst({
      where: eq(inventory.id, id),
    });
    if (!existing) {
      return NextResponse.json({ error: 'Product not found.' }, { status: 404 });
    }

    if (body.currentStock !== undefined)
      return NextResponse.json({ error: 'Use the stock transaction endpoint to record stock-in or stock-out.' }, { status: 400 });

    const updates: Partial<typeof inventory.$inferInsert> = {};
    if (body.brand !== undefined) {
      if (body.brand !== null && (typeof body.brand !== 'string' || body.brand.trim().length > 120))
        return NextResponse.json({ error: 'Brand must be up to 120 characters.' }, { status: 400 });
      updates.brand = typeof body.brand === 'string' ? body.brand.trim() || null : null;
    }

    if (body.productName !== undefined) {
      if (typeof body.productName !== 'string' || !body.productName.trim() || body.productName.trim().length > 255)
        return NextResponse.json({ error: 'Enter a product name up to 255 characters.' }, { status: 400 });
      updates.productName = body.productName.trim();
    }
    if (body.category !== undefined) {
      if (typeof body.category !== 'string' || !body.category.trim() || body.category.trim().length > 100)
        return NextResponse.json({ error: 'Enter a category up to 100 characters.' }, { status: 400 });
      updates.category = body.category.trim();
    }
    if (body.unitPrice !== undefined) {
      if (body.unitPrice !== null && !whole(body.unitPrice, 0, 100000000))
        return NextResponse.json({ error: 'Enter a nonnegative whole-peso price.' }, { status: 400 });
      updates.unitPrice = body.unitPrice as number | null;
    }
    if (body.minimumThreshold !== undefined) {
      if (!whole(body.minimumThreshold, 0, 10000000))
        return NextResponse.json({ error: 'Threshold must be a nonnegative whole number.' }, { status: 400 });
      updates.minimumThreshold = body.minimumThreshold;
      updates.status = deriveStatus(existing.currentStock, body.minimumThreshold);
    }
    if (body.status !== undefined)
      return NextResponse.json({ error: 'Inventory status is calculated from stock and threshold.' }, { status: 400 });
    if (!Object.keys(updates).length)
      return NextResponse.json({ error: 'Provide at least one product detail to update.' }, { status: 400 });

    const [updated] = await db
      .update(inventory)
      .set(updates)
      .where(eq(inventory.id, id))
      .returning();

    return NextResponse.json({ item: updated });
  } catch (error) {
    console.error('[api/inventory PATCH]', error);
    return NextResponse.json({ error: 'Could not update product.' }, { status: 500 });
  }
}

/** DELETE /api/inventory?id=... — admin only. */
export async function DELETE(req: Request) {
  try {
    const session = await requireRole(['admin']);
    if (!session) {
      return NextResponse.json({ error: 'Admins only.' }, { status: 403 });
    }
    mutationOrigin(req, process.env.RENDER_EXTERNAL_URL);

    const id = new URL(req.url).searchParams.get('id');
    if (!id) {
      return NextResponse.json({ error: 'Product id is required.' }, { status: 400 });
    }

    const removed = await db
      .delete(inventory)
      .where(eq(inventory.id, id))
      .returning({ id: inventory.id });

    if (removed.length === 0) {
      return NextResponse.json({ error: 'Product not found.' }, { status: 404 });
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('[api/inventory DELETE]', error);
    return NextResponse.json({ error: 'Could not delete product.' }, { status: 500 });
  }
}
