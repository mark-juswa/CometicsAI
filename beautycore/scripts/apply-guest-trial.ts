/** Explicit opt-in only; never runs during build/startup. */
import { neon } from "@neondatabase/serverless";
import { config } from "dotenv";
import { guestTrialStatements } from "./guest-trial-migration";
config({ path: ".env.local", quiet: true });
try {
  if (!process.env.DATABASE_URL) throw new Error("Configuration missing");
  const query = neon(process.env.DATABASE_URL);
  if (process.argv.includes("--apply"))
    await query.transaction(
      guestTrialStatements().map((statement) => query.query(statement)),
    );
  const rows =
    await query.query(`SELECT to_regclass('ai_guest_trials') IS NOT NULL
    AND to_regprocedure('beautycore_guest_trial(text,text,text,jsonb)') IS NOT NULL AS applied`);
  console.log(
    JSON.stringify({
      guestTrialApplied: rows[0].applied,
      mode: process.argv.includes("--apply")
        ? "explicit-apply"
        : "read-only-schema-check",
    }),
  );
  if (!rows[0].applied) process.exitCode = 1;
} catch {
  console.error(
    "Guest trial migration/check failed; private details suppressed.",
  );
  process.exitCode = 1;
}
