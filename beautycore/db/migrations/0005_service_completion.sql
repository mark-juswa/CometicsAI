-- Additive only. Run explicitly after 0004; never applied at application startup.
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS completed_at timestamptz;
--> statement-breakpoint
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS completed_by uuid REFERENCES users(id);
--> statement-breakpoint
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS brand varchar(120);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS appointment_reviews (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 appointment_id uuid NOT NULL UNIQUE REFERENCES appointments(id) ON DELETE RESTRICT,
 client_id uuid NOT NULL REFERENCES users(id),
 stylist_id uuid NOT NULL REFERENCES users(id),
 rating integer NOT NULL CONSTRAINT review_rating_range CHECK (rating BETWEEN 1 AND 5),
 comment varchar(1000), created_at timestamptz NOT NULL DEFAULT now()
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS appointment_reviews_stylist_idx ON appointment_reviews(stylist_id);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS appointment_reviews_client_idx ON appointment_reviews(client_id);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS appointment_product_usage (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 appointment_id uuid NOT NULL REFERENCES appointments(id) ON DELETE RESTRICT,
 inventory_id uuid REFERENCES inventory(id) ON DELETE SET NULL,
 product_name varchar(255) NOT NULL CONSTRAINT usage_product_name CHECK (length(trim(product_name))>0),
 brand varchar(120), quantity numeric(12,3) CONSTRAINT usage_quantity_positive CHECK(quantity>0 AND quantity<=1000000), unit varchar(32),
 unit_cost numeric(12,2) CONSTRAINT usage_cost_nonnegative CHECK(unit_cost>=0 AND unit_cost<=1000000),
 recorded_by uuid NOT NULL REFERENCES users(id), created_at timestamptz NOT NULL DEFAULT now(),
 CONSTRAINT usage_quantity_unit CHECK(quantity IS NULL OR unit IS NOT NULL),
 CONSTRAINT usage_cost_basis CHECK(unit_cost IS NULL OR (quantity IS NOT NULL AND unit IS NOT NULL))
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS appointment_product_usage_appointment_idx ON appointment_product_usage(appointment_id);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS appointment_product_usage_inventory_idx ON appointment_product_usage(inventory_id);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS appointment_product_usage_recorder_idx ON appointment_product_usage(recorded_by);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS appointments_completed_by_idx ON appointments(completed_by);
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_protect_service_history() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF OLD.status='completed' THEN
  IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Completed service history cannot be deleted'; END IF;
  IF (NEW.status,NEW.client_id,NEW.stylist_id,NEW.appointment_date,NEW.ai_generation_id,NEW.service_name,NEW.service_type,NEW.completed_at,NEW.completed_by)
     IS DISTINCT FROM (OLD.status,OLD.client_id,OLD.stylist_id,OLD.appointment_date,OLD.ai_generation_id,OLD.service_name,OLD.service_type,OLD.completed_at,OLD.completed_by)
  THEN RAISE EXCEPTION 'Completed service attribution is immutable'; END IF;
 END IF;
 IF TG_OP='UPDATE' AND OLD.status='cancelled' AND NEW.status<>OLD.status THEN
  RAISE EXCEPTION 'Cancelled appointments cannot be reopened';
 END IF;
 IF TG_OP='DELETE' THEN RETURN OLD; END IF;
 RETURN NEW;
END $$;
--> statement-breakpoint
DROP TRIGGER IF EXISTS beautycore_service_history_guard ON appointments;
--> statement-breakpoint
CREATE TRIGGER beautycore_service_history_guard BEFORE UPDATE OR DELETE ON appointments FOR EACH ROW EXECUTE FUNCTION beautycore_protect_service_history();
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
 IF a.status='cancelled' THEN RETURN QUERY SELECT 'terminal'::text; RETURN; END IF;
 IF a.stylist_id IS NULL THEN RETURN QUERY SELECT 'unassigned'::text; RETURN; END IF;
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
CREATE OR REPLACE FUNCTION beautycore_review_appointment(p_id uuid,p_client uuid,p_rating integer,p_comment text)
RETURNS TABLE(outcome text) LANGUAGE plpgsql AS $$
DECLARE a appointments%ROWTYPE; existing appointment_reviews%ROWTYPE;
BEGIN
 SELECT * INTO a FROM appointments WHERE id=p_id FOR UPDATE;
 IF NOT FOUND OR a.client_id<>p_client OR NOT EXISTS(SELECT 1 FROM users WHERE id=p_client AND role='client') THEN
  RETURN QUERY SELECT 'not_found'::text; RETURN;
 END IF;
 IF a.status<>'completed' OR a.stylist_id IS NULL THEN RETURN QUERY SELECT 'ineligible'::text; RETURN; END IF;
 SELECT * INTO existing FROM appointment_reviews WHERE appointment_id=p_id;
 IF FOUND THEN
  RETURN QUERY SELECT CASE WHEN existing.rating=p_rating AND existing.comment IS NOT DISTINCT FROM p_comment THEN 'existing' ELSE 'conflict' END; RETURN;
 END IF;
 INSERT INTO appointment_reviews(appointment_id,client_id,stylist_id,rating,comment) VALUES(p_id,a.client_id,a.stylist_id,p_rating,p_comment);
 RETURN QUERY SELECT 'created'::text;
END $$;
