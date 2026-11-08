-- Reserve ninety minutes per new booking. Preserve every existing record.
ALTER TABLE appointments ALTER COLUMN duration_minutes SET DEFAULT 90;
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_work_available(p_id uuid,p_date timestamptz,p_duration integer)
RETURNS boolean LANGUAGE sql STABLE AS $$
 SELECT EXISTS(SELECT 1 FROM stylist_work_settings w JOIN users u ON u.id=w.stylist_id,
 jsonb_array_elements(w.hours) h WHERE w.stylist_id=p_id AND w.available AND u.is_active AND u.role='stylist'
 AND (h->>'day')::integer=extract(dow FROM p_date AT TIME ZONE 'Asia/Manila')
 AND (p_date AT TIME ZONE 'Asia/Manila')::time >= (h->>'start')::time
 AND (p_date AT TIME ZONE 'Asia/Manila')::date=(p_date AT TIME ZONE 'Asia/Manila'+make_interval(mins=>greatest(p_duration,90)))::date
 AND (p_date AT TIME ZONE 'Asia/Manila'+make_interval(mins=>greatest(p_duration,90)))::time <= (h->>'end')::time);
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
 PERFORM pg_advisory_xact_lock(hashtextextended(NEW.stylist_id::text,0));
 IF NOT EXISTS(SELECT 1 FROM users u JOIN stylist_specialties ss ON ss.stylist_id=u.id WHERE u.id=NEW.stylist_id AND u.role='stylist' AND u.is_active AND ss.service_type=NEW.service_type)
 OR NOT beautycore_work_available(NEW.stylist_id,NEW.appointment_date AT TIME ZONE 'UTC',NEW.duration_minutes) THEN
 RAISE EXCEPTION 'stylist_unavailable' USING ERRCODE='23514'; END IF;
 IF EXISTS(SELECT 1 FROM appointments a WHERE a.stylist_id=NEW.stylist_id AND a.status IN ('pending','confirmed') AND a.id IS DISTINCT FROM NEW.id
 AND NEW.appointment_date<a.appointment_date+make_interval(mins=>greatest(a.duration_minutes,90))
 AND a.appointment_date<NEW.appointment_date+make_interval(mins=>greatest(NEW.duration_minutes,90))) THEN
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
    AND (p_date AT TIME ZONE 'UTC')<a.appointment_date+make_interval(mins=>greatest(a.duration_minutes,90))
    AND a.appointment_date<(p_date AT TIME ZONE 'UTC')+make_interval(mins=>greatest(p_duration,90))) THEN
   RETURN QUERY SELECT 'unavailable',NULL::uuid; RETURN;
  END IF;
 END IF;
 INSERT INTO appointments(client_id,stylist_id,service_name,service_type,appointment_date,duration_minutes,total_price,notes,ai_generation_id)
  VALUES(p_client,p_stylist,p_service,p_type,p_date AT TIME ZONE 'UTC',p_duration,p_price,p_notes,p_look) RETURNING id INTO created_id;
 RETURN QUERY SELECT 'created',created_id;
END $$;
