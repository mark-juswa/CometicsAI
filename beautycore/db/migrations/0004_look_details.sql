-- Local/disposable tests only until this additive migration is separately approved.
ALTER TABLE ai_generations ADD COLUMN IF NOT EXISTS look_details jsonb;
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_saved_content_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF OLD.result_hash IS NOT NULL AND (NEW.generated_image_url,NEW.client_id,NEW.style_type,NEW.style_id,NEW.style_name,NEW.result_hash,NEW.image_bytes,NEW.source_kind,NEW.look_details)
 IS DISTINCT FROM (OLD.generated_image_url,OLD.client_id,OLD.style_type,OLD.style_id,OLD.style_name,OLD.result_hash,OLD.image_bytes,OLD.source_kind,OLD.look_details) THEN
 RAISE EXCEPTION 'Saved look content is immutable';
 END IF; RETURN NEW;
END $$;
--> statement-breakpoint
-- One function call is one atomic transaction on Neon's HTTP driver.
-- Lock precedes fresh PL/pgSQL SELECT snapshots; concurrent saves cannot bypass quotas.
CREATE OR REPLACE FUNCTION beautycore_save_look_with_details(p_owner uuid,p_type text,p_style text,p_name text,p_image text,p_hash text,p_bytes integer,p_source text,p_limit integer,p_budget bigint,p_details jsonb)
RETURNS TABLE(look_id uuid,outcome text) LANGUAGE plpgsql AS $$
DECLARE found_id uuid; was_saved timestamptz; used_bytes bigint;
BEGIN
 PERFORM pg_advisory_xact_lock(181477,1017);
 IF p_type NOT IN ('hair','nail','makeup') OR p_source NOT IN ('manual','consultation') OR p_limit NOT BETWEEN 1 AND 100 OR p_budget NOT BETWEEN 1048576 AND 268435456 THEN
 RAISE EXCEPTION 'Invalid saved look settings'; END IF;
 IF p_details IS NOT NULL AND (jsonb_typeof(p_details) <> 'object' OR p_details->>'version' IS DISTINCT FROM '1' OR octet_length(p_details::text)>16384) THEN RAISE EXCEPTION 'Invalid look details'; END IF;
 SELECT id,saved_at INTO found_id,was_saved FROM ai_generations WHERE client_id=p_owner AND style_type=p_type::style_type AND style_id=p_style AND result_hash=p_hash;
 IF found_id IS NOT NULL AND was_saved IS NOT NULL THEN RETURN QUERY SELECT found_id,'existing'::text;RETURN;END IF;
 IF (SELECT count(*) FROM ai_generations WHERE client_id=p_owner AND saved_at IS NOT NULL)>=p_limit THEN RETURN QUERY SELECT NULL::uuid,'client_limit'::text;RETURN;END IF;
 IF found_id IS NOT NULL THEN UPDATE ai_generations SET saved_at=now() WHERE id=found_id;RETURN QUERY SELECT found_id,'restored'::text;RETURN;END IF;
 SELECT coalesce(sum(octet_length(coalesce(generated_image_url,''))+octet_length(coalesce(source_image_url,''))),0) INTO used_bytes FROM ai_generations;
 IF used_bytes+octet_length(p_image)>p_budget THEN RETURN QUERY SELECT NULL::uuid,'storage_limit'::text;RETURN;END IF;
 INSERT INTO ai_generations(client_id,style_type,style_id,style_name,generated_image_url,result_hash,image_bytes,source_kind,saved_at,look_details)
 VALUES(p_owner,p_type::style_type,p_style,p_name,p_image,p_hash,p_bytes,p_source,now(),p_details) RETURNING id INTO found_id;
 RETURN QUERY SELECT found_id,'created'::text;
END $$;
