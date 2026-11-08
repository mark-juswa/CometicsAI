/** Explicit migration utility. Default/check mode is read-only. Never seeds users. */
import { applySavedLookMigrations } from "./saved-look-migrations";
import { preservingBusinessRecords } from "./business-preservation";
import { neon } from "@neondatabase/serverless";
import { config } from "dotenv";
config({ path: ".env.local", quiet: true });
try {
  if (!process.env.DATABASE_URL) throw new Error("Missing configuration");
  const query = neon(process.env.DATABASE_URL);
  let recordsPreserved: { name: string; count: unknown }[] | undefined;
  if (process.argv.includes("--apply")) {
    const additionalOnly = process.argv.includes("--additional-only");
    if (additionalOnly) {
      const prerequisite = await query.query(
        "SELECT to_regprocedure('beautycore_inventory_move(uuid,uuid,text,integer,text)') IS NOT NULL AS present",
      );
      if (!prerequisite[0].present)
        throw new Error("Apply the earlier business controls first.");
    }
    await applySavedLookMigrations(async (statements) => {
      if (!additionalOnly)
        return query.transaction(
          statements.map((statement) => query.query(statement)),
        );
      const results = await query.transaction(
        preservingBusinessRecords(statements).map((statement) =>
          query.query(statement),
        ),
      );
      recordsPreserved = results.at(-1) as { name: string; count: unknown }[];
      return results;
    }, additionalOnly);
  }
  const columns = await query.query(
    "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='ai_generations'",
  );
  const required = [
    "style_id",
    "style_name",
    "saved_at",
    "result_hash",
    "image_bytes",
    "source_kind",
    "look_details",
  ];
  const functions = await query.query(
    "SELECT EXISTS(SELECT 1 FROM pg_proc WHERE proname='beautycore_save_look_with_details') AS present",
  );
  const fk = await query.query(
    "SELECT EXISTS(SELECT 1 FROM pg_constraint WHERE conname='appointments_look_owner_fk' AND conrelid='appointments'::regclass) AS present",
  );
  const workflow = await query.query(`SELECT
    to_regprocedure('beautycore_complete_appointment(uuid,uuid,text,jsonb)') IS NOT NULL
    AND to_regprocedure('beautycore_review_appointment(uuid,uuid,integer,text)') IS NOT NULL
    AND EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='appointments' AND column_name='completed_at')
    AND EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='appointments' AND column_name='completed_by')
    AND EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='inventory' AND column_name='brand')
    AND to_regclass('appointment_reviews') IS NOT NULL
    AND to_regclass('appointment_product_usage') IS NOT NULL AS present`);
  const applied =
    required.every((name) => columns.some((row) => row.column_name === name)) &&
    functions[0].present &&
    fk[0].present &&
    workflow[0].present;
  const businessControls = await query.query(`SELECT
    EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='users' AND column_name='is_active')
    AND EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='users' AND column_name='phone')
    AND EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='appointments' AND column_name='duration_minutes')
    AND to_regclass('stylist_specialties') IS NOT NULL AND to_regclass('inventory_transactions') IS NOT NULL
    AND to_regprocedure('beautycore_create_appointment(uuid,uuid,text,text,timestamp with time zone,integer,integer,text,uuid)') IS NOT NULL
    AND to_regprocedure('beautycore_inventory_move(uuid,uuid,text,integer,text)') IS NOT NULL AS present`);
  const bytes = process.argv.includes("--schema-only")
    ? []
    : await query.query(
        "SELECT coalesce(sum(octet_length(coalesce(generated_image_url,''))+octet_length(coalesce(source_image_url,''))),0)::bigint AS bytes FROM ai_generations",
      );
  const additions = await query.query(`SELECT
    to_regclass('stylist_work_settings') IS NOT NULL AND to_regprocedure('beautycore_work_available(uuid,timestamp with time zone,integer)') IS NOT NULL AS availability,
    to_regclass('client_consultations') IS NOT NULL AND to_regclass('client_reference_images') IS NOT NULL
    AND to_regclass('client_consultation_results') IS NOT NULL AND to_regclass('client_consultation_jobs') IS NOT NULL
    AND to_regprocedure('beautycore_archive_result(uuid,uuid,text,text,text,text,text,text,integer,jsonb,bigint)') IS NOT NULL AS history,
    to_regclass('appointment_payments') IS NOT NULL AND to_regprocedure('beautycore_record_payment(uuid,uuid,uuid,integer,text,text,uuid)') IS NOT NULL AS payments`);
  console.log(
    JSON.stringify({
      applied,
      workflowApplied: workflow[0].present,
      businessControlsApplied: businessControls[0].present,
      workAvailabilityApplied: additions[0].availability,
      customerHistoryApplied: additions[0].history,
      paymentsApplied: additions[0].payments,
      existingRecordsPreserved: recordsPreserved ? true : undefined,
      preservedRecordCounts: recordsPreserved,
      mode: process.argv.includes("--apply")
        ? "explicit-apply"
        : "read-only-check",
      existingImageTextBytes: bytes.length ? Number(bytes[0].bytes) : undefined,
      verificationBasis: recordsPreserved
        ? "Schema metadata and before/after record fingerprints; no record contents output"
        : process.argv.includes("--schema-only")
          ? "schema metadata only; no application records read"
          : "schema and storage capacity",
      savedLooksEnabled: process.env.SAVED_LOOKS_ENABLED === "true",
    }),
  );
  if (
    process.argv.includes("--apply") &&
    (!applied ||
      !businessControls[0].present ||
      !additions[0].availability ||
      !additions[0].history ||
      !additions[0].payments)
  )
    process.exitCode = 1;
} catch {
  console.error(
    "Saved-look migration/check failed. Private database errors and credentials suppressed.",
  );
  process.exitCode = 1;
}
