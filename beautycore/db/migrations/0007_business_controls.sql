-- Additive business controls. Existing accounts and business records are retained.
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone varchar(40);
--> statement-breakpoint
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true;
--> statement-breakpoint
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS duration_minutes integer NOT NULL DEFAULT 60;
--> statement-breakpoint
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conname='appointment_duration_positive') THEN
  ALTER TABLE appointments ADD CONSTRAINT appointment_duration_positive CHECK (duration_minutes BETWEEN 1 AND 1440) NOT VALID;
 END IF;
END $$;
--> statement-breakpoint
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conname='inventory_nonnegative_stock') THEN
  ALTER TABLE inventory ADD CONSTRAINT inventory_nonnegative_stock CHECK (current_stock >= 0) NOT VALID;
 END IF;
END $$;
--> statement-breakpoint
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conname='inventory_nonnegative_threshold') THEN
  ALTER TABLE inventory ADD CONSTRAINT inventory_nonnegative_threshold CHECK (minimum_threshold >= 0) NOT VALID;
 END IF;
END $$;
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS stylist_specialties (
 stylist_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 service_type varchar(40) NOT NULL CHECK(service_type IN ('hair','nail','makeup','treatment','massage','aesthetic')),
 PRIMARY KEY(stylist_id,service_type)
);
--> statement-breakpoint
-- Preserve existing assignments using the service groups they have actually performed.
INSERT INTO stylist_specialties(stylist_id,service_type)
 SELECT DISTINCT a.stylist_id,a.service_type FROM appointments a
 JOIN users u ON u.id=a.stylist_id AND u.role='stylist'
 WHERE a.stylist_id IS NOT NULL AND a.service_type IN ('hair','nail','makeup','treatment','massage','aesthetic')
 ON CONFLICT DO NOTHING;
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS inventory_transactions (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 inventory_id uuid REFERENCES inventory(id) ON DELETE SET NULL,
 product_name varchar(255) NOT NULL,
 direction varchar(3) NOT NULL CHECK(direction IN ('in','out')),
 quantity integer NOT NULL CHECK(quantity > 0),
 stock_after integer NOT NULL CHECK(stock_after >= 0),
 note varchar(500),
 recorded_by uuid NOT NULL REFERENCES users(id),
 created_at timestamptz NOT NULL DEFAULT now()
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS inventory_transactions_item_created_idx ON inventory_transactions(inventory_id,created_at DESC);
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_validate_appointment_assignment() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.stylist_id IS NULL OR NEW.status NOT IN ('pending','confirmed') THEN RETURN NEW; END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended(NEW.stylist_id::text,0));
 IF NOT EXISTS(SELECT 1 FROM users u JOIN stylist_specialties ss ON ss.stylist_id=u.id
               WHERE u.id=NEW.stylist_id AND u.role='stylist' AND u.is_active AND ss.service_type=NEW.service_type) THEN
  RAISE EXCEPTION 'stylist_not_qualified' USING ERRCODE='23514';
 END IF;
 IF EXISTS(SELECT 1 FROM appointments a WHERE a.stylist_id=NEW.stylist_id
           AND a.status IN ('pending','confirmed') AND a.id IS DISTINCT FROM NEW.id
           AND NEW.appointment_date < a.appointment_date + make_interval(mins => a.duration_minutes)
           AND a.appointment_date < NEW.appointment_date + make_interval(mins => NEW.duration_minutes)) THEN
  RAISE EXCEPTION 'appointment_conflict' USING ERRCODE='23P01';
 END IF;
 RETURN NEW;
END $$;
--> statement-breakpoint
DROP TRIGGER IF EXISTS beautycore_appointment_assignment_guard ON appointments;
--> statement-breakpoint
CREATE TRIGGER beautycore_appointment_assignment_guard BEFORE INSERT OR UPDATE OF stylist_id,service_type,appointment_date,duration_minutes,status ON appointments
 FOR EACH ROW EXECUTE FUNCTION beautycore_validate_appointment_assignment();
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_create_appointment(p_client uuid,p_stylist uuid,p_service text,p_type text,p_date timestamptz,p_duration integer,p_price integer,p_notes text,p_look uuid)
RETURNS TABLE(outcome text,appointment_id uuid) LANGUAGE plpgsql AS $$
DECLARE created_id uuid;
BEGIN
 IF NOT EXISTS(SELECT 1 FROM users WHERE id=p_client AND role='client' AND is_active) THEN RETURN QUERY SELECT 'invalid_client',NULL::uuid; RETURN; END IF;
 IF p_look IS NOT NULL AND NOT EXISTS(SELECT 1 FROM ai_generations WHERE id=p_look AND client_id=p_client AND saved_at IS NOT NULL AND result_hash IS NOT NULL AND style_type::text=p_type) THEN
  RETURN QUERY SELECT 'invalid_look',NULL::uuid; RETURN;
 END IF;
 IF p_stylist IS NOT NULL THEN
  PERFORM pg_advisory_xact_lock(hashtextextended(p_stylist::text,0));
  IF NOT EXISTS(SELECT 1 FROM users u JOIN stylist_specialties ss ON ss.stylist_id=u.id WHERE u.id=p_stylist AND u.role='stylist' AND u.is_active AND ss.service_type=p_type) THEN
   RETURN QUERY SELECT 'unqualified',NULL::uuid; RETURN;
  END IF;
  IF EXISTS(SELECT 1 FROM appointments a WHERE a.stylist_id=p_stylist AND a.status IN ('pending','confirmed')
    AND (p_date AT TIME ZONE 'UTC')<a.appointment_date+make_interval(mins=>a.duration_minutes)
    AND a.appointment_date<(p_date AT TIME ZONE 'UTC')+make_interval(mins=>p_duration)) THEN
   RETURN QUERY SELECT 'unavailable',NULL::uuid; RETURN;
  END IF;
 END IF;
 INSERT INTO appointments(client_id,stylist_id,service_name,service_type,appointment_date,duration_minutes,total_price,notes,ai_generation_id)
  VALUES(p_client,p_stylist,p_service,p_type,p_date AT TIME ZONE 'UTC',p_duration,p_price,p_notes,p_look) RETURNING id INTO created_id;
 RETURN QUERY SELECT 'created',created_id;
END $$;
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_create_stylist(p_name text,p_email text,p_hash text,p_types text[])
RETURNS TABLE(id uuid,name text,email text,is_active boolean) LANGUAGE plpgsql AS $$
DECLARE new_id uuid;
BEGIN
 IF trim(p_name)='' OR length(trim(p_name))>255 OR p_email !~* '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
    OR length(p_email)>255 OR cardinality(p_types)=0
    OR EXISTS(SELECT 1 FROM unnest(p_types) x WHERE x NOT IN ('hair','nail','makeup','treatment','massage','aesthetic')) THEN
  RAISE EXCEPTION 'invalid_stylist_data' USING ERRCODE='22023';
 END IF;
 INSERT INTO users(name,email,password_hash,role,is_active) VALUES(trim(p_name),lower(trim(p_email)),p_hash,'stylist',true) RETURNING users.id INTO new_id;
 INSERT INTO stylist_specialties(stylist_id,service_type) SELECT new_id,x FROM (SELECT DISTINCT unnest(p_types) x) values_to_add;
 RETURN QUERY SELECT u.id,u.name::text,u.email::text,u.is_active FROM users u WHERE u.id=new_id;
END $$;
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_update_stylist(p_id uuid,p_name text,p_email text,p_active boolean,p_types text[])
RETURNS boolean LANGUAGE plpgsql AS $$
BEGIN
 IF EXISTS(SELECT 1 FROM unnest(p_types) x WHERE x NOT IN ('hair','nail','makeup','treatment','massage','aesthetic')) THEN
  RAISE EXCEPTION 'invalid_stylist_specialty' USING ERRCODE='22023';
 END IF;
 UPDATE users SET name=trim(p_name),email=lower(trim(p_email)),is_active=p_active
  WHERE id=p_id AND role='stylist' AND length(trim(p_name)) BETWEEN 1 AND 255
    AND length(p_email)<=255 AND p_email ~* '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$';
 IF NOT FOUND THEN RETURN false; END IF;
 DELETE FROM stylist_specialties WHERE stylist_id=p_id;
 INSERT INTO stylist_specialties(stylist_id,service_type) SELECT p_id,x FROM (SELECT DISTINCT unnest(p_types) x) values_to_add;
 RETURN true;
END $$;
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_inventory_move(p_id uuid,p_actor uuid,p_direction text,p_quantity integer,p_note text)
RETURNS TABLE(outcome text,stock integer,status product_status,last_restocked timestamp) LANGUAGE plpgsql AS $$
DECLARE item inventory%ROWTYPE; new_stock integer;
BEGIN
 IF NOT EXISTS(SELECT 1 FROM users WHERE id=p_actor AND role='admin' AND is_active) THEN RETURN QUERY SELECT 'forbidden',NULL::integer,NULL::product_status,NULL::timestamp; RETURN; END IF;
 IF p_direction NOT IN ('in','out') OR p_quantity<=0 OR p_quantity>1000000 OR length(p_note)>500 THEN
  RETURN QUERY SELECT 'invalid',NULL::integer,NULL::product_status,NULL::timestamp; RETURN;
 END IF;
 SELECT * INTO item FROM inventory WHERE id=p_id FOR UPDATE;
 IF NOT FOUND THEN RETURN QUERY SELECT 'missing',NULL::integer,NULL::product_status,NULL::timestamp; RETURN; END IF;
 new_stock:=item.current_stock + CASE WHEN p_direction='in' THEN p_quantity ELSE -p_quantity END;
 IF new_stock<0 THEN RETURN QUERY SELECT 'insufficient',item.current_stock,item.status,item.last_restocked; RETURN; END IF;
 UPDATE inventory SET current_stock=new_stock,
  status=CASE WHEN new_stock=0 THEN 'out_of_stock'::product_status WHEN new_stock<=item.minimum_threshold THEN 'low_stock'::product_status ELSE 'in_stock'::product_status END,
  last_restocked=CASE WHEN p_direction='in' THEN now()::timestamp ELSE item.last_restocked END WHERE id=p_id;
 INSERT INTO inventory_transactions(inventory_id,product_name,direction,quantity,stock_after,note,recorded_by)
  VALUES(p_id,item.product_name,p_direction,p_quantity,new_stock,nullif(trim(p_note),''),p_actor);
 RETURN QUERY SELECT 'updated',new_stock,
  CASE WHEN new_stock=0 THEN 'out_of_stock'::product_status WHEN new_stock<=item.minimum_threshold THEN 'low_stock'::product_status ELSE 'in_stock'::product_status END,
  CASE WHEN p_direction='in' THEN now()::timestamp ELSE item.last_restocked END;
END $$;
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_create_inventory_item(p_name text,p_brand text,p_category text,p_stock integer,p_threshold integer,p_price integer,p_actor uuid)
RETURNS TABLE(id uuid,product_name text,brand text,category text,current_stock integer,minimum_threshold integer,unit_price integer,status product_status,last_restocked timestamp,created_at timestamp) LANGUAGE plpgsql AS $$
DECLARE item_id uuid; item_status product_status;
BEGIN
 IF NOT EXISTS(SELECT 1 FROM users WHERE users.id=p_actor AND role='admin' AND is_active) THEN RAISE EXCEPTION 'forbidden' USING ERRCODE='42501'; END IF;
 IF trim(p_name)='' OR length(p_name)>255 OR trim(p_category)='' OR length(p_category)>100
    OR p_stock<0 OR p_threshold<0 OR (p_price IS NOT NULL AND p_price<0) THEN RAISE EXCEPTION 'invalid_inventory_item' USING ERRCODE='22023'; END IF;
 item_status:=CASE WHEN p_stock=0 THEN 'out_of_stock'::product_status WHEN p_stock<=p_threshold THEN 'low_stock'::product_status ELSE 'in_stock'::product_status END;
 INSERT INTO inventory(product_name,brand,category,current_stock,minimum_threshold,unit_price,status,last_restocked)
  VALUES(trim(p_name),nullif(trim(p_brand),''),trim(p_category),p_stock,p_threshold,p_price,item_status,CASE WHEN p_stock>0 THEN now() ELSE NULL END) RETURNING inventory.id INTO item_id;
 IF p_stock>0 THEN INSERT INTO inventory_transactions(inventory_id,product_name,direction,quantity,stock_after,note,recorded_by)
  VALUES(item_id,trim(p_name),'in',p_stock,p_stock,'Opening stock',p_actor); END IF;
 RETURN QUERY SELECT i.id,i.product_name::text,i.brand::text,i.category::text,i.current_stock,i.minimum_threshold,i.unit_price,i.status,i.last_restocked,i.created_at FROM inventory i WHERE i.id=item_id;
END $$;
