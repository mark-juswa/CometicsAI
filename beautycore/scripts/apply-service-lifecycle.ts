/** Explicit installation only. Never changes existing appointments or runs a sweep. */
import { readFileSync } from "node:fs";
import { neon } from "@neondatabase/serverless";
import { config } from "dotenv";
import { preservingBusinessRecords } from "./business-preservation";
config({ path: ".env.local", quiet: true });
try {
  if (!process.argv.includes("--apply") || !process.env.DATABASE_URL)
    throw new Error("Explicit apply and database configuration required.");
  const sql = neon(process.env.DATABASE_URL);
  const statements = (file: string) =>
    readFileSync(new URL("../db/migrations/" + file, import.meta.url), "utf8")
      .split("--> statement-breakpoint")
      .map((s) => s.trim())
      .filter(Boolean);
  // New enum values must commit before any function/trigger uses them.
  await sql.transaction(
    statements("0012_service_statuses.sql").map((s) => sql.query(s)),
  );
  const result = await sql.transaction(
    preservingBusinessRecords(statements("0013_service_lifecycle.sql"), [
      "salon_services",
      "preset_services",
      "appointment_services",
      "stylist_work_settings",
      "client_consultations",
      "client_reference_images",
      "client_consultation_results",
      "client_consultation_jobs",
      "appointment_payments",
    ]).map((s) => sql.query(s)),
  );
  console.log(
    JSON.stringify({
      applied: true,
      existingRecordsPreserved: true,
      preservedRecordCounts: result.at(-1),
      automation:
        "Active from policy installation; earlier overdue appointments excluded",
    }),
  );
} catch {
  console.error(
    "Service lifecycle installation failed. Schema transaction rolled back; enum additions, if committed, are harmless and safe to retry.",
  );
  process.exitCode = 1;
}
