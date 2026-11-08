-- Additive customer archive and actual payment receipts. No legacy rows are removed.
CREATE TABLE IF NOT EXISTS client_consultations (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), client_id uuid NOT NULL REFERENCES users(id),
 source_key varchar(64) NOT NULL, feature varchar(20) NOT NULL CHECK(feature IN ('hairstyle','nails','makeup')),
 snapshot jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(client_id,source_key), UNIQUE(id,client_id)
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS client_reference_images (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), client_id uuid NOT NULL REFERENCES users(id), consultation_id uuid NOT NULL,
 image_data text NOT NULL, image_hash varchar(64) NOT NULL, image_bytes integer NOT NULL CHECK(image_bytes BETWEEN 1 AND 8388608),
 content_type text NOT NULL CHECK(content_type IN ('image/png','image/jpeg')), width integer NOT NULL, height integer NOT NULL,
 filename varchar(255) NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(consultation_id,client_id) REFERENCES client_consultations(id,client_id), UNIQUE(consultation_id,image_hash)
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS client_reference_images_owner_idx ON client_reference_images(client_id,created_at DESC,id);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS client_consultation_results (
 consultation_id uuid NOT NULL, client_id uuid NOT NULL, recommendation_id varchar(80) NOT NULL, generation_id uuid NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(consultation_id,recommendation_id,generation_id),
 FOREIGN KEY(consultation_id,client_id) REFERENCES client_consultations(id,client_id),
 FOREIGN KEY(generation_id,client_id) REFERENCES ai_generations(id,client_id)
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS client_consultation_jobs (
 job_id uuid PRIMARY KEY, client_id uuid NOT NULL, consultation_id uuid NOT NULL, recommendation_id varchar(80) NOT NULL,
 FOREIGN KEY(consultation_id,client_id) REFERENCES client_consultations(id,client_id)
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS client_consultations_owner_idx ON client_consultations(client_id,created_at DESC,id);
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_private_image_bytes() RETURNS bigint LANGUAGE sql STABLE AS $$
 SELECT (SELECT coalesce(sum(octet_length(coalesce(generated_image_url,''))+octet_length(coalesce(source_image_url,''))),0) FROM ai_generations)
 +(SELECT coalesce(sum(octet_length(image_data)),0) FROM client_reference_images);
$$;
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_store_reference(p_owner uuid,p_session uuid,p_image text,p_hash text,p_bytes integer,p_mime text,p_width integer,p_height integer,p_name text,p_budget bigint)
RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE found_id uuid;
BEGIN
 PERFORM pg_advisory_xact_lock(181477,1017);
 IF NOT EXISTS(SELECT 1 FROM client_consultations WHERE id=p_session AND client_id=p_owner) THEN RAISE EXCEPTION 'invalid_owner'; END IF;
 SELECT id INTO found_id FROM client_reference_images WHERE consultation_id=p_session AND image_hash=p_hash;
 IF found_id IS NOT NULL THEN RETURN found_id; END IF;
 IF p_budget NOT BETWEEN 1048576 AND 268435456 OR beautycore_private_image_bytes()+octet_length(p_image)>p_budget THEN RAISE EXCEPTION 'image_storage_full' USING ERRCODE='54000'; END IF;
 INSERT INTO client_reference_images(client_id,consultation_id,image_data,image_hash,image_bytes,content_type,width,height,filename)
 VALUES(p_owner,p_session,p_image,p_hash,p_bytes,p_mime,p_width,p_height,left(p_name,255)) RETURNING id INTO found_id;
 RETURN found_id;
END $$;
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_archive_result(p_owner uuid,p_session uuid,p_recommendation text,p_type text,p_style text,p_name text,p_image text,p_hash text,p_bytes integer,p_details jsonb,p_budget bigint)
RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE found_id uuid;
BEGIN
 PERFORM pg_advisory_xact_lock(181477,1017);
 IF NOT EXISTS(SELECT 1 FROM client_consultations WHERE id=p_session AND client_id=p_owner) THEN RAISE EXCEPTION 'invalid_owner'; END IF;
 SELECT id INTO found_id FROM ai_generations WHERE client_id=p_owner AND style_type::text=p_type AND style_id=p_style AND result_hash=p_hash;
 IF found_id IS NULL THEN
  IF p_budget NOT BETWEEN 1048576 AND 268435456 OR beautycore_private_image_bytes()+octet_length(p_image)>p_budget THEN RAISE EXCEPTION 'image_storage_full' USING ERRCODE='54000'; END IF;
  INSERT INTO ai_generations(client_id,style_type,style_id,style_name,generated_image_url,result_hash,image_bytes,source_kind,look_details)
  VALUES(p_owner,p_type::style_type,p_style,p_name,p_image,p_hash,p_bytes,'consultation',p_details) RETURNING id INTO found_id;
 END IF;
 INSERT INTO client_consultation_results(consultation_id,client_id,recommendation_id,generation_id)
 VALUES(p_session,p_owner,p_recommendation,found_id) ON CONFLICT DO NOTHING;
 RETURN found_id;
END $$;
--> statement-breakpoint
-- Retain existing save limits and include uploaded references in the shared storage budget.
CREATE OR REPLACE FUNCTION beautycore_save_look(p_owner uuid,p_type text,p_style text,p_name text,p_image text,p_hash text,p_bytes integer,p_source text,p_limit integer,p_budget bigint)
RETURNS TABLE(look_id uuid,outcome text) LANGUAGE plpgsql AS $$
DECLARE found_id uuid; was_saved timestamptz;
BEGIN
 PERFORM pg_advisory_xact_lock(181477,1017);
 IF p_type NOT IN ('hair','nail','makeup') OR p_source NOT IN ('manual','consultation') OR p_limit NOT BETWEEN 1 AND 100 OR p_budget NOT BETWEEN 1048576 AND 268435456 THEN RAISE EXCEPTION 'Invalid saved look settings'; END IF;
 SELECT id,saved_at INTO found_id,was_saved FROM ai_generations WHERE client_id=p_owner AND style_type=p_type::style_type AND style_id=p_style AND result_hash=p_hash;
 IF found_id IS NOT NULL AND was_saved IS NOT NULL THEN RETURN QUERY SELECT found_id,'existing'::text;RETURN;END IF;
 IF (SELECT count(*) FROM ai_generations WHERE client_id=p_owner AND saved_at IS NOT NULL)>=p_limit THEN RETURN QUERY SELECT NULL::uuid,'client_limit'::text;RETURN;END IF;
 IF found_id IS NOT NULL THEN UPDATE ai_generations SET saved_at=now() WHERE id=found_id;RETURN QUERY SELECT found_id,'restored'::text;RETURN;END IF;
 IF beautycore_private_image_bytes()+octet_length(p_image)>p_budget THEN RETURN QUERY SELECT NULL::uuid,'storage_limit'::text;RETURN;END IF;
 INSERT INTO ai_generations(client_id,style_type,style_id,style_name,generated_image_url,result_hash,image_bytes,source_kind,saved_at)
 VALUES(p_owner,p_type::style_type,p_style,p_name,p_image,p_hash,p_bytes,p_source,now()) RETURNING id INTO found_id;
 RETURN QUERY SELECT found_id,'created'::text;
END $$;
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS appointment_payments (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), appointment_id uuid NOT NULL REFERENCES appointments(id) ON DELETE RESTRICT,
 amount integer NOT NULL CHECK(amount BETWEEN 1 AND 100000000), method varchar(20) NOT NULL CHECK(method IN ('cash','card','bank','other')),
 reference varchar(160), request_id uuid NOT NULL UNIQUE, recorded_by uuid NOT NULL REFERENCES users(id), created_at timestamptz NOT NULL DEFAULT now()
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS appointment_payments_appointment_idx ON appointment_payments(appointment_id,created_at);
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_record_payment(p_client uuid,p_appointment uuid,p_actor uuid,p_amount integer,p_method text,p_reference text,p_request uuid)
RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE a appointments%ROWTYPE; paid bigint; payment_id uuid;
BEGIN
 IF NOT EXISTS(SELECT 1 FROM users WHERE id=p_actor AND role='admin' AND is_active) THEN RAISE EXCEPTION 'admin_required'; END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended(p_request::text,23));
 SELECT id INTO payment_id FROM appointment_payments WHERE request_id=p_request AND appointment_id=p_appointment AND amount=p_amount AND method=p_method AND coalesce(reference,'')=coalesce(nullif(trim(p_reference),''),'');
 IF payment_id IS NOT NULL THEN RETURN payment_id; END IF;
 SELECT * INTO a FROM appointments WHERE id=p_appointment AND client_id=p_client FOR UPDATE;
 IF NOT FOUND OR a.status='cancelled' OR a.total_price IS NULL THEN RAISE EXCEPTION 'payment_not_allowed' USING ERRCODE='23514'; END IF;
 SELECT coalesce(sum(amount),0) INTO paid FROM appointment_payments WHERE appointment_id=p_appointment;
 IF p_amount IS NULL OR p_amount<1 OR p_amount>100000000 OR p_amount+paid>a.total_price THEN RAISE EXCEPTION 'invalid_payment_amount' USING ERRCODE='23514'; END IF;
 INSERT INTO appointment_payments(appointment_id,amount,method,reference,request_id,recorded_by) VALUES(p_appointment,p_amount,p_method,nullif(trim(p_reference),''),p_request,p_actor) RETURNING id INTO payment_id;
 RETURN payment_id;
END $$;
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_preserve_payment_total() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE paid bigint;
BEGIN
 SELECT coalesce(sum(amount),0) INTO paid FROM appointment_payments WHERE appointment_id=NEW.id;
 IF paid>0 AND (NEW.total_price IS NULL OR NEW.total_price<paid) THEN RAISE EXCEPTION 'price_below_recorded_payments' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
--> statement-breakpoint
DROP TRIGGER IF EXISTS appointment_preserve_payment_total ON appointments;
--> statement-breakpoint
CREATE TRIGGER appointment_preserve_payment_total BEFORE UPDATE OF total_price ON appointments FOR EACH ROW EXECUTE FUNCTION beautycore_preserve_payment_total();
