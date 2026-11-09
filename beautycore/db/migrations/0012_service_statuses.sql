ALTER TYPE appointment_status ADD VALUE IF NOT EXISTS 'in_progress';
--> statement-breakpoint
ALTER TYPE appointment_status ADD VALUE IF NOT EXISTS 'no_show';
