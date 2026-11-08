import "server-only";
import { databaseSql } from "@/db";
import { getSession } from "@/lib/auth";
import type { HistoryDependencies } from "./customer-history";

export const historyDependencies: HistoryDependencies = {
  query: (sql, values) => databaseSql.query(sql, values),
  actor: async () => {
    const session = await getSession();
    return session ? { id: session.userId, role: session.role } : null;
  },
  publicOrigin: process.env.RENDER_EXTERNAL_URL,
};
