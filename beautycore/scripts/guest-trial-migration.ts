import { readFileSync } from "node:fs";
export const guestTrialStatements = () =>
  readFileSync(
    new URL(
      "../db/migrations/0006_guest_consultation_trial.sql",
      import.meta.url,
    ),
    "utf8",
  )
    .split("--> statement-breakpoint")
    .map((s) => s.trim())
    .filter(Boolean);
