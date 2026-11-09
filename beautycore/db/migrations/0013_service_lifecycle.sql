CREATE TABLE IF NOT EXISTS appointment_lifecycle_policy(id boolean PRIMARY KEY DEFAULT true CHECK(id), enabled_at timestamptz NOT NULL DEFAULT now());
--> statement-breakpoint
INSERT INTO appointment_lifecycle_policy(id) VALUES(true) ON CONFLICT DO NOTHING;
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS appointment_service_tracking(
 appointment_id uuid PRIMARY KEY REFERENCES appointments(id) ON DELETE CASCADE,
 arrived_at timestamptz, started_at timestamptz, ended_at timestamptz,
 no_show_at timestamptz, no_show_by uuid REFERENCES users(id), release_at timestamptz,
 last_actor uuid REFERENCES users(id), stop_reason text, explanation varchar(1000)
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS appointment_activity(
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), appointment_id uuid NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
 action text NOT NULL, previous_status text, status text NOT NULL,
 actor_id uuid REFERENCES users(id), source text NOT NULL, happened_at timestamptz NOT NULL DEFAULT now(),
 explanation varchar(1000), details jsonb NOT NULL DEFAULT '{}'::jsonb
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS appointment_activity_visit_idx ON appointment_activity(appointment_id,happened_at);
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_lifecycle_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE action text:=current_setting('beautycore.lifecycle_action',true); who uuid:=nullif(current_setting('beautycore.actor_id',true),'')::uuid;
BEGIN
 IF TG_OP='DELETE' THEN
  IF OLD.status IN ('no_show','in_progress') THEN RAISE EXCEPTION 'Service history cannot be deleted' USING ERRCODE='23514'; END IF;
  RETURN OLD;
 END IF;
 IF OLD.status='no_show' AND (action IS DISTINCT FROM 'restore' OR NOT EXISTS(SELECT 1 FROM users WHERE id=who AND role='admin' AND is_active)) THEN
  RAISE EXCEPTION 'No-show appointment requires administrator restoration' USING ERRCODE='23514';
 END IF;
 IF NEW.status='in_progress' AND OLD.status<>'in_progress' AND
  (OLD.status<>'confirmed' OR action IS DISTINCT FROM 'start') THEN RAISE EXCEPTION 'Start service through the service controls' USING ERRCODE='23514'; END IF;
 IF NEW.status='no_show' AND OLD.status<>'no_show' AND
  (OLD.status<>'confirmed' OR action NOT IN ('no_show','automatic_no_show') OR action IS NULL
   OR EXISTS(SELECT 1 FROM appointment_service_tracking WHERE appointment_id=OLD.id AND (arrived_at IS NOT NULL OR started_at IS NOT NULL)))
 THEN RAISE EXCEPTION 'An attended service cannot be marked no-show' USING ERRCODE='23514'; END IF;
 IF OLD.status='in_progress' AND (NEW.status NOT IN ('in_progress','completed','cancelled') OR
   (NEW.stylist_id,NEW.appointment_date,NEW.service_type,NEW.client_id) IS DISTINCT FROM (OLD.stylist_id,OLD.appointment_date,OLD.service_type,OLD.client_id))
 THEN RAISE EXCEPTION 'Finish or cancel the running service before changing its schedule' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
--> statement-breakpoint
DROP TRIGGER IF EXISTS beautycore_lifecycle_guard ON appointments;
--> statement-breakpoint
CREATE TRIGGER beautycore_lifecycle_guard BEFORE UPDATE OR DELETE ON appointments FOR EACH ROW EXECUTE FUNCTION beautycore_lifecycle_guard();
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_audit_appointment() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE who uuid:=nullif(current_setting('beautycore.actor_id',true),'')::uuid;
 action text:=coalesce(nullif(current_setting('beautycore.lifecycle_action',true),''),'status_update');
 stamp timestamptz:=coalesce(nullif(current_setting('beautycore.action_time',true),'')::timestamptz,clock_timestamp());
BEGIN
 IF TG_OP='INSERT' OR NEW.status IS DISTINCT FROM OLD.status THEN
  IF NEW.status IN ('completed','cancelled') THEN
   INSERT INTO appointment_service_tracking(appointment_id,ended_at,last_actor,release_at,stop_reason)
    VALUES(NEW.id,stamp,who,stamp,NEW.status::text) ON CONFLICT(appointment_id) DO UPDATE SET
    ended_at=EXCLUDED.ended_at,last_actor=EXCLUDED.last_actor,release_at=EXCLUDED.release_at,stop_reason=EXCLUDED.stop_reason;
  END IF;
  INSERT INTO appointment_activity(appointment_id,action,previous_status,status,actor_id,source,happened_at,explanation,details)
   VALUES(NEW.id,CASE WHEN TG_OP='INSERT' THEN 'booked' ELSE action END,CASE WHEN TG_OP='UPDATE' THEN OLD.status::text END,
   NEW.status::text,who,CASE WHEN action='automatic_no_show' THEN 'system' WHEN who IS NOT NULL THEN 'portal' ELSE 'database' END,
   stamp,nullif(current_setting('beautycore.action_reason',true),''),
   jsonb_build_object('scheduledAt',NEW.appointment_date,'stylistId',NEW.stylist_id));
 END IF;
 RETURN NEW;
END $$;
--> statement-breakpoint
DROP TRIGGER IF EXISTS beautycore_appointment_audit ON appointments;
--> statement-breakpoint
CREATE TRIGGER beautycore_appointment_audit AFTER INSERT OR UPDATE OF status ON appointments FOR EACH ROW EXECUTE FUNCTION beautycore_audit_appointment();
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_service_action(p_id uuid,p_actor uuid,p_action text,p_reason text DEFAULT NULL,p_date timestamptz DEFAULT NULL,p_now timestamptz DEFAULT clock_timestamp())
RETURNS TABLE(outcome text) LANGUAGE plpgsql AS $$
DECLARE a appointments%ROWTYPE; staff uuid; role_name text; t appointment_service_tracking%ROWTYPE;
BEGIN
 SELECT role::text INTO role_name FROM users WHERE id=p_actor AND is_active;
 SELECT stylist_id INTO staff FROM appointments WHERE id=p_id;
 IF staff IS NOT NULL THEN PERFORM pg_advisory_xact_lock(hashtextextended(staff::text,0)); END IF;
 SELECT * INTO a FROM appointments WHERE id=p_id FOR UPDATE;
 IF NOT FOUND OR role_name NOT IN ('admin','stylist') OR role_name IS NULL OR
    (role_name='stylist' AND a.stylist_id IS DISTINCT FROM p_actor) THEN RETURN QUERY SELECT 'not_found';RETURN; END IF;
 IF a.stylist_id IS DISTINCT FROM staff THEN RETURN QUERY SELECT 'conflict';RETURN; END IF;
 IF length(coalesce(p_reason,''))>1000 THEN RETURN QUERY SELECT 'invalid_reason';RETURN;END IF;
 SELECT * INTO t FROM appointment_service_tracking WHERE appointment_id=p_id;
 PERFORM set_config('beautycore.actor_id',p_actor::text,true),set_config('beautycore.lifecycle_action',p_action,true),
   set_config('beautycore.action_time',p_now::text,true),set_config('beautycore.action_reason',coalesce(p_reason,''),true);
 IF p_action='restore' THEN
  IF role_name<>'admin' OR a.status<>'no_show' OR p_date IS NULL OR p_date<=p_now OR a.stylist_id IS NULL OR nullif(trim(p_reason),'') IS NULL THEN RETURN QUERY SELECT 'ineligible';RETURN;END IF;
  UPDATE appointments SET status='confirmed',appointment_date=p_date AT TIME ZONE 'UTC' WHERE id=p_id;
  UPDATE appointment_service_tracking SET last_actor=p_actor,release_at=NULL WHERE appointment_id=p_id;
  RETURN QUERY SELECT 'updated';RETURN;
 END IF;
 IF p_action='other' THEN
  IF a.status NOT IN ('confirmed','in_progress') OR nullif(trim(p_reason),'') IS NULL THEN RETURN QUERY SELECT 'ineligible';RETURN;END IF;
  INSERT INTO appointment_activity(appointment_id,action,previous_status,status,actor_id,source,happened_at,explanation)
   VALUES(p_id,p_action,a.status::text,a.status::text,p_actor,'portal',p_now,p_reason);
  RETURN QUERY SELECT 'updated';RETURN;
 END IF;
 IF p_action='cancel' THEN
  IF a.status NOT IN ('pending','confirmed','in_progress') THEN RETURN QUERY SELECT 'ineligible';RETURN;END IF;
  INSERT INTO appointment_service_tracking(appointment_id,stop_reason,explanation,last_actor) VALUES(p_id,'cancelled',p_reason,p_actor)
   ON CONFLICT(appointment_id) DO UPDATE SET stop_reason=EXCLUDED.stop_reason,explanation=EXCLUDED.explanation,last_actor=p_actor;
  UPDATE appointments SET status='cancelled' WHERE id=p_id;RETURN QUERY SELECT 'updated';RETURN;
 END IF;
 IF a.status<>'confirmed' OR a.stylist_id IS NULL THEN RETURN QUERY SELECT 'ineligible';RETURN;END IF;
 IF p_action IN ('arrive','start') THEN
  IF p_now<(a.appointment_date AT TIME ZONE 'UTC')-interval '30 minutes' OR
    (t.arrived_at IS NULL AND p_now>=(a.appointment_date AT TIME ZONE 'UTC')+interval '30 minutes') THEN RETURN QUERY SELECT 'outside_window';RETURN; END IF;
  IF p_action='start' AND EXISTS(SELECT 1 FROM appointments WHERE stylist_id=staff AND status='in_progress' AND id<>p_id) THEN RETURN QUERY SELECT 'conflict';RETURN;END IF;
  IF p_action='arrive' AND t.arrived_at IS NOT NULL THEN RETURN QUERY SELECT 'existing';RETURN;END IF;
  INSERT INTO appointment_service_tracking(appointment_id,arrived_at,started_at,last_actor)
   VALUES(p_id,coalesce(t.arrived_at,p_now),CASE WHEN p_action='start' THEN p_now END,p_actor)
   ON CONFLICT(appointment_id) DO UPDATE SET arrived_at=EXCLUDED.arrived_at,started_at=EXCLUDED.started_at,last_actor=p_actor;
  IF p_action='start' THEN UPDATE appointments SET status='in_progress' WHERE id=p_id;
  ELSE INSERT INTO appointment_activity(appointment_id,action,previous_status,status,actor_id,source,happened_at)
   VALUES(p_id,'arrived',a.status::text,a.status::text,p_actor,'portal',p_now); END IF;
  RETURN QUERY SELECT 'updated';RETURN;
 END IF;
 IF p_action='no_show' THEN
  IF t.arrived_at IS NOT NULL OR t.started_at IS NOT NULL OR p_now<(a.appointment_date AT TIME ZONE 'UTC') OR nullif(trim(p_reason),'') IS NULL THEN RETURN QUERY SELECT 'ineligible';RETURN;END IF;
  INSERT INTO appointment_service_tracking(appointment_id,no_show_at,no_show_by,release_at,last_actor,stop_reason,explanation)
   VALUES(p_id,p_now,p_actor,p_now,p_actor,'no_show',p_reason) ON CONFLICT(appointment_id) DO UPDATE SET
   no_show_at=p_now,no_show_by=p_actor,release_at=p_now,last_actor=p_actor,stop_reason='no_show',explanation=p_reason;
  UPDATE appointments SET status='no_show' WHERE id=p_id;RETURN QUERY SELECT 'updated';RETURN;
 END IF;
 RETURN QUERY SELECT 'ineligible';
END $$;
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_process_no_shows(p_now timestamptz DEFAULT clock_timestamp()) RETURNS integer LANGUAGE plpgsql AS $$
DECLARE candidate record; a appointments%ROWTYPE; n integer:=0;
BEGIN
 -- Existing overdue records before policy installation are never retroactively changed.
 FOR candidate IN SELECT x.id,x.stylist_id FROM appointments x,appointment_lifecycle_policy p
  WHERE x.status='confirmed' AND x.stylist_id IS NOT NULL AND (x.appointment_date AT TIME ZONE 'UTC')>=p.enabled_at
  AND (x.appointment_date AT TIME ZONE 'UTC')+interval '30 minutes'<=p_now AND NOT EXISTS(SELECT 1 FROM appointment_service_tracking t WHERE t.appointment_id=x.id AND (t.arrived_at IS NOT NULL OR t.started_at IS NOT NULL)) ORDER BY x.stylist_id,x.id LIMIT 200 LOOP
  IF NOT pg_try_advisory_xact_lock(hashtextextended(candidate.stylist_id::text,0)) THEN CONTINUE; END IF;
  SELECT * INTO a FROM appointments WHERE id=candidate.id FOR UPDATE;
  IF a.status<>'confirmed' OR a.stylist_id IS DISTINCT FROM candidate.stylist_id OR
    (a.appointment_date AT TIME ZONE 'UTC')+interval '30 minutes'>p_now OR
    EXISTS(SELECT 1 FROM appointment_service_tracking WHERE appointment_id=a.id AND (arrived_at IS NOT NULL OR started_at IS NOT NULL)) THEN CONTINUE;END IF;
  PERFORM set_config('beautycore.actor_id','',true),set_config('beautycore.lifecycle_action','automatic_no_show',true),
    set_config('beautycore.action_time',p_now::text,true),set_config('beautycore.action_reason','Customer not recorded as arrived within 30 minutes',true);
  INSERT INTO appointment_service_tracking(appointment_id,no_show_at,release_at,stop_reason)
   VALUES(a.id,p_now,p_now,'no_show') ON CONFLICT(appointment_id) DO UPDATE SET no_show_at=p_now,release_at=p_now,stop_reason='no_show',no_show_by=NULL,last_actor=NULL;
  UPDATE appointments SET status='no_show' WHERE id=a.id;n:=n+1;
 END LOOP;
 RETURN n;
END $$;

--> statement-breakpoint

CREATE OR REPLACE FUNCTION beautycore_validate_appointment_assignment() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.status='in_progress' THEN RETURN NEW; END IF;
 IF NEW.stylist_id IS NULL OR NEW.status NOT IN ('pending','confirmed','in_progress') THEN RETURN NEW; END IF;
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
 IF EXISTS(SELECT 1 FROM appointments a WHERE a.stylist_id=NEW.stylist_id AND a.status IN ('pending','confirmed','in_progress') AND a.id IS DISTINCT FROM NEW.id
 AND NEW.appointment_date<CASE WHEN a.status='in_progress' THEN greatest(a.appointment_date+make_interval(mins=>90),(date_trunc('minute',clock_timestamp())+interval '91 minutes') AT TIME ZONE 'UTC') ELSE a.appointment_date+make_interval(mins=>90) END
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
  IF EXISTS(SELECT 1 FROM appointments a WHERE a.stylist_id=p_stylist AND a.status IN ('pending','confirmed','in_progress')
    AND (p_date AT TIME ZONE 'UTC')<CASE WHEN a.status='in_progress' THEN greatest(a.appointment_date+make_interval(mins=>90),(date_trunc('minute',clock_timestamp())+interval '91 minutes') AT TIME ZONE 'UTC') ELSE a.appointment_date+make_interval(mins=>90) END
    AND a.appointment_date<(p_date AT TIME ZONE 'UTC')+make_interval(mins=>90)) THEN
   RETURN QUERY SELECT 'unavailable',NULL::uuid; RETURN;
  END IF;
 END IF;
 INSERT INTO appointments(client_id,stylist_id,service_name,service_type,appointment_date,duration_minutes,total_price,notes,ai_generation_id)
  VALUES(p_client,p_stylist,p_service,p_type,p_date AT TIME ZONE 'UTC',p_duration,p_price,p_notes,p_look) RETURNING id INTO created_id;
 RETURN QUERY SELECT 'created',created_id;
END $$;

--> statement-breakpoint

CREATE OR REPLACE FUNCTION beautycore_complete_appointment(p_id uuid,p_actor uuid,p_role text,p_products jsonb)
RETURNS TABLE(outcome text) LANGUAGE plpgsql AS $$
DECLARE a appointments%ROWTYPE; item jsonb;
BEGIN
 SELECT * INTO a FROM appointments WHERE id=p_id FOR UPDATE;
 IF NOT FOUND OR NOT EXISTS(SELECT 1 FROM users WHERE id=p_actor AND role::text=p_role)
    OR NOT coalesce(p_role='admin' OR (p_role='stylist' AND a.stylist_id=p_actor),false) THEN
  RETURN QUERY SELECT 'not_found'::text; RETURN;
 END IF;
 IF a.status='completed' THEN RETURN QUERY SELECT 'existing'::text; RETURN; END IF;
 IF a.status IN ('cancelled','no_show') THEN RETURN QUERY SELECT 'terminal'::text; RETURN; END IF;
 IF a.stylist_id IS NULL THEN RETURN QUERY SELECT 'unassigned'::text; RETURN; END IF;
 PERFORM set_config('beautycore.actor_id',p_actor::text,true),set_config('beautycore.lifecycle_action','completed',true),set_config('beautycore.action_time','',true),set_config('beautycore.action_reason','Service completed',true);
 IF jsonb_typeof(p_products) IS DISTINCT FROM 'array' OR jsonb_array_length(p_products)>20 THEN
  RAISE EXCEPTION 'Invalid product records';
 END IF;
 -- Lock referenced products so a concurrent catalog deletion cannot invalidate completion.
 FOR item IN SELECT value FROM jsonb_array_elements(p_products) LOOP
  IF item->>'inventoryId' IS NOT NULL THEN
   PERFORM id FROM inventory WHERE id=(item->>'inventoryId')::uuid FOR KEY SHARE;
   IF NOT FOUND THEN RETURN QUERY SELECT 'invalid_product'::text; RETURN; END IF;
  END IF;
 END LOOP;
 -- Status and usage are committed together; any constraint failure rolls back both.
 UPDATE appointments SET status='completed',completed_at=now(),completed_by=p_actor WHERE id=p_id;
 FOR item IN SELECT value FROM jsonb_array_elements(p_products) LOOP
  INSERT INTO appointment_product_usage(appointment_id,inventory_id,product_name,brand,quantity,unit,unit_cost,recorded_by)
  VALUES(p_id,(item->>'inventoryId')::uuid,item->>'productName',item->>'brand',(item->>'quantity')::numeric,item->>'unit',(item->>'unitCost')::numeric,p_actor);
 END LOOP;
 RETURN QUERY SELECT 'completed'::text;
END $$;

--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_create_service_appointment(p_client uuid,p_stylist uuid,p_service text,p_type text,p_date timestamptz,p_duration integer,p_price integer,p_notes text,p_look uuid,p_service_id text,p_actor uuid)
RETURNS TABLE(outcome text,appointment_id uuid) LANGUAGE plpgsql AS $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM users WHERE id=p_actor AND is_active AND (role='admin' OR (role='client' AND id=p_client))) THEN RETURN QUERY SELECT 'invalid_client',NULL::uuid;RETURN;END IF;
 PERFORM set_config('beautycore.actor_id',p_actor::text,true),set_config('beautycore.lifecycle_action','booked',true),set_config('beautycore.action_time','',true),set_config('beautycore.action_reason','',true);
 RETURN QUERY SELECT * FROM beautycore_create_service_appointment(p_client,p_stylist,p_service,p_type,p_date,90,p_price,p_notes,p_look,p_service_id);
END $$;

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
 IF NOT FOUND OR a.status IN ('cancelled','no_show') OR a.total_price IS NULL THEN RAISE EXCEPTION 'payment_not_allowed' USING ERRCODE='23514'; END IF;
 SELECT coalesce(sum(amount),0) INTO paid FROM appointment_payments WHERE appointment_id=p_appointment;
 IF p_amount IS NULL OR p_amount<1 OR p_amount>100000000 OR p_amount+paid>a.total_price THEN RAISE EXCEPTION 'invalid_payment_amount' USING ERRCODE='23514'; END IF;
 INSERT INTO appointment_payments(appointment_id,amount,method,reference,request_id,recorded_by) VALUES(p_appointment,p_amount,p_method,nullif(trim(p_reference),''),p_request,p_actor) RETURNING id INTO payment_id;
 RETURN payment_id;
END $$;
