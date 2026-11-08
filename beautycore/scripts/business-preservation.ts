/** Protect existing application records while installing additive schema changes. */
export function preservingBusinessRecords(statements: string[]): string[] {
  const tables = [
    "users",
    "client_profiles",
    "appointments",
    "ai_generations",
    "inventory",
    "stylist_specialties",
    "inventory_transactions",
    "appointment_reviews",
    "appointment_product_usage",
  ];
  const snapshot = tables
    .map(
      (name) =>
        `SELECT '${name}' AS name,count(*)::bigint AS count,md5(coalesce(string_agg(md5(to_jsonb(t)::text),'' ORDER BY md5(to_jsonb(t)::text)),'')) AS fingerprint FROM ${name} t`,
    )
    .join(" UNION ALL ");
  return [
    `LOCK TABLE ${tables.join(",")} IN SHARE MODE`,
    `CREATE TEMP TABLE beautycore_migration_integrity ON COMMIT DROP AS ${snapshot}`,
    ...statements,
    `DO $preserve$ BEGIN IF EXISTS(SELECT * FROM beautycore_migration_integrity EXCEPT SELECT * FROM (${snapshot}) observed) OR EXISTS(SELECT * FROM (${snapshot}) observed EXCEPT SELECT * FROM beautycore_migration_integrity) THEN RAISE EXCEPTION 'Existing records changed; rolling back migration'; END IF; END $preserve$`,
    "SELECT name,count FROM beautycore_migration_integrity ORDER BY name",
  ];
}
