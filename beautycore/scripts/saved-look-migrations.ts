import { readFileSync } from "node:fs";

// Explicit boundaries preserve PL/pgSQL bodies containing internal semicolons.
// Commit enum additions first. Install all scheduling/archive controls atomically.
export async function applySavedLookMigrations(
  transaction: (statements: string[]) => Promise<unknown>,
  additionalOnly = false,
) {
  const groups = [
    ["0002_saved_looks.sql"],
    ["0003_saved_look_admission.sql"],
    ["0004_look_details.sql"],
    ["0005_service_completion.sql"],
    [
      "0007_business_controls.sql",
      "0008_work_availability.sql",
      "0009_customer_history.sql",
    ],
  ];
  for (const names of additionalOnly
    ? [["0008_work_availability.sql", "0009_customer_history.sql"]]
    : groups) {
    const statements = names.flatMap((name) =>
      readFileSync(new URL("../db/migrations/" + name, import.meta.url), "utf8")
        .split("--> statement-breakpoint")
        .map((statement) => statement.trim())
        .filter(Boolean),
    );
    await transaction(statements);
  }
}
