/** Explicit schema-only scheduling upgrade; never creates or rewrites appointments. */
import { readFileSync } from "node:fs";
import { neon } from "@neondatabase/serverless";
import { config } from "dotenv";
import { preservingBusinessRecords } from "./business-preservation";
config({ path: ".env.local", quiet: true });
try {
  if (!process.argv.includes("--apply"))
    throw new Error("Pass --apply explicitly.");
  if (!process.env.DATABASE_URL)
    throw new Error("Missing database configuration.");
  const sql = neon(process.env.DATABASE_URL);
  const statements = readFileSync(
    new URL(
      "../db/migrations/0011_booking_services.sql",
      import.meta.url,
    ),
    "utf8",
  )
    .split("--> statement-breakpoint")
    .map((s) => s.trim())
    .filter(Boolean);
  const result = await sql.transaction(
    preservingBusinessRecords(statements).map((s) => sql.query(s)),
  );
  console.log(
    JSON.stringify({
      applied: true,
      durationMinutes: 90,
      existingRecordsPreserved: true,
      preservedRecordCounts: result.at(-1),
    }),
  );
} catch (error) {
  const e=error as {code?:string;message?:string};console.error(JSON.stringify({code:e.code,message:e.message?.replace(/postgres(?:ql)?:\/\/[^\s]+/g,"[redacted]")}));
  console.error(
    "Scheduling upgrade failed; transaction rolled back. Verify database configuration and earlier migrations.",
  );
  process.exitCode = 1;
}
