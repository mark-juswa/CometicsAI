/** Apply only the reviewed operational table, without db:push or seeding. */
import { readFileSync } from 'node:fs';
import { neon } from '@neondatabase/serverless';
import { config } from 'dotenv';
config({ path: '.env.local', quiet: true });
try {
  if (!process.env.DATABASE_URL) throw new Error('Missing database configuration');
  const client = neon(process.env.DATABASE_URL);
  await client.query(readFileSync('db/migrations/0001_ai_runtime_endpoints.sql', 'utf8'));
  const rows = await client.query("SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'ai_runtime_endpoints'");
  const expected = ['slot','session_id','endpoint','started_at','last_issued_at','lease_expires_at','updated_at'].sort();
  if (rows.map(r => String(r.column_name)).sort().join(',') !== expected.join(',')) throw new Error('Unexpected registry schema');
  console.log('Registry table created/verified. No account or business data changed.');
} catch {
  console.error('Registry migration did not pass. Database credentials and provider errors are not printed.');
  process.exitCode = 1;
}
