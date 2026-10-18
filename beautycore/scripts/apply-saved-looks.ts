/** Explicit migration utility. Default/check mode is read-only. Never seeds users. */
import { applySavedLookMigrations } from "./saved-look-migrations";
import { neon } from "@neondatabase/serverless";
import { config } from "dotenv";
config({ path: ".env.local", quiet: true });
try {
  if (!process.env.DATABASE_URL) throw new Error("Missing configuration");
  const query = neon(process.env.DATABASE_URL);
  if (process.argv.includes("--apply")) {
    await applySavedLookMigrations((statements) =>
      query.transaction(statements.map((statement) => query.query(statement))),
    );
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
  const applied =
    required.every((name) => columns.some((row) => row.column_name === name)) &&
    functions[0].present &&
    fk[0].present;
  const bytes = await query.query(
    "SELECT coalesce(sum(octet_length(coalesce(generated_image_url,''))+octet_length(coalesce(source_image_url,''))),0)::bigint AS bytes FROM ai_generations",
  );
  console.log(
    JSON.stringify({
      applied,
      mode: process.argv.includes("--apply")
        ? "explicit-apply"
        : "read-only-check",
      existingImageTextBytes: Number(bytes[0].bytes),
      savedLooksEnabled: "Enable only after capacity review and deployment.",
    }),
  );
  if (process.argv.includes("--apply") && !applied) process.exitCode = 1;
} catch {
  console.error(
    "Saved-look migration/check failed. Private database errors and credentials suppressed.",
  );
  process.exitCode = 1;
}
