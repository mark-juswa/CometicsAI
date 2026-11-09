# Consultation History search and date filters

Status: CONFIRMED user request, 9 November 2026. Add searchable, date-filtered private history without changing protected AI resources or the generation pipeline.

The archive list supports a keyword, consultation-created-from date, consulted-through date and Hair/Nails/Makeup feature. Match keywords case-insensitively against archived message content, preferences, generated look names, photo filenames and feature names. Treat user text literally, including percent signs and underscores, and bind query parameters. Apply all selected filters together before pagination. Limit keywords to 120 characters, reject invalid dates/features/pages and reject reversed date ranges. An omitted filter imposes no restriction.

Dates use whole inclusive Philippine days: start at midnight Asia/Manila and stop before the next day after the through date. Preserve owner restrictions across the consultation, photo and generated-result queries. Keep true filtered totals even when a later page contains no records. Use existing indexes/tables; no migration, historical backfill, model request or record mutation is needed.

Provide labeled responsive controls, Apply/Clear actions, loading feedback, no-match guidance, failure/retry feedback and filtered counts. Apply/Clear returns to page one. Preserve applied filters and page in the URL, pagination and detail/back links, and restore them on reload. Ignore/cancel obsolete responses. Existing record detail, downloads and photo reuse remain intact.

Verify date boundaries, literal keyword sources, private ownership, validation, combined filtering, pagination/counts, apply/clear, URL restoration and retry behavior against the actual query and component with isolated fixture records. Validate the production build and existing role-guarded HTTP routes without modifying live data.
