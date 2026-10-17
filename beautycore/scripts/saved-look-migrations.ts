import { readFileSync } from "node:fs";

// Explicit boundaries preserve PL/pgSQL bodies containing internal semicolons.
// One transaction per file commits the enum before the next file uses it.
export async function applySavedLookMigrations(
  transaction: (statements: string[]) => Promise<unknown>,
) {
  for (const name of [
    "0002_saved_looks.sql",
    "0003_saved_look_admission.sql",
  ]) {
    const statements = readFileSync(
      new URL("../db/migrations/" + name, import.meta.url),
      "utf8",
    )
      .split("--> statement-breakpoint")
      .map((statement) => statement.trim())
      .filter(Boolean);
    await transaction(statements);
  }
}
