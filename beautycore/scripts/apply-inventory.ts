/** Explicit, preservation-checked inventory upgrade. No products are seeded or historical services consumed. */
import { readFileSync } from "node:fs";
import { neon } from "@neondatabase/serverless";
import { config } from "dotenv";
import { preservingBusinessRecords } from "./business-preservation";
config({ path: ".env.local", quiet: true });
try {
  if (!process.argv.includes("--apply") || !process.env.DATABASE_URL)
    throw new Error("Explicit apply and database configuration required.");
  const sql = neon(process.env.DATABASE_URL);
  const statements = readFileSync(
    new URL("../db/migrations/0014_service_inventory.sql", import.meta.url),
    "utf8",
  )
    .split("--> statement-breakpoint")
    .map((s) => s.trim())
    .filter(Boolean);
  const result = await sql.transaction(
    preservingBusinessRecords(statements, [
      "salon_services",
      "preset_services",
      "appointment_services",
      "stylist_work_settings",
      "client_consultations",
      "client_reference_images",
      "client_consultation_results",
      "client_consultation_jobs",
      "appointment_payments",
      "appointment_lifecycle_policy",
      "appointment_service_tracking",
      "appointment_activity",
    ]).map((s) => sql.query(s)),
  );
  console.log(
    JSON.stringify({
      applied: true,
      existingRecordsPreserved: true,
      preservedRecordCounts: result.at(-1),
      productSeeding: false,
      historicalDeductions: false,
      quantityStorage: "Exact numeric, up to three fractional digits",
    }),
  );
} catch (error) {
  const e = error as { code?: string; message?: string };
  console.error(
    JSON.stringify({
      code: e.code,
      message: e.message?.replace(/postgres(?:ql)?:\/\/[^\s]+/g, "[redacted]"),
    }),
  );
  console.error("Inventory upgrade failed; the transaction was rolled back.");
  process.exitCode = 1;
}
