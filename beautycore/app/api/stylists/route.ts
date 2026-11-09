import { NextResponse } from 'next/server';
import { db, databaseSql } from '@/db';
import { users } from '@/db/schema';
import { hashPassword, requireRole } from '@/lib/auth';
import { serviceGroups, serviceDurationMinutes } from '@/lib/services';
import { mutationOrigin } from '@/lib/business/core';

export const dynamic = 'force-dynamic';
const serviceTypes = serviceGroups.map((group) => group.serviceType);

/** Public booking list is always restricted to active, qualified staff. */
export async function GET(request: Request) {
  try {
    const params = new URL(request.url).searchParams;
    const manage = params.get('manage') === 'true';
    if (manage && !(await requireRole(['admin'])))
      return NextResponse.json({ error: 'Admins only.' }, { status: 403 });
    const serviceType = params.get('serviceType');
    if (serviceType && !serviceTypes.includes(serviceType as (typeof serviceTypes)[number]))
      return NextResponse.json({ error: 'Invalid service type.' }, { status: 400 });
    const serviceName = params.get('serviceName') ?? '';
    const date = params.get('appointmentDate');
    if (date && (!/(?:Z|[+-]\d{2}:\d{2})$/.test(date) || !Number.isFinite(Date.parse(date))))
      return NextResponse.json({ error: 'Invalid appointment time.' }, { status: 400 });
    const duration = serviceDurationMinutes(serviceName, serviceType ?? '');
    const rows = await databaseSql.query(
      `SELECT u.id,u.name,u.avatar,u.is_active AS "isActive",CASE WHEN $1::boolean THEN u.email ELSE NULL END AS email,
        EXISTS(SELECT 1 FROM stylist_work_settings w WHERE w.stylist_id=u.id AND w.available) AS "workAvailable",
        coalesce(array_agg(DISTINCT ss.service_type) FILTER(WHERE ss.service_type IS NOT NULL),'{}') AS specialties
       FROM users u LEFT JOIN stylist_specialties ss ON ss.stylist_id=u.id
       WHERE u.role='stylist' AND ($1::boolean OR u.is_active)
         AND ($1::boolean OR EXISTS(SELECT 1 FROM stylist_work_settings w WHERE w.stylist_id=u.id AND w.available))
         AND ($1::boolean OR $3::timestamptz IS NULL OR beautycore_work_available(u.id,$3::timestamptz,$4))
         AND ($2::text IS NULL OR ss.service_type=$2)
         AND ($3::timestamptz IS NULL OR NOT EXISTS(
           SELECT 1 FROM appointments a WHERE a.stylist_id=u.id AND a.status IN ('pending','confirmed')
            AND ($3::timestamptz AT TIME ZONE 'UTC') < a.appointment_date + make_interval(mins=>90)
            AND a.appointment_date < ($3::timestamptz AT TIME ZONE 'UTC') + make_interval(mins=>$4)))
       GROUP BY u.id ORDER BY u.name,u.id`,
      [manage, serviceType, date, duration],
    );
    return NextResponse.json({ stylists: rows });
  } catch (error) {
    console.error('[api/stylists GET]', error);
    return NextResponse.json({ error: 'Could not load stylists.' }, { status: 500 });
  }
}

/** Stylist accounts can only be created by an administrator. */
export async function POST(request: Request) {
  try {
    if (!(await requireRole(['admin'])))
      return NextResponse.json({ error: 'Admins only.' }, { status: 403 });
    mutationOrigin(request, process.env.RENDER_EXTERNAL_URL);
    const body = await request.json();
    const name = typeof body.name === 'string' ? body.name.trim() : '';
    const email = typeof body.email === 'string' ? body.email.trim().toLowerCase() : '';
    const password = typeof body.password === 'string' ? body.password : '';
    const specialties = Array.isArray(body.specialties) ? [...new Set(body.specialties)] : [];
    if (!name || name.length > 255 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length > 255 || password.length < 8 || password.length > 128)
      return NextResponse.json({ error: 'Enter a name, valid email, and password of at least 8 characters.' }, { status: 400 });
    if (!specialties.length || specialties.some((type) => typeof type !== 'string' || !serviceTypes.includes(type as (typeof serviceTypes)[number])))
      return NextResponse.json({ error: 'Assign at least one valid service specialty.' }, { status: 400 });
    const hash = await hashPassword(password);
    const rows = await databaseSql.query(
      'SELECT * FROM beautycore_create_stylist($1,$2,$3,$4::text[])',
      [name,email,hash,specialties],
    );
    return NextResponse.json({ stylist: rows[0] }, { status: 201 });
  } catch (error) {
    console.error('[api/stylists POST]', error);
    return NextResponse.json({ error: 'Could not create stylist. The email may already be in use.' }, { status: 409 });
  }
}

/** Update only a stylist; role changes are never accepted from this endpoint. */
export async function PATCH(request: Request) {
  try {
    if (!(await requireRole(['admin'])))
      return NextResponse.json({ error: 'Admins only.' }, { status: 403 });
    mutationOrigin(request, process.env.RENDER_EXTERNAL_URL);
    const body = await request.json();
    const id = typeof body.id === 'string' ? body.id : '';
    const name = typeof body.name === 'string' ? body.name.trim() : '';
    const email = typeof body.email === 'string' ? body.email.trim().toLowerCase() : '';
    const specialties = Array.isArray(body.specialties) ? [...new Set(body.specialties)] : [];
    if (!id || !name || name.length > 255 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length > 255 || typeof body.isActive !== 'boolean')
      return NextResponse.json({ error: 'Enter valid stylist details and account status.' }, { status: 400 });
    if (specialties.some((type) => typeof type !== 'string' || !serviceTypes.includes(type as (typeof serviceTypes)[number])))
      return NextResponse.json({ error: 'Choose valid service specialties.' }, { status: 400 });
    const result = await databaseSql.query(
      'SELECT beautycore_update_stylist($1,$2,$3,$4,$5::text[]) AS updated',
      [id,name,email,body.isActive,specialties],
    );
    if (!result[0]?.updated) return NextResponse.json({ error: 'Stylist not found.' }, { status: 404 });
    const stylist = await db.query.users.findFirst({ where: (u, { eq }) => eq(u.id, id), columns: { id: true, name: true, email: true, isActive: true } });
    return NextResponse.json({ stylist: { ...stylist, specialties } });
  } catch (error) {
    console.error('[api/stylists PATCH]', error);
    return NextResponse.json({ error: 'Could not update stylist details.' }, { status: 409 });
  }
}
