import "server-only";
import { databaseSql } from "@/db";
import type { TrialStore } from "./guest-trial";
export const guestTrialStore: TrialStore = {
  async act(action, hash, network, data = {}) {
    const rows = await databaseSql.query(
      "SELECT beautycore_guest_trial($1,$2,$3,$4::jsonb) AS result",
      [action, hash, network, JSON.stringify(data)],
    );
    return rows[0].result;
  },
};
