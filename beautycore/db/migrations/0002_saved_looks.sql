-- Apply this migration and commit before 0003 uses the new enum value.
ALTER TYPE style_type ADD VALUE IF NOT EXISTS 'makeup';
ALTER TABLE ai_generations ALTER COLUMN source_image_url DROP NOT NULL;
ALTER TABLE ai_generations ALTER COLUMN prompt_text DROP NOT NULL;
ALTER TABLE ai_generations ADD COLUMN IF NOT EXISTS style_id varchar(80),
 ADD COLUMN IF NOT EXISTS style_name varchar(255), ADD COLUMN IF NOT EXISTS saved_at timestamptz,
 ADD COLUMN IF NOT EXISTS result_hash varchar(64), ADD COLUMN IF NOT EXISTS image_bytes integer,
 ADD COLUMN IF NOT EXISTS source_kind varchar(20) NOT NULL DEFAULT 'legacy';
CREATE UNIQUE INDEX IF NOT EXISTS ai_generations_id_owner_idx ON ai_generations(id,client_id);
CREATE UNIQUE INDEX IF NOT EXISTS ai_generations_saved_dedup_idx ON ai_generations(client_id,style_type,style_id,result_hash);
CREATE INDEX IF NOT EXISTS ai_generations_client_saved_idx ON ai_generations(client_id,saved_at DESC,id);
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS ai_generation_id uuid;
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conname='appointments_look_owner_fk' AND conrelid='appointments'::regclass) THEN
 ALTER TABLE appointments ADD CONSTRAINT appointments_look_owner_fk FOREIGN KEY(ai_generation_id,client_id) REFERENCES ai_generations(id,client_id);
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conname='saved_look_integrity' AND conrelid='ai_generations'::regclass) THEN
 ALTER TABLE ai_generations ADD CONSTRAINT saved_look_integrity CHECK(result_hash IS NULL OR
 (result_hash ~ '^[0-9a-f]{64}$' AND style_id IS NOT NULL AND style_name IS NOT NULL
 AND generated_image_url IS NOT NULL AND image_bytes IS NOT NULL AND image_bytes BETWEEN 1 AND 8388608 AND source_kind IN ('manual','consultation')));
 END IF;
END $$;
CREATE INDEX IF NOT EXISTS appointments_stylist_date_idx ON appointments(stylist_id,appointment_date);
CREATE INDEX IF NOT EXISTS appointments_date_status_idx ON appointments(appointment_date,status);
CREATE INDEX IF NOT EXISTS appointments_look_idx ON appointments(ai_generation_id);
CREATE OR REPLACE FUNCTION beautycore_saved_content_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF OLD.result_hash IS NOT NULL AND (NEW.generated_image_url,NEW.client_id,NEW.style_type,NEW.style_id,NEW.style_name,NEW.result_hash,NEW.image_bytes,NEW.source_kind)
 IS DISTINCT FROM (OLD.generated_image_url,OLD.client_id,OLD.style_type,OLD.style_id,OLD.style_name,OLD.result_hash,OLD.image_bytes,OLD.source_kind) THEN
 RAISE EXCEPTION 'Saved look content is immutable';
 END IF; RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS beautycore_saved_content_guard ON ai_generations;
CREATE TRIGGER beautycore_saved_content_guard BEFORE UPDATE ON ai_generations FOR EACH ROW EXECUTE FUNCTION beautycore_saved_content_immutable();
