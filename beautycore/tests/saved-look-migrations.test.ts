import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { PGlite } from "@electric-sql/pglite";
import { applySavedLookMigrations } from "../scripts/saved-look-migrations";

async function fixture() {
  const pg = new PGlite();
  await pg.exec(readFileSync("tests/fixtures/business-base.sql", "utf8"));
  await pg.exec(`INSERT INTO users(id,email,name,password_hash) VALUES('11111111-1111-4111-8111-111111111111','release@example.invalid','Release fixture','not-a-login');
    INSERT INTO ai_generations(client_id,style_type,source_image_url,prompt_text,generated_image_url) VALUES('11111111-1111-4111-8111-111111111111','hair','fixture-source','fixture-prompt','fixture-result');`);
  return pg;
}

test("release runner uses single-statement queries, commits enum before use and preserves legacy rows on repeat", async () => {
  const pg = await fixture();
  try {
    // The HTTP query protocol rejects a whole multi-command file.
    await assert.rejects(
      pg.query(readFileSync("db/migrations/0002_saved_looks.sql", "utf8")),
    );
    const transaction = (statements: string[]) =>
      pg.transaction(async (tx) => {
        for (const statement of statements) await tx.query(statement);
      });
    await applySavedLookMigrations(transaction);
    const result = await pg.query<{ outcome: string }>(
      `SELECT * FROM beautycore_save_look('11111111-1111-4111-8111-111111111111','makeup','natural','Natural','fixture-preview',repeat('a',64),1,'manual',20,134217728)`,
    );
    assert.equal(result.rows[0].outcome, "created");
    await applySavedLookMigrations(transaction);
    const legacy = await pg.query(
      `SELECT source_image_url,prompt_text,generated_image_url,source_kind,result_hash FROM ai_generations WHERE style_type='hair'`,
    );
    assert.deepEqual(legacy.rows, [
      {
        source_image_url: "fixture-source",
        prompt_text: "fixture-prompt",
        generated_image_url: "fixture-result",
        source_kind: "legacy",
        result_hash: null,
      },
    ]);
    assert.equal(
      (await pg.query<{ n: number }>("SELECT count(*)::int AS n FROM ai_generations")).rows[0]
        .n,
      2,
    );
  } finally {
    await pg.close();
  }
});

test("a failed schema batch rolls back completely and does not run the next migration", async () => {
  const pg = await fixture();
  try {
    let transactions = 0;
    await assert.rejects(
      applySavedLookMigrations((statements) =>
        pg.transaction(async (tx) => {
          transactions++;
          for (const statement of statements) await tx.query(statement);
          await tx.query("SELECT missing_release_fixture_column");
        }),
      ),
    );
    assert.equal(transactions, 1);
    const result = await pg.query(
      `SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='ai_generations' AND column_name='saved_at') AS added,EXISTS(SELECT 1 FROM pg_enum e JOIN pg_type t ON t.oid=e.enumtypid WHERE t.typname='style_type' AND e.enumlabel='makeup') AS makeup`,
    );
    assert.deepEqual(result.rows, [{ added: false, makeup: false }]);
    assert.equal(
      (await pg.query<{ n: number }>("SELECT count(*)::int AS n FROM ai_generations")).rows[0]
        .n,
      1,
    );
  } finally {
    await pg.close();
  }
});
