import 'server-only';
import { sql } from 'drizzle-orm';
import { db } from '@/db';
import { LEASE_SECONDS, type RuntimeLease, type RuntimeMessage, type RuntimeStore } from './runtime-registry';

function lease(row?: Record<string, unknown>): RuntimeLease | null {
  return row ? { sessionId: String(row.session_id), endpoint: String(row.endpoint),
    startedAt: Number(row.started_at), lastIssuedAt: Number(row.last_issued_at),
    expiresAt: new Date(String(row.lease_expires_at)).getTime() } : null;
}
export const runtimeStore: RuntimeStore = {
  async get() {
    const result = await db.execute(sql`SELECT session_id, endpoint, started_at, last_issued_at, lease_expires_at
      FROM ai_runtime_endpoints WHERE slot = 'primary'`);
    return lease(result.rows[0]);
  },
  async claim(m: RuntimeMessage) {
    const result = await db.execute(sql`INSERT INTO ai_runtime_endpoints
      (slot, session_id, endpoint, started_at, last_issued_at, lease_expires_at, updated_at)
      VALUES ('primary', ${m.session_id}::uuid, ${m.endpoint}, ${m.started_at}, ${m.issued_at},
        now() + ${LEASE_SECONDS} * interval '1 second', now())
      ON CONFLICT (slot) DO UPDATE SET session_id = EXCLUDED.session_id, endpoint = EXCLUDED.endpoint,
        started_at = EXCLUDED.started_at, last_issued_at = EXCLUDED.last_issued_at,
        lease_expires_at = EXCLUDED.lease_expires_at, updated_at = now()
      WHERE EXCLUDED.last_issued_at > ai_runtime_endpoints.last_issued_at AND (
        (ai_runtime_endpoints.session_id = EXCLUDED.session_id AND ai_runtime_endpoints.endpoint = EXCLUDED.endpoint
          AND ai_runtime_endpoints.started_at = EXCLUDED.started_at)
        OR (ai_runtime_endpoints.lease_expires_at <= now() AND EXCLUDED.started_at > ai_runtime_endpoints.started_at))
      RETURNING session_id, endpoint, started_at, last_issued_at, lease_expires_at`);
    return lease(result.rows[0]);
  },
  async renew(m: RuntimeMessage) {
    const result = await db.execute(sql`UPDATE ai_runtime_endpoints
      SET last_issued_at = ${m.issued_at}, lease_expires_at = now() + ${LEASE_SECONDS} * interval '1 second', updated_at = now()
      WHERE slot = 'primary' AND session_id = ${m.session_id}::uuid AND endpoint = ${m.endpoint}
        AND started_at = ${m.started_at} AND last_issued_at < ${m.issued_at} AND lease_expires_at > now()
      RETURNING session_id, endpoint, started_at, last_issued_at, lease_expires_at`);
    return lease(result.rows[0]);
  },
};
