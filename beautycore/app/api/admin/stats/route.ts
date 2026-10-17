import { NextResponse } from 'next/server';
import { sql, eq, gte, and, desc, lt } from 'drizzle-orm';
import { db } from '@/db';
import { appointments, inventory, users } from '@/db/schema';
import { businessDependencies } from '@/lib/business/server';
import { salonDay } from '@/lib/business/dates';

/**
 * GET /api/admin/stats — dashboard aggregates.
 *
 * Revenue counts completed appointments only, so pending/cancelled bookings
 * don't inflate the figure.
 */
export async function GET() {
  try {
    const session = await businessDependencies.actor();
    if (!session || session.role !== 'admin') {
      return NextResponse.json({ error: 'Admins only.' }, { status: 403 });
    }

    const month = salonDay().slice(0, 7);
    const startOfMonth = new Date(month + '-01T00:00:00+08:00');
    const [year, monthNumber] = month.split('-').map(Number);
    const endOfMonth = new Date(Date.UTC(year, monthNumber, 1, -8));

    const [
      revenueRow,
      monthRevenueRow,
      bookingsRow,
      stylistsRow,
      lowStockItems,
      statusBreakdown,
      topServices,
    ] = await Promise.all([
      db
        .select({ total: sql<number>`coalesce(sum(total_price), 0)::bigint`.mapWith(Number) })
        .from(appointments)
        .where(eq(appointments.status, 'completed')),

      db
        .select({ total: sql<number>`coalesce(sum(total_price), 0)::bigint`.mapWith(Number) })
        .from(appointments)
        .where(
          and(
            eq(appointments.status, 'completed'),
            gte(appointments.appointmentDate, startOfMonth),
            lt(appointments.appointmentDate, endOfMonth),
          ),
        ),

      db.select({ n: sql<number>`count(*)::int` }).from(appointments),

      db
        .select({ n: sql<number>`count(*)::int` })
        .from(users)
        .where(eq(users.role, 'stylist')),

      db
        .select({
          id: inventory.id,
          productName: inventory.productName,
          category: inventory.category,
          currentStock: inventory.currentStock,
          minimumThreshold: inventory.minimumThreshold,
          status: inventory.status,
        })
        .from(inventory)
        .where(sql`current_stock <= minimum_threshold`)
        .orderBy(inventory.currentStock),

      db
        .select({
          status: appointments.status,
          n: sql<number>`count(*)::int`,
        })
        .from(appointments)
        .groupBy(appointments.status),

      db
        .select({
          serviceName: appointments.serviceName,
          serviceType: appointments.serviceType,
          bookings: sql<number>`count(*)::int`,
          revenue:
            sql<number>`coalesce(sum(total_price) filter (where status = 'completed'), 0)::bigint`.mapWith(
              Number,
            ),
        })
        .from(appointments)
        .groupBy(appointments.serviceName, appointments.serviceType)
        .orderBy(desc(sql`count(*)`))
        .limit(8),
    ]);

    const clientsRow = await db
      .select({ n: sql<number>`count(*)::int` })
      .from(users)
      .where(eq(users.role, 'client'));

    return NextResponse.json({
      stats: {
        totalRevenue: revenueRow[0]?.total ?? 0,
        monthRevenue: monthRevenueRow[0]?.total ?? 0,
        totalBookings: bookingsRow[0]?.n ?? 0,
        activeStylists: stylistsRow[0]?.n ?? 0,
        totalClients: clientsRow[0]?.n ?? 0,
        lowStockCount: lowStockItems.length,
      },
      lowStockItems,
      statusBreakdown,
      topServices,
    });
  } catch (error) {
    console.error('[api/admin/stats]', error);
    return NextResponse.json({ error: 'Could not load stats.' }, { status: 500 });
  }
}
