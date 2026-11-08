import { NextResponse } from 'next/server';
import { desc, eq } from 'drizzle-orm';
import { db, inventory, inventoryTransactions, databaseSql } from '@/db';
import { requireRole } from '@/lib/auth';
import { mutationOrigin } from '@/lib/business/core';

export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  try {
    if (!(await requireRole(['admin']))) return NextResponse.json({ error: 'Admins only.' }, { status: 403 });
    const itemId = new URL(request.url).searchParams.get('itemId');
    const rows = await db.select().from(inventoryTransactions)
      .where(itemId ? eq(inventoryTransactions.inventoryId, itemId) : undefined)
      .orderBy(desc(inventoryTransactions.createdAt)).limit(100);
    return NextResponse.json({ transactions: rows });
  } catch (error) {
    console.error('[api/inventory/transactions GET]', error);
    return NextResponse.json({ error: 'Could not load inventory history.' }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const actor = await requireRole(['admin']);
    if (!actor) return NextResponse.json({ error: 'Admins only.' }, { status: 403 });
    mutationOrigin(request, process.env.RENDER_EXTERNAL_URL);
    const body = await request.json();
    if (typeof body.id !== 'string' || !['in','out'].includes(body.direction) || !Number.isSafeInteger(body.quantity) || body.quantity <= 0 || body.quantity > 1000000 || (body.note !== undefined && (typeof body.note !== 'string' || body.note.length > 500)))
      return NextResponse.json({ error: 'Enter a valid stock movement.' }, { status: 400 });
    const result = await databaseSql.query(
      'SELECT * FROM beautycore_inventory_move($1,$2,$3,$4,$5)',
      [body.id, actor.userId, body.direction, body.quantity, body.note ?? null],
    );
    const movement = result[0];
    if (movement?.outcome === 'missing') return NextResponse.json({ error: 'Product not found.' }, { status: 404 });
    if (movement?.outcome === 'insufficient') return NextResponse.json({ error: 'Stock-out quantity exceeds current stock.' }, { status: 409 });
    if (movement?.outcome !== 'updated') return NextResponse.json({ error: 'Invalid stock movement.' }, { status: 400 });
    const [item] = await db.select().from(inventory).where(eq(inventory.id, body.id));
    return NextResponse.json({ item, transaction: movement }, { status: 201 });
  } catch (error) {
    console.error('[api/inventory/transactions POST]', error);
    return NextResponse.json({ error: 'Could not record the stock movement.' }, { status: 500 });
  }
}
