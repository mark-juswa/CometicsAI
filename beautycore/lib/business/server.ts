import 'server-only';
import { databaseSql } from '../../db';
import { getSession } from '../auth';
import { createBusinessStore } from './store';
import type { Dependencies } from './api';
const store = createBusinessStore(async (text, values = []) => databaseSql.query(text, values));
function limit(name: string, fallback: number, max: number, min = 1) {
  const value = Number(process.env[name] ?? fallback);
  return Number.isSafeInteger(value) && value >= min && value <= max ? value : fallback;
}
export const businessDependencies: Dependencies = {
  store,
  actor: async () => {
    const session = await getSession();
    if (!session) return null;
    return (await store.currentUser(session.userId)) ?? null;
  },
  publicOrigin: process.env.RENDER_EXTERNAL_URL,
  settings: {
    enabled: process.env.SAVED_LOOKS_ENABLED === 'true',
    clientLimit: limit('SAVED_LOOKS_CLIENT_LIMIT', 20, 100),
    storageBudget: limit(
      'SAVED_LOOKS_STORAGE_BYTES',
      128 * 1024 * 1024,
      256 * 1024 * 1024,
      1024 * 1024,
    ),
  },
};
