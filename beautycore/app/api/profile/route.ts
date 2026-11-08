import { NextResponse } from 'next/server';
import { eq } from 'drizzle-orm';
import { db } from '@/db';
import { users, clientProfiles } from '@/db/schema';
import { getSession } from '@/lib/auth';

/** GET /api/profile — the signed-in user plus their client profile. */
export async function GET() {
  try {
    const session = await getSession();
    if (!session) {
      return NextResponse.json({ error: 'Not signed in.' }, { status: 401 });
    }

    const user = await db.query.users.findFirst({
      where: eq(users.id, session.userId),
      columns: { id: true, name: true, email: true, role: true, avatar: true, phone: true, createdAt: true },
      with: { profile: true },
    });

    if (!user) {
      return NextResponse.json({ error: 'Account not found.' }, { status: 404 });
    }

    return NextResponse.json({ user });
  } catch (error) {
    console.error('[api/profile GET]', error);
    return NextResponse.json({ error: 'Could not load profile.' }, { status: 500 });
  }
}

/** PATCH /api/profile — update this account's personal and contact details. */
export async function PATCH(req: Request) {
  try {
    const session = await getSession();
    if (!session) {
      return NextResponse.json({ error: 'Not signed in.' }, { status: 401 });
    }

    const body = await req.json();
    if (!body || typeof body !== 'object' || Array.isArray(body))
      return NextResponse.json({ error: 'Invalid profile details.' }, { status: 400 });
    const { name, avatar, phone, hairPreferences, nailPreferences } = body;

    // Email and role are deliberately not editable here — changing email would
    // need re-verification, and role escalation must go through an admin.
    if (typeof name === 'string' || typeof avatar === 'string' || typeof phone === 'string') {
      const updates: Partial<typeof users.$inferInsert> = {};
      if (typeof name === 'string') {
        const trimmed = name.trim();
        if (!trimmed) {
          return NextResponse.json({ error: 'Name cannot be empty.' }, { status: 400 });
        }
        updates.name = trimmed.slice(0, 255);
      }
      if (typeof avatar === 'string') {
        if (avatar && (!/^data:image\/(?:png|jpeg);base64,[A-Za-z0-9+/]+={0,2}$/.test(avatar) || avatar.length > 550000))
          return NextResponse.json({ error: 'Choose a PNG or JPEG profile image up to 400 KB.' }, { status: 400 });
        updates.avatar = avatar || null;
      }
      if (typeof phone === 'string') {
        const trimmed = phone.trim();
        if (trimmed.length > 40 || (trimmed && !/^[+0-9(). -]{7,40}$/.test(trimmed)))
          return NextResponse.json({ error: 'Enter a valid contact number.' }, { status: 400 });
        updates.phone = trimmed || null;
      }

      await db.update(users).set(updates).where(eq(users.id, session.userId));
    }

    if (typeof hairPreferences === 'string' || typeof nailPreferences === 'string') {
      const prefs: Record<string, string> = {};
      if (typeof hairPreferences === 'string') prefs.hairPreferences = hairPreferences.slice(0, 2000);
      if (typeof nailPreferences === 'string') prefs.nailPreferences = nailPreferences.slice(0, 2000);

      const existing = await db.query.clientProfiles.findFirst({
        where: eq(clientProfiles.userId, session.userId),
      });

      if (existing) {
        await db
          .update(clientProfiles)
          .set(prefs)
          .where(eq(clientProfiles.userId, session.userId));
      } else {
        await db.insert(clientProfiles).values({ userId: session.userId, ...prefs });
      }
    }

    const updated = await db.query.users.findFirst({
      where: eq(users.id, session.userId),
      columns: { id: true, name: true, email: true, role: true, avatar: true, phone: true },
      with: { profile: true },
    });

    return NextResponse.json({ user: updated });
  } catch (error) {
    console.error('[api/profile PATCH]', error);
    return NextResponse.json({ error: 'Could not save changes.' }, { status: 500 });
  }
}
