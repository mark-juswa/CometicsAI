CREATE TABLE IF NOT EXISTS salon_services(id text PRIMARY KEY,name text NOT NULL,service_type text NOT NULL,group_id text NOT NULL,group_label text NOT NULL,price text NOT NULL,active boolean NOT NULL DEFAULT true,UNIQUE(name,service_type));
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS preset_services(feature text NOT NULL,style_id text NOT NULL,service_id text NOT NULL REFERENCES salon_services(id),PRIMARY KEY(feature,style_id));
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS appointment_services(appointment_id uuid PRIMARY KEY REFERENCES appointments(id) ON DELETE CASCADE,service_id text NOT NULL REFERENCES salon_services(id));
--> statement-breakpoint
INSERT INTO salon_services(id,name,service_type,group_id,group_label,price) VALUES ('svc_beb38a0966fc7b0a2fc4aa1e','Classic Head Spa (60 min)','treatment','japanese-head-spa','Japanese Head Spa','₱850'),('svc_57dff76d20e59e2e44c6ced4','Deep Cleanse Head Spa (75 min)','treatment','japanese-head-spa','Japanese Head Spa','₱1,100'),('svc_aba7a5b787a35935e3b1f49f','Scalp Detox Treatment','treatment','japanese-head-spa','Japanese Head Spa','₱750'),('svc_019195911457200dd673602d','Premium Head Spa (90 min)','treatment','japanese-head-spa','Japanese Head Spa','₱1,350'),('svc_fbed26ed69deb3f82c7ffa83','Scalp Analysis & Treatment','treatment','japanese-head-spa','Japanese Head Spa','₱950'),('svc_a7bf89bb13e49c83dd233f6a','Hydrating Scalp Ritual','treatment','japanese-head-spa','Japanese Head Spa','₱900'),('svc_e63aabc360f5e9a52d19949c','Aromatherapy Enhancement','treatment','japanese-head-spa','Japanese Head Spa','₱150'),('svc_fa328ccc922943adf6def723','Hot Oil Treatment','treatment','japanese-head-spa','Japanese Head Spa','₱200'),('svc_0e2f18024350fefa89bb0546','Neck & Shoulder Massage','treatment','japanese-head-spa','Japanese Head Spa','₱250'),('svc_5984f08e66438265126cdd18','Hair Mask Treatment','treatment','japanese-head-spa','Japanese Head Spa','₱300'),('svc_052ddae825e8099d6fd10692','Women''s Cut & Blowdry','hair','hair-design','Hair Design','₱350'),('svc_3248d1335d4b18bacbe2cde7','Men''s Cut','hair','hair-design','Hair Design','₱180'),('svc_8ceabb4c403849a29fdc59b3','Children''s Cut (under 12)','hair','hair-design','Hair Design','₱150'),('svc_86ab6d7b8ec9743d47012524','Blowdry & Style','hair','hair-design','Hair Design','₱250'),('svc_5fcca8130253de8bf378e2df','Updo / Special Occasion','hair','hair-design','Hair Design','₱500'),('svc_43fd64b5fefd973b9dd24513','Bridal Hair','hair','hair-design','Hair Design','Mula ₱1,500'),('svc_1b797ffd2c3f4ea191a02460','Keratin Treatment','hair','hair-design','Hair Design','Mula ₱2,500'),('svc_09a7aa23816dee5e094ff99e','Hair Extensions Consult','hair','hair-design','Hair Design','Libre'),('svc_0029016c518982c3f60e79e9','Full Colour','hair','hair-design','Hair Design','Mula ₱800'),('svc_ba36f4a4a3096cbda70777a2','Highlights (Full)','hair','hair-design','Hair Design','Mula ₱1,200'),('svc_08bf923498ce4d4e4f8c1c8c','Highlights (Partial)','hair','hair-design','Hair Design','Mula ₱700'),('svc_cf60579297e335662684b73b','Balayage','hair','hair-design','Hair Design','Mula ₱1,500'),('svc_d5f8c33ff478cfac43c85132','Toner / Gloss','hair','hair-design','Hair Design','₱350'),('svc_0fd0b8d230e5763a22d5f8c6','Colour Correction','hair','hair-design','Hair Design','Konsultasyon'),('svc_6c65e40f98f92db2fb62ee9a','Classic Facial (60 min)','aesthetic','face-laser','Face & Laser','₱600'),('svc_1a43bcbbb278660d8a2b7c03','HydraFacial','aesthetic','face-laser','Face & Laser','₱1,800'),('svc_80d9d31171183b42fba29589','Microdermabrasion','aesthetic','face-laser','Face & Laser','₱1,200'),('svc_73af6ebb98f0161a1ccb393c','Chemical Peel (Light)','aesthetic','face-laser','Face & Laser','₱1,000'),('svc_c07b2caa3cf58c12c9610caa','Chemical Peel (Medium)','aesthetic','face-laser','Face & Laser','₱1,500'),('svc_8c7bbc381c904d9587c1fcee','LED Light Therapy','aesthetic','face-laser','Face & Laser','₱700'),('svc_bbff8783257b9368ac695972','Microneedling','aesthetic','face-laser','Face & Laser','₱2,500'),('svc_23d5fd1beda56aad5bea313c','PRP Facial','aesthetic','face-laser','Face & Laser','₱4,500'),('svc_492aad295b25ed43939c1332','Laser Hair Removal – Face','aesthetic','face-laser','Face & Laser','Mula ₱800'),('svc_1c48565a055537b27d42bcd5','Laser Hair Removal – Body','aesthetic','face-laser','Face & Laser','Mula ₱1,500'),('svc_45275788ff85e19ff83fe3d2','Laser Skin Resurfacing','aesthetic','face-laser','Face & Laser','Mula ₱3,500'),('svc_e86516ec5fe0ff7ba0b70633','IPL Photofacial','aesthetic','face-laser','Face & Laser','₱2,200'),('svc_6c9e9dc03aef5dd7dae964ff','Pigmentation Treatment','aesthetic','face-laser','Face & Laser','Mula ₱1,800'),('svc_0f3951d57d2aa00c29ebbafd','Vascular Treatment','aesthetic','face-laser','Face & Laser','Mula ₱2,000'),('svc_c81a7edbd144065312ebd00a','Classic Manicure','nail','nail-studio','Nail Studio','₱180'),('svc_9d2199ab4e9ba8cb6540aea7','Gel Manicure','nail','nail-studio','Nail Studio','₱350'),('svc_5af37ab26d98ea6b98a226c8','Acrylic Full Set','nail','nail-studio','Nail Studio','₱650'),('svc_5b4328ce0d5ef3047d9e8cb4','Acrylic Infill','nail','nail-studio','Nail Studio','₱450'),('svc_2b821edd45efee03e15cfa88','Gel Extensions','nail','nail-studio','Nail Studio','₱750'),('svc_a1a830ab6f62e654b047033a','Nail Art (per nail)','nail','nail-studio','Nail Studio','Mula ₱50'),('svc_86f8da2679e3c2c2d230e6f2','Gel Removal','nail','nail-studio','Nail Studio','₱150'),('svc_8d3f2268b9dfae1fc30599e9','Nail Repair','nail','nail-studio','Nail Studio','₱80'),('svc_07fc984c3eaa7b785f5181d4','Classic Pedicure','nail','nail-studio','Nail Studio','₱220'),('svc_8ff567828567e028aac69cbd','Gel Pedicure','nail','nail-studio','Nail Studio','₱400'),('svc_89bac704475ffe9a47fdfad1','Spa Pedicure (60 min)','nail','nail-studio','Nail Studio','₱550'),('svc_7163ffce0dfc4b8678c027c5','Luxury Pedicure (75 min)','nail','nail-studio','Nail Studio','₱750'),('svc_047d5736bd8a262b3928f661','Callus Treatment','nail','nail-studio','Nail Studio','₱200'),('svc_7e9867f681934dd4e48f0236','Paraffin Wax Add-On','nail','nail-studio','Nail Studio','₱150'),('svc_6aad5ed58b25d74508410d32','Swedish Massage (60 min)','massage','massage-therapy','Massage Therapy','₱600'),('svc_e7e6ce778c8825082006d128','Swedish Massage (90 min)','massage','massage-therapy','Massage Therapy','₱850'),('svc_0f705934ea207191c617d5d8','Deep Tissue (60 min)','massage','massage-therapy','Massage Therapy','₱700'),('svc_fcb99f492fa3e24f00d01ea6','Deep Tissue (90 min)','massage','massage-therapy','Massage Therapy','₱950'),('svc_3f5c5f80009e0c7c6a088760','Hot Stone Massage (75 min)','massage','massage-therapy','Massage Therapy','₱900'),('svc_e7d635ecd105c77b2e9049ce','Aromatherapy Massage','massage','massage-therapy','Massage Therapy','₱750'),('svc_ad7372f373ff0fc804e33f66','Back, Neck & Shoulder (30 min)','massage','massage-therapy','Massage Therapy','₱350'),('svc_5c25cf62c12330cbae3f0286','Foot Reflexology (45 min)','massage','massage-therapy','Massage Therapy','₱450'),('svc_65ef0c03ef2fde728e8681fa','Prenatal Massage (60 min)','massage','massage-therapy','Massage Therapy','₱650'),('svc_82a6b0e73af2c0288e72e4ce','Sports Massage (60 min)','massage','massage-therapy','Massage Therapy','₱700'),('svc_30df54c6191d3d7019826d08','Makeup Application','makeup','makeup','Makeup','Price to be confirmed') ON CONFLICT DO NOTHING;
--> statement-breakpoint
INSERT INTO preset_services(feature,style_id,service_id) VALUES ('hairstyle','crew_cut','svc_3248d1335d4b18bacbe2cde7'),('hairstyle','bob_hair','svc_3248d1335d4b18bacbe2cde7'),('hairstyle','layered_hair','svc_3248d1335d4b18bacbe2cde7'),('hairstyle','bun','svc_86ab6d7b8ec9743d47012524'),('hairstyle','curtain_hair','svc_3248d1335d4b18bacbe2cde7'),('hairstyle','pixie_cut','svc_3248d1335d4b18bacbe2cde7'),('hairstyle','pompadour_undercut','svc_3248d1335d4b18bacbe2cde7'),('hairstyle','ponytail','svc_86ab6d7b8ec9743d47012524'),('hairstyle','shag_hair','svc_3248d1335d4b18bacbe2cde7'),('hairstyle','shoulder_length_hair','svc_3248d1335d4b18bacbe2cde7'),('hairstyle','side_part_undercut','svc_3248d1335d4b18bacbe2cde7'),('hairstyle','exp_butterfly_cut','svc_3248d1335d4b18bacbe2cde7'),('hairstyle','exp_wolf_cut','svc_3248d1335d4b18bacbe2cde7'),('hairstyle','exp_korean_two_block','svc_3248d1335d4b18bacbe2cde7'),('hairstyle','exp_comma_hair','svc_3248d1335d4b18bacbe2cde7'),('hairstyle','exp_french_bob_wispy','svc_3248d1335d4b18bacbe2cde7'),('makeup','natural_makeup','svc_30df54c6191d3d7019826d08'),('makeup','no_makeup_makeup','svc_30df54c6191d3d7019826d08'),('makeup','soft_glam','svc_30df54c6191d3d7019826d08'),('makeup','smoky_glam','svc_30df54c6191d3d7019826d08'),('makeup','dewy_peach','svc_30df54c6191d3d7019826d08'),('makeup','rosy_pink','svc_30df54c6191d3d7019826d08'),('makeup','bronze_golden_glam','svc_30df54c6191d3d7019826d08'),('makeup','matte_nude','svc_30df54c6191d3d7019826d08'),('makeup','classic_red_lip','svc_30df54c6191d3d7019826d08'),('makeup','bold_evening_glam','svc_30df54c6191d3d7019826d08'),('makeup','exp_cloud_berry_lips','svc_30df54c6191d3d7019826d08'),('makeup','exp_manga_lash','svc_30df54c6191d3d7019826d08'),('makeup','exp_icy_silver','svc_30df54c6191d3d7019826d08'),('nails','classic_red','svc_c81a7edbd144065312ebd00a'),('nails','nude_pink','svc_c81a7edbd144065312ebd00a'),('nails','glossy_black','svc_c81a7edbd144065312ebd00a'),('nails','french_tip','svc_c81a7edbd144065312ebd00a'),('nails','pink_ombre','svc_c81a7edbd144065312ebd00a'),('nails','exp_raspberry_jelly','svc_c81a7edbd144065312ebd00a'),('nails','exp_pink_aura','svc_c81a7edbd144065312ebd00a'),('nails','exp_negative_space_microdots','svc_c81a7edbd144065312ebd00a') ON CONFLICT DO NOTHING;
--> statement-breakpoint
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_create_service_appointment(p_client uuid,p_stylist uuid,p_service text,p_type text,p_date timestamptz,p_duration integer,p_price integer,p_notes text,p_look uuid,p_service_id text)
RETURNS TABLE(outcome text,appointment_id uuid) LANGUAGE plpgsql AS $$ DECLARE r record;s salon_services%ROWTYPE; BEGIN
 SELECT * INTO s FROM salon_services WHERE id=p_service_id AND active FOR SHARE;
 IF NOT FOUND OR s.name<>p_service OR s.service_type<>p_type THEN RETURN QUERY SELECT 'invalid_service',NULL::uuid;RETURN;END IF;
 SELECT * INTO r FROM beautycore_create_appointment(p_client,p_stylist,s.name,s.service_type,p_date,90,p_price,p_notes,p_look);
 IF r.outcome='created' THEN INSERT INTO appointment_services VALUES(r.appointment_id,s.id); END IF;
 RETURN QUERY SELECT r.outcome,r.appointment_id;END $$;
--> statement-breakpoint

CREATE OR REPLACE FUNCTION beautycore_work_available(p_id uuid,p_date timestamptz,p_duration integer)
RETURNS boolean LANGUAGE sql STABLE AS $$
 SELECT EXISTS(SELECT 1 FROM stylist_work_settings w JOIN users u ON u.id=w.stylist_id,
 jsonb_array_elements(w.hours) h WHERE w.stylist_id=p_id AND w.available AND u.is_active AND u.role='stylist'
 AND (h->>'day')::integer=extract(dow FROM p_date AT TIME ZONE 'Asia/Manila')
 AND (p_date AT TIME ZONE 'Asia/Manila')::time >= (h->>'start')::time
 AND (p_date AT TIME ZONE 'Asia/Manila')::date=(p_date AT TIME ZONE 'Asia/Manila'+make_interval(mins=>90))::date
 AND (p_date AT TIME ZONE 'Asia/Manila'+make_interval(mins=>90))::time <= (h->>'end')::time);
$$;
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_validate_appointment_assignment() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.stylist_id IS NULL OR NEW.status NOT IN ('pending','confirmed') THEN RETURN NEW; END IF;
 IF TG_OP='UPDATE' THEN
  IF OLD.stylist_id IS NOT DISTINCT FROM NEW.stylist_id AND OLD.appointment_date=NEW.appointment_date
    AND OLD.duration_minutes=NEW.duration_minutes AND OLD.service_type=NEW.service_type
    AND OLD.status=NEW.status THEN RETURN NEW; END IF;
 END IF;
 NEW.duration_minutes := 90;
 PERFORM pg_advisory_xact_lock(hashtextextended(NEW.stylist_id::text,0));
 IF NOT EXISTS(SELECT 1 FROM users u JOIN stylist_specialties ss ON ss.stylist_id=u.id WHERE u.id=NEW.stylist_id AND u.role='stylist' AND u.is_active AND ss.service_type=NEW.service_type)
 OR NOT beautycore_work_available(NEW.stylist_id,NEW.appointment_date AT TIME ZONE 'UTC',NEW.duration_minutes) THEN
 RAISE EXCEPTION 'stylist_unavailable' USING ERRCODE='23514'; END IF;
 IF EXISTS(SELECT 1 FROM appointments a WHERE a.stylist_id=NEW.stylist_id AND a.status IN ('pending','confirmed') AND a.id IS DISTINCT FROM NEW.id
 AND NEW.appointment_date<a.appointment_date+make_interval(mins=>90)
 AND a.appointment_date<NEW.appointment_date+make_interval(mins=>90)) THEN
 RAISE EXCEPTION 'appointment_conflict' USING ERRCODE='23P01'; END IF;
 NEW.status := 'confirmed';
 RETURN NEW;
END $$;
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_create_appointment(p_client uuid,p_stylist uuid,p_service text,p_type text,p_date timestamptz,p_duration integer,p_price integer,p_notes text,p_look uuid)
RETURNS TABLE(outcome text,appointment_id uuid) LANGUAGE plpgsql AS $$
DECLARE created_id uuid;
BEGIN
 p_duration := 90;
 IF NOT EXISTS(SELECT 1 FROM users WHERE id=p_client AND role='client' AND is_active) THEN RETURN QUERY SELECT 'invalid_client',NULL::uuid; RETURN; END IF;
 IF p_look IS NOT NULL AND NOT EXISTS(SELECT 1 FROM ai_generations WHERE id=p_look AND client_id=p_client AND saved_at IS NOT NULL AND result_hash IS NOT NULL AND style_type::text=p_type) THEN
  RETURN QUERY SELECT 'invalid_look',NULL::uuid; RETURN;
 END IF;
 IF p_stylist IS NOT NULL THEN
  PERFORM pg_advisory_xact_lock(hashtextextended(p_stylist::text,0));
  IF NOT EXISTS(SELECT 1 FROM users u JOIN stylist_specialties ss ON ss.stylist_id=u.id WHERE u.id=p_stylist AND u.role='stylist' AND u.is_active AND ss.service_type=p_type) THEN
   RETURN QUERY SELECT 'unqualified',NULL::uuid; RETURN;
  END IF;
  IF NOT beautycore_work_available(p_stylist,p_date,p_duration) THEN RETURN QUERY SELECT 'unavailable',NULL::uuid; RETURN; END IF;
  IF EXISTS(SELECT 1 FROM appointments a WHERE a.stylist_id=p_stylist AND a.status IN ('pending','confirmed')
    AND (p_date AT TIME ZONE 'UTC')<a.appointment_date+make_interval(mins=>90)
    AND a.appointment_date<(p_date AT TIME ZONE 'UTC')+make_interval(mins=>90)) THEN
   RETURN QUERY SELECT 'unavailable',NULL::uuid; RETURN;
  END IF;
 END IF;
 INSERT INTO appointments(client_id,stylist_id,service_name,service_type,appointment_date,duration_minutes,total_price,notes,ai_generation_id)
  VALUES(p_client,p_stylist,p_service,p_type,p_date AT TIME ZONE 'UTC',p_duration,p_price,p_notes,p_look) RETURNING id INTO created_id;
 RETURN QUERY SELECT 'created',created_id;
END $$;
