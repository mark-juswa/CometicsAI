-- Additive catalog metadata and an exact decimal ledger. No product seeding or historical deductions.
ALTER TABLE inventory ALTER COLUMN current_stock TYPE numeric USING current_stock::numeric;
--> statement-breakpoint
ALTER TABLE inventory ALTER COLUMN minimum_threshold TYPE numeric USING minimum_threshold::numeric;
--> statement-breakpoint
ALTER TABLE inventory_transactions ALTER COLUMN quantity TYPE numeric USING quantity::numeric;
--> statement-breakpoint
ALTER TABLE inventory_transactions ALTER COLUMN stock_after TYPE numeric USING stock_after::numeric;
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS inventory_suppliers(id uuid PRIMARY KEY DEFAULT gen_random_uuid(),name varchar(160) NOT NULL,contact varchar(160),email varchar(255),phone varchar(64),address varchar(500),notes varchar(1000),active boolean NOT NULL DEFAULT true);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS inventory_details(
 inventory_id uuid PRIMARY KEY REFERENCES inventory(id) ON DELETE CASCADE, sku varchar(64),item_type text NOT NULL DEFAULT 'consumable' CHECK(item_type IN ('consumable','equipment')),
 description varchar(2000),unit text NOT NULL DEFAULT 'piece' CHECK(unit IN ('piece','bottle','tube','pack','pair','set','g','kg','ml','l','application')),
 maximum_stock numeric CHECK(maximum_stock>=0),purchase_cost numeric CHECK(purchase_cost>=0),selling_price numeric CHECK(selling_price>=0),
 supplier_id uuid REFERENCES inventory_suppliers(id),location varchar(160),expiration_date date,active boolean NOT NULL DEFAULT true,image_data text
);
--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS inventory_sku_unique ON inventory_details(lower(sku)) WHERE sku IS NOT NULL;
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS inventory_policy(id boolean PRIMARY KEY DEFAULT true CHECK(id),shortage_policy text NOT NULL DEFAULT 'block' CHECK(shortage_policy IN ('block','consume_available')),expiry_warning_days integer NOT NULL DEFAULT 30 CHECK(expiry_warning_days BETWEEN 1 AND 365));
--> statement-breakpoint
ALTER TABLE inventory_policy ADD COLUMN IF NOT EXISTS consumption_mode text NOT NULL DEFAULT 'reported_only' CHECK(consumption_mode IN ('reported_only','configured'));
--> statement-breakpoint
INSERT INTO inventory_policy(id) VALUES(true) ON CONFLICT DO NOTHING;
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS service_inventory_requirements(service_id text NOT NULL REFERENCES salon_services(id),inventory_id uuid NOT NULL REFERENCES inventory(id),quantity numeric NOT NULL CHECK(quantity>0 AND quantity<=1000000 AND quantity=round(quantity,3)),PRIMARY KEY(service_id,inventory_id));
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS inventory_transaction_details(
 transaction_id uuid PRIMARY KEY REFERENCES inventory_transactions(id),kind text NOT NULL CHECK(kind IN ('initial_stock','stock_in','stock_out','adjustment','service_consumption','correction','damaged','expired')),
 previous_quantity numeric NOT NULL,unit text NOT NULL,unit_cost numeric CHECK(unit_cost>=0),supplier_id uuid REFERENCES inventory_suppliers(id),supplier_name text,
 reference varchar(160),occurred_at timestamptz NOT NULL,appointment_id uuid REFERENCES appointments(id),service_id text REFERENCES salon_services(id),
 category text NOT NULL,brand text,reason varchar(1000),request_id uuid NOT NULL UNIQUE,request_data jsonb NOT NULL
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS inventory_details_history_date ON inventory_transaction_details(occurred_at,kind);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS inventory_service_consumption(
 appointment_id uuid NOT NULL REFERENCES appointments(id),inventory_id uuid NOT NULL REFERENCES inventory(id),service_id text REFERENCES salon_services(id),
 product_name text NOT NULL,unit text NOT NULL,configured_quantity numeric,requested_quantity numeric NOT NULL,deducted_quantity numeric NOT NULL,shortage numeric NOT NULL DEFAULT 0,
 equipment boolean NOT NULL DEFAULT false,reason varchar(1000),recorded_by uuid NOT NULL REFERENCES users(id),created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(appointment_id,inventory_id)
);
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_inventory_convert(p_quantity numeric,p_from text,p_to text) RETURNS numeric LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE value numeric;
BEGIN
 IF p_quantity<0 OR p_quantity>1000000 OR p_quantity<>round(p_quantity,3) THEN RAISE EXCEPTION 'invalid_quantity' USING ERRCODE='22023';END IF;
 IF p_from=p_to THEN value:=p_quantity;
 ELSIF (p_from,p_to) IN (('l','ml'),('kg','g')) THEN value:=p_quantity*1000;
 ELSIF (p_from,p_to) IN (('ml','l'),('g','kg')) THEN value:=p_quantity/1000;
 ELSE RAISE EXCEPTION 'unit_mismatch' USING ERRCODE='22023'; END IF;
 IF value<>round(value,3) THEN RAISE EXCEPTION 'quantity_precision' USING ERRCODE='22023';END IF;
 RETURN value;
END $$;

--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_inventory_guard() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 IF TG_OP='DELETE' THEN
  IF EXISTS(SELECT 1 FROM inventory_transactions WHERE inventory_id=OLD.id) OR EXISTS(SELECT 1 FROM inventory_service_consumption WHERE inventory_id=OLD.id) THEN RAISE EXCEPTION 'Archive products with history instead of deleting them' USING ERRCODE='23514';END IF;RETURN OLD;
 END IF;
 IF TG_OP='UPDATE' AND NEW.current_stock IS DISTINCT FROM OLD.current_stock AND current_setting('beautycore.inventory_write',true) IS DISTINCT FROM 'allowed' THEN RAISE EXCEPTION 'Record a stock transaction instead of editing stock' USING ERRCODE='23514'; END IF;
 IF NEW.current_stock<0 OR NEW.current_stock>1000000000 OR NEW.current_stock<>round(NEW.current_stock,3) OR NEW.minimum_threshold<0 OR NEW.minimum_threshold<>round(NEW.minimum_threshold,3) THEN RAISE EXCEPTION 'invalid_quantity' USING ERRCODE='23514';END IF;
 NEW.status:=CASE WHEN NEW.current_stock=0 THEN 'out_of_stock'::product_status WHEN NEW.current_stock<=NEW.minimum_threshold THEN 'low_stock'::product_status ELSE 'in_stock'::product_status END;
 RETURN NEW;
END $$;
--> statement-breakpoint
DROP TRIGGER IF EXISTS beautycore_inventory_stock_guard ON inventory;
--> statement-breakpoint
CREATE TRIGGER beautycore_inventory_stock_guard BEFORE INSERT OR UPDATE OR DELETE ON inventory FOR EACH ROW EXECUTE FUNCTION beautycore_inventory_guard();
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_inventory_post(p_id uuid,p_actor uuid,p_data jsonb) RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE i inventory%ROWTYPE;d inventory_details%ROWTYPE; prior inventory_transaction_details%ROWTYPE;t uuid;qty numeric;next_stock numeric;kind text:=p_data->>'kind';direction text:=p_data->>'direction';unit_name text;service text;ap uuid:=nullif(p_data->>'appointmentId','')::uuid;supplier uuid:=nullif(p_data->>'supplierId','')::uuid;request uuid:=(p_data->>'requestId')::uuid;actor_role text;cost numeric:=nullif(p_data->>'unitCost','')::numeric;
BEGIN
 SELECT role::text INTO actor_role FROM users WHERE id=p_actor AND is_active;
 IF actor_role IS NULL OR NOT (actor_role='admin' OR (actor_role='stylist' AND kind='service_consumption' AND current_setting('beautycore.consumption_appointment',true)=ap::text AND EXISTS(SELECT 1 FROM appointments WHERE id=ap AND stylist_id=p_actor AND status='completed'))) THEN RAISE EXCEPTION 'forbidden' USING ERRCODE='42501'; END IF;
 IF request IS NULL THEN RAISE EXCEPTION 'request_id_required' USING ERRCODE='22023';END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended('inventory-request:'||request::text,0));
 SELECT * INTO prior FROM inventory_transaction_details WHERE request_id=request;
 IF FOUND THEN
  IF prior.request_data IS DISTINCT FROM p_data OR NOT EXISTS(SELECT 1 FROM inventory_transactions WHERE id=prior.transaction_id AND inventory_id=p_id AND recorded_by=p_actor) THEN RAISE EXCEPTION 'request_conflict' USING ERRCODE='23514';END IF;RETURN prior.transaction_id;
 END IF;
 SELECT * INTO i FROM inventory WHERE id=p_id FOR UPDATE;IF NOT FOUND THEN RAISE EXCEPTION 'product_not_found' USING ERRCODE='23503';END IF;
 SELECT * INTO d FROM inventory_details WHERE inventory_id=p_id;unit_name:=coalesce(d.unit,'piece');
 IF kind NOT IN ('initial_stock','stock_in','stock_out','adjustment','service_consumption','correction','damaged','expired') OR kind IS NULL THEN RAISE EXCEPTION 'invalid_transaction' USING ERRCODE='22023';END IF;
 IF kind IN ('stock_out','adjustment','correction','damaged','expired') AND nullif(trim(p_data->>'reason'),'') IS NULL THEN RAISE EXCEPTION 'reason_required' USING ERRCODE='22023';END IF;
 IF kind='adjustment' THEN
  IF (p_data->>'previousQuantity')::numeric IS DISTINCT FROM i.current_stock THEN RAISE EXCEPTION 'stock_changed' USING ERRCODE='23514';END IF;
  next_stock:=beautycore_inventory_convert((p_data->>'adjustedQuantity')::numeric,coalesce(p_data->>'unit',unit_name),unit_name);
  qty:=abs(next_stock-i.current_stock);direction:=CASE WHEN next_stock>=i.current_stock THEN 'in' ELSE 'out' END;
 ELSE
  qty:=beautycore_inventory_convert((p_data->>'quantity')::numeric,coalesce(p_data->>'unit',unit_name),unit_name);
  IF direction NOT IN ('in','out') OR direction IS NULL THEN RAISE EXCEPTION 'invalid_direction' USING ERRCODE='22023';END IF;
  IF kind IN ('initial_stock','stock_in') AND direction<>'in' OR kind IN ('stock_out','service_consumption','damaged','expired') AND direction<>'out' THEN RAISE EXCEPTION 'invalid_direction' USING ERRCODE='22023';END IF;
  next_stock:=i.current_stock+CASE WHEN direction='in' THEN qty ELSE -qty END;
 END IF;
 IF qty IS NULL OR qty<0 OR qty>1000000 OR next_stock<0 THEN RAISE EXCEPTION 'insufficient_stock' USING ERRCODE='23514';END IF;
 IF qty=0 THEN
  IF kind<>'adjustment' THEN RAISE EXCEPTION 'Enter a positive transaction quantity' USING ERRCODE='22023';END IF;
  RETURN NULL;
 END IF;
 IF d.item_type='equipment' AND (qty<>trunc(qty) OR next_stock<>trunc(next_stock)) THEN RAISE EXCEPTION 'Equipment quantities must be whole numbers' USING ERRCODE='22023';END IF;
 IF kind='service_consumption' AND (coalesce(d.item_type,'consumable')='equipment' OR coalesce(d.active,true)=false OR d.expiration_date<(clock_timestamp() AT TIME ZONE 'Asia/Manila')::date) THEN RAISE EXCEPTION 'product_unavailable' USING ERRCODE='23514';END IF;
 IF supplier IS NOT NULL AND NOT EXISTS(SELECT 1 FROM inventory_suppliers WHERE id=supplier AND active) THEN RAISE EXCEPTION 'invalid_supplier' USING ERRCODE='23503';END IF;
 IF cost IS NOT NULL AND (cost<0 OR cost<>round(cost,2)) THEN RAISE EXCEPTION 'invalid_cost' USING ERRCODE='22023';END IF;
 IF ap IS NOT NULL THEN
  SELECT coalesce((SELECT service_id FROM appointment_services WHERE appointment_id=a.id),(SELECT id FROM salon_services WHERE name=a.service_name AND service_type=a.service_type)) INTO service FROM appointments a WHERE a.id=ap;
  IF NOT FOUND THEN RAISE EXCEPTION 'appointment_not_found' USING ERRCODE='23503';END IF;
  IF kind='correction' AND NOT EXISTS(SELECT 1 FROM appointments WHERE id=ap AND status='completed') THEN RAISE EXCEPTION 'Correction requires a completed service' USING ERRCODE='23514';END IF;
  IF kind='service_consumption' AND NOT EXISTS(SELECT 1 FROM appointments WHERE id=ap AND status='completed') THEN RAISE EXCEPTION 'Only completed services consume inventory' USING ERRCODE='23514';END IF;
  IF kind='correction' THEN
   IF d.item_type='equipment' THEN RAISE EXCEPTION 'Use an asset adjustment for reusable equipment' USING ERRCODE='22023';END IF;
   IF direction='in' AND qty>coalesce((SELECT sum(CASE WHEN t.direction='out' THEN t.quantity ELSE -t.quantity END) FROM inventory_transactions t JOIN inventory_transaction_details h ON h.transaction_id=t.id WHERE h.appointment_id=ap AND t.inventory_id=p_id AND h.kind IN ('service_consumption','correction')),0) THEN RAISE EXCEPTION 'Returned quantity exceeds recorded service consumption' USING ERRCODE='23514';END IF;
   IF cost IS NULL THEN cost:=CASE WHEN direction='in' THEN (SELECT h.unit_cost FROM inventory_transactions t JOIN inventory_transaction_details h ON h.transaction_id=t.id WHERE h.appointment_id=ap AND t.inventory_id=p_id AND h.kind='service_consumption' LIMIT 1) ELSE d.purchase_cost END;END IF;
  END IF;
 ELSIF kind IN ('service_consumption','correction') THEN RAISE EXCEPTION 'appointment_required' USING ERRCODE='22023';END IF;
 PERFORM set_config('beautycore.inventory_write','allowed',true);
 UPDATE inventory SET current_stock=next_stock,last_restocked=CASE WHEN direction='in' AND kind IN ('stock_in','initial_stock') THEN clock_timestamp() AT TIME ZONE 'UTC' ELSE last_restocked END WHERE id=p_id;
 IF kind='stock_in' AND cost IS NOT NULL THEN INSERT INTO inventory_details(inventory_id,purchase_cost,supplier_id) VALUES(p_id,cost,supplier) ON CONFLICT(inventory_id) DO UPDATE SET purchase_cost=EXCLUDED.purchase_cost,supplier_id=coalesce(EXCLUDED.supplier_id,inventory_details.supplier_id); END IF;
 INSERT INTO inventory_transactions(inventory_id,product_name,direction,quantity,stock_after,note,recorded_by) VALUES(p_id,i.product_name,direction,qty,next_stock,left(p_data->>'reason',500),p_actor) RETURNING id INTO t;
 INSERT INTO inventory_transaction_details(transaction_id,kind,previous_quantity,unit,unit_cost,supplier_id,supplier_name,reference,occurred_at,appointment_id,service_id,category,brand,reason,request_id,request_data)
 VALUES(t,kind,i.current_stock,unit_name,cost,supplier,(SELECT name FROM inventory_suppliers WHERE id=supplier),p_data->>'reference',coalesce(nullif(p_data->>'occurredAt','')::timestamptz,clock_timestamp()),ap,service,i.category,i.brand,p_data->>'reason',request,p_data);
 PERFORM set_config('beautycore.inventory_write','',true);
 RETURN t;
END $$;
--> statement-breakpoint
-- Keep the legacy integer-call signature; all arithmetic now delegates to the exact ledger.
CREATE OR REPLACE FUNCTION beautycore_inventory_move(p_id uuid,p_actor uuid,p_direction text,p_quantity integer,p_note text)
RETURNS TABLE(outcome text,stock integer,status product_status,last_restocked timestamp) LANGUAGE plpgsql AS $$
DECLARE t uuid;i inventory%ROWTYPE;
BEGIN
 IF NOT EXISTS(SELECT 1 FROM users WHERE id=p_actor AND role='admin' AND is_active) THEN RETURN QUERY SELECT 'forbidden',NULL::integer,NULL::product_status,NULL::timestamp;RETURN;END IF;
 SELECT * INTO i FROM inventory WHERE id=p_id FOR UPDATE;IF NOT FOUND THEN RETURN QUERY SELECT 'missing',NULL::integer,NULL::product_status,NULL::timestamp;RETURN;END IF;
 IF p_quantity<=0 OR p_quantity>1000000 OR p_direction NOT IN ('in','out') THEN RETURN QUERY SELECT 'invalid',NULL::integer,NULL::product_status,NULL::timestamp;RETURN;END IF;
 IF p_direction='out' AND p_quantity>i.current_stock THEN RETURN QUERY SELECT 'insufficient',CASE WHEN i.current_stock=trunc(i.current_stock) THEN i.current_stock::integer END,i.status,i.last_restocked;RETURN;END IF;
 t:=beautycore_inventory_post(p_id,p_actor,jsonb_build_object('kind',CASE WHEN p_direction='in' THEN 'stock_in' ELSE 'stock_out' END,'direction',p_direction,'quantity',p_quantity,'reason',coalesce(nullif(trim(p_note),''),'Legacy stock movement'),'requestId',gen_random_uuid()));
 SELECT * INTO i FROM inventory WHERE id=p_id;
 RETURN QUERY SELECT 'updated',CASE WHEN i.current_stock=trunc(i.current_stock) THEN i.current_stock::integer END,i.status,i.last_restocked;
END $$;
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_inventory_unit_guard() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 IF TG_OP='INSERT' THEN
  IF NOT EXISTS(SELECT 1 FROM inventory_details WHERE inventory_id=NEW.inventory_id) AND NEW.unit<>'piece' AND EXISTS(SELECT 1 FROM inventory_transactions WHERE inventory_id=NEW.inventory_id) THEN RAISE EXCEPTION 'Existing stock history uses the legacy count unit; create a separate item for a different unit' USING ERRCODE='23514';END IF;RETURN NEW;
 END IF;
 IF (NEW.unit,NEW.item_type) IS DISTINCT FROM (OLD.unit,OLD.item_type) AND (EXISTS(SELECT 1 FROM inventory_transactions WHERE inventory_id=OLD.inventory_id) OR EXISTS(SELECT 1 FROM service_inventory_requirements WHERE inventory_id=OLD.inventory_id)) THEN RAISE EXCEPTION 'Unit and product type are locked after stock history or service configuration; create a separate item instead' USING ERRCODE='23514'; END IF;RETURN NEW;END $$;
--> statement-breakpoint
DROP TRIGGER IF EXISTS inventory_unit_guard ON inventory_details;
--> statement-breakpoint
CREATE TRIGGER inventory_unit_guard BEFORE INSERT OR UPDATE ON inventory_details FOR EACH ROW EXECUTE FUNCTION beautycore_inventory_unit_guard();
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_inventory_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'Inventory history is immutable; record a correction transaction' USING ERRCODE='23514';END $$;
--> statement-breakpoint
DROP TRIGGER IF EXISTS inventory_ledger_guard ON inventory_transactions;
--> statement-breakpoint
CREATE TRIGGER inventory_ledger_guard BEFORE UPDATE OR DELETE ON inventory_transactions FOR EACH ROW EXECUTE FUNCTION beautycore_inventory_immutable();
--> statement-breakpoint
DROP TRIGGER IF EXISTS inventory_ledger_details_guard ON inventory_transaction_details;
--> statement-breakpoint
CREATE TRIGGER inventory_ledger_details_guard BEFORE UPDATE OR DELETE ON inventory_transaction_details FOR EACH ROW EXECUTE FUNCTION beautycore_inventory_immutable();
--> statement-breakpoint
DROP TRIGGER IF EXISTS inventory_consumption_guard ON inventory_service_consumption;
--> statement-breakpoint
CREATE TRIGGER inventory_consumption_guard BEFORE UPDATE OR DELETE ON inventory_service_consumption FOR EACH ROW EXECUTE FUNCTION beautycore_inventory_immutable();
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_inventory_save(p_actor uuid,p_id uuid,p_data jsonb) RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE i inventory%ROWTYPE;d inventory_details%ROWTYPE;item_id uuid:=p_id;initial numeric:=coalesce((p_data->>'currentStock')::numeric,0);new_unit text:=coalesce(p_data->>'unit','piece');new_type text:=coalesce(p_data->>'itemType','consumable');
BEGIN
 IF NOT EXISTS(SELECT 1 FROM users WHERE id=p_actor AND role='admin' AND is_active) THEN RAISE EXCEPTION 'forbidden' USING ERRCODE='42501';END IF;
 IF nullif(trim(p_data->>'productName'),'') IS NULL OR length(p_data->>'productName')>255 OR nullif(trim(p_data->>'category'),'') IS NULL OR length(p_data->>'category')>100 OR initial<0 OR initial>1000000 OR initial<>round(initial,3) THEN RAISE EXCEPTION 'Enter a valid product, category and opening quantity up to 1000000' USING ERRCODE='22023';END IF;
 IF p_id IS NULL THEN
  INSERT INTO inventory(product_name,brand,category,current_stock,minimum_threshold,unit_price) VALUES(p_data->>'productName',p_data->>'brand',p_data->>'category',0,(p_data->>'minimumThreshold')::numeric,NULL) RETURNING id INTO item_id;
 ELSE
  SELECT * INTO i FROM inventory WHERE id=p_id FOR UPDATE;IF NOT FOUND THEN RAISE EXCEPTION 'product_not_found' USING ERRCODE='23503';END IF;
  IF p_data ? 'currentStock' THEN RAISE EXCEPTION 'Use a stock transaction' USING ERRCODE='22023';END IF;
 END IF;
 INSERT INTO inventory_details(inventory_id,sku,item_type,description,unit,maximum_stock,purchase_cost,selling_price,supplier_id,location,expiration_date,active,image_data)
 VALUES(item_id,p_data->>'sku',new_type,p_data->>'description',new_unit,(p_data->>'maximumStock')::numeric,(p_data->>'purchaseCost')::numeric,(p_data->>'sellingPrice')::numeric,(p_data->>'supplierId')::uuid,p_data->>'location',(p_data->>'expirationDate')::date,coalesce((p_data->>'active')::boolean,true),p_data->>'image')
 ON CONFLICT(inventory_id) DO UPDATE SET sku=EXCLUDED.sku,item_type=EXCLUDED.item_type,description=EXCLUDED.description,unit=EXCLUDED.unit,maximum_stock=EXCLUDED.maximum_stock,purchase_cost=EXCLUDED.purchase_cost,selling_price=EXCLUDED.selling_price,supplier_id=EXCLUDED.supplier_id,location=EXCLUDED.location,expiration_date=EXCLUDED.expiration_date,active=EXCLUDED.active,image_data=CASE WHEN p_data ? 'image' THEN EXCLUDED.image_data ELSE inventory_details.image_data END;
 UPDATE inventory SET product_name=p_data->>'productName',brand=p_data->>'brand',category=p_data->>'category',minimum_threshold=(p_data->>'minimumThreshold')::numeric,
  unit_price=CASE WHEN (p_data->>'sellingPrice')::numeric=trunc((p_data->>'sellingPrice')::numeric) AND (p_data->>'sellingPrice')::numeric<=2147483647 THEN (p_data->>'sellingPrice')::integer ELSE NULL END WHERE id=item_id;
 IF new_type='equipment' AND (initial<>trunc(initial) OR EXISTS(SELECT 1 FROM inventory WHERE id=item_id AND current_stock<>trunc(current_stock))) THEN RAISE EXCEPTION 'Equipment quantities must be whole numbers' USING ERRCODE='22023';END IF;
 IF (p_data->>'maximumStock')::numeric<(p_data->>'minimumThreshold')::numeric THEN RAISE EXCEPTION 'Maximum stock must be at least the minimum' USING ERRCODE='22023';END IF;
 IF p_id IS NULL AND initial>0 THEN PERFORM beautycore_inventory_post(item_id,p_actor,jsonb_build_object('kind','initial_stock','direction','in','quantity',initial,'unit',new_unit,'unitCost',p_data->>'purchaseCost','supplierId',p_data->>'supplierId','reason','Opening stock','requestId',gen_random_uuid()));END IF;
 RETURN item_id;
END $$;
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_inventory_requirements(p_actor uuid,p_service text,p_rows jsonb) RETURNS void LANGUAGE plpgsql AS $$
DECLARE row jsonb;d inventory_details%ROWTYPE;
BEGIN
 IF NOT EXISTS(SELECT 1 FROM users WHERE id=p_actor AND role='admin' AND is_active) THEN RAISE EXCEPTION 'forbidden' USING ERRCODE='42501';END IF;
 IF NOT EXISTS(SELECT 1 FROM salon_services WHERE id=p_service AND active) OR jsonb_typeof(p_rows)<>'array' OR jsonb_array_length(p_rows)>40 THEN RAISE EXCEPTION 'invalid_requirements' USING ERRCODE='22023';END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended('inventory-service:'||p_service,0));
 FOR row IN SELECT value FROM jsonb_array_elements(p_rows) LOOP
  PERFORM id FROM inventory WHERE id=(row->>'inventoryId')::uuid FOR KEY SHARE;IF NOT FOUND THEN RAISE EXCEPTION 'product_not_found' USING ERRCODE='23503';END IF;
  SELECT * INTO d FROM inventory_details WHERE inventory_id=(row->>'inventoryId')::uuid;
  IF d.active=false THEN RAISE EXCEPTION 'Configure active products only' USING ERRCODE='22023';END IF;
 END LOOP;
 DELETE FROM service_inventory_requirements WHERE service_id=p_service;
 FOR row IN SELECT value FROM jsonb_array_elements(p_rows) LOOP
  SELECT * INTO d FROM inventory_details WHERE inventory_id=(row->>'inventoryId')::uuid;
  INSERT INTO service_inventory_requirements VALUES(p_service,(row->>'inventoryId')::uuid,beautycore_inventory_convert((row->>'quantity')::numeric,coalesce(row->>'unit',d.unit,'piece'),coalesce(d.unit,'piece')));
 END LOOP;
END $$;

--> statement-breakpoint


CREATE OR REPLACE FUNCTION beautycore_complete_appointment_record(p_id uuid,p_actor uuid,p_role text,p_products jsonb)
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
 IF jsonb_typeof(p_products) IS DISTINCT FROM 'array' OR jsonb_array_length(p_products)>100 THEN
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
CREATE OR REPLACE FUNCTION beautycore_complete_appointment(p_id uuid,p_actor uuid,p_role text,p_products jsonb)
RETURNS TABLE(outcome text) LANGUAGE plpgsql AS $$
DECLARE a appointments%ROWTYPE;service text;policy text;mode text;row record;actual jsonb;qty numeric;available numeric;deduct numeric;missing numeric;plan jsonb:='[]'::jsonb;products jsonb:='[]'::jsonb;line jsonb;result text;reason text;
BEGIN
 SELECT * INTO a FROM appointments WHERE id=p_id FOR UPDATE;
 IF NOT FOUND OR NOT EXISTS(SELECT 1 FROM users WHERE id=p_actor AND role::text=p_role AND is_active) OR NOT coalesce(p_role='admin' OR (p_role='stylist' AND a.stylist_id=p_actor),false) THEN RETURN QUERY SELECT 'not_found';RETURN;END IF;
 IF a.status='completed' THEN RETURN QUERY SELECT 'existing';RETURN;END IF;
 IF a.status IN ('cancelled','no_show') THEN RETURN QUERY SELECT 'terminal';RETURN;END IF;
 IF a.stylist_id IS NULL THEN RETURN QUERY SELECT 'unassigned';RETURN;END IF;
 IF jsonb_typeof(p_products) IS DISTINCT FROM 'array' OR jsonb_array_length(p_products)>50 THEN RAISE EXCEPTION 'Invalid product records' USING ERRCODE='22023';END IF;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(p_products) v WHERE v->>'inventoryId' IS NOT NULL GROUP BY v->>'inventoryId' HAVING count(*)>1) THEN RETURN QUERY SELECT 'duplicate_product';RETURN;END IF;
 SELECT coalesce((SELECT service_id FROM appointment_services WHERE appointment_id=p_id),(SELECT id FROM salon_services WHERE name=a.service_name AND service_type=a.service_type)) INTO service;
 IF service IS NOT NULL THEN PERFORM pg_advisory_xact_lock(hashtextextended('inventory-service:'||service,0));END IF;
 SELECT shortage_policy,consumption_mode INTO policy,mode FROM inventory_policy WHERE id=true FOR SHARE;
 PERFORM i.id FROM inventory i WHERE (mode='configured' AND EXISTS(SELECT 1 FROM service_inventory_requirements r WHERE r.service_id=service AND r.inventory_id=i.id))
  OR EXISTS(SELECT 1 FROM jsonb_array_elements(p_products) v WHERE v->>'inventoryId'=i.id::text AND v->>'consumeStock'='true') ORDER BY i.id FOR UPDATE;
 FOR row IN SELECT i.*,coalesce(d.unit,'piece') AS stock_unit,coalesce(d.item_type,'consumable') AS item_type,coalesce(d.active,true) AS active,d.expiration_date,d.purchase_cost,r.quantity AS estimate
  FROM inventory i LEFT JOIN inventory_details d ON d.inventory_id=i.id LEFT JOIN service_inventory_requirements r ON r.inventory_id=i.id AND r.service_id=service
  WHERE (mode='configured' AND r.inventory_id IS NOT NULL) OR EXISTS(SELECT 1 FROM jsonb_array_elements(p_products) v WHERE v->>'inventoryId'=i.id::text AND v->>'consumeStock'='true') ORDER BY i.id LOOP
  SELECT value INTO actual FROM jsonb_array_elements(p_products) WHERE value->>'inventoryId'=row.id::text;
  IF actual IS NOT NULL AND actual->>'quantity' IS NOT NULL THEN
   qty:=beautycore_inventory_convert((actual->>'quantity')::numeric,coalesce(actual->>'unit',row.stock_unit),row.stock_unit);
  ELSE qty:=CASE WHEN mode='configured' THEN row.estimate END;END IF;
  reason:=nullif(trim(actual->>'adjustmentReason'),'');
  IF qty IS NULL THEN RETURN QUERY SELECT 'invalid_quantity';RETURN;END IF;
  IF mode='reported_only' THEN
   IF row.item_type='equipment' THEN RETURN QUERY SELECT 'equipment_not_consumable';RETURN;END IF;
   IF qty<=0 THEN RETURN QUERY SELECT 'invalid_quantity';RETURN;END IF;
   reason:=coalesce(reason,'Reported used-up supply after service');
  ELSIF (row.estimate IS NULL OR qty IS DISTINCT FROM row.estimate) AND reason IS NULL THEN RETURN QUERY SELECT 'adjustment_reason';RETURN;END IF;
  available:=CASE WHEN NOT row.active OR row.expiration_date<(clock_timestamp() AT TIME ZONE 'Asia/Manila')::date THEN 0 ELSE row.current_stock END;
  missing:=greatest(qty-available,0);
  IF missing>0 AND coalesce(policy,'block')='block' THEN RETURN QUERY SELECT 'inventory_shortage';RETURN;END IF;
  deduct:=CASE WHEN row.item_type='equipment' THEN 0 ELSE least(qty,available) END;
  plan:=plan||jsonb_build_array(jsonb_build_object('inventoryId',row.id,'productName',row.product_name,'brand',row.brand,'unit',row.stock_unit,'unitCost',row.purchase_cost,'configuredQuantity',row.estimate,'requestedQuantity',qty,'deductedQuantity',deduct,'shortage',missing,'equipment',row.item_type='equipment','reason',reason));
  IF (row.item_type='equipment' AND qty>0) OR deduct>0 THEN
   products:=products||jsonb_build_array(jsonb_build_object('inventoryId',row.id,'productName',row.product_name,'brand',row.brand,'quantity',CASE WHEN row.item_type='equipment' THEN qty ELSE deduct END,'unit',row.stock_unit,'unitCost',CASE WHEN row.item_type='equipment' THEN NULL ELSE row.purchase_cost END));
  END IF;
 END LOOP;
 -- Untracked notes keep their legacy meaning. A stock deduction requires a configured requirement or explicit consumeStock.
 FOR line IN SELECT value FROM jsonb_array_elements(p_products) LOOP
  IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(plan) x WHERE x->>'inventoryId'=line->>'inventoryId') THEN products:=products||jsonb_build_array(line);END IF;
 END LOOP;
 PERFORM set_config('beautycore.inventory_completion',p_id::text,true);
 SELECT x.outcome INTO result FROM beautycore_complete_appointment_record(p_id,p_actor,p_role,products) x;
 IF result<>'completed' THEN PERFORM set_config('beautycore.inventory_completion','',true);RETURN QUERY SELECT result;RETURN;END IF;
 PERFORM set_config('beautycore.consumption_appointment',p_id::text,true);
 FOR line IN SELECT value FROM jsonb_array_elements(plan) LOOP
  INSERT INTO inventory_service_consumption(appointment_id,inventory_id,service_id,product_name,unit,configured_quantity,requested_quantity,deducted_quantity,shortage,equipment,reason,recorded_by)
   VALUES(p_id,(line->>'inventoryId')::uuid,service,line->>'productName',line->>'unit',(line->>'configuredQuantity')::numeric,(line->>'requestedQuantity')::numeric,(line->>'deductedQuantity')::numeric,(line->>'shortage')::numeric,(line->>'equipment')::boolean,line->>'reason',p_actor);
  IF (line->>'deductedQuantity')::numeric>0 THEN
   PERFORM beautycore_inventory_post((line->>'inventoryId')::uuid,p_actor,jsonb_build_object('kind','service_consumption','direction','out','quantity',(line->>'deductedQuantity')::numeric,'unit',line->>'unit','unitCost',line->>'unitCost','reason',coalesce(line->>'reason','Configured usage for completed service'),'appointmentId',p_id,'requestId',gen_random_uuid()));
  END IF;
 END LOOP;
 PERFORM set_config('beautycore.consumption_appointment','',true);
 PERFORM set_config('beautycore.inventory_completion','',true);
 RETURN QUERY SELECT 'completed';
END $$;
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_inventory_completion_guard() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 IF NEW.status='completed' AND OLD.status<>'completed' AND current_setting('beautycore.inventory_completion',true) IS DISTINCT FROM NEW.id::text
  AND EXISTS(SELECT 1 FROM service_inventory_requirements r WHERE r.service_id=coalesce((SELECT service_id FROM appointment_services WHERE appointment_id=NEW.id),(SELECT id FROM salon_services WHERE name=NEW.service_name AND service_type=NEW.service_type)))
 THEN RAISE EXCEPTION 'Complete configured services through the inventory-aware workflow' USING ERRCODE='23514';END IF;
 RETURN NEW;
END $$;
--> statement-breakpoint
DROP TRIGGER IF EXISTS inventory_completion_guard ON appointments;
--> statement-breakpoint
CREATE TRIGGER inventory_completion_guard BEFORE UPDATE OF status ON appointments FOR EACH ROW EXECUTE FUNCTION beautycore_inventory_completion_guard();
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_inventory_archive(p_id uuid,p_actor uuid) RETURNS text LANGUAGE plpgsql AS $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM users WHERE id=p_actor AND role='admin' AND is_active) THEN RAISE EXCEPTION 'forbidden' USING ERRCODE='42501';END IF;
 PERFORM id FROM inventory WHERE id=p_id FOR UPDATE;IF NOT FOUND THEN RAISE EXCEPTION 'product_not_found' USING ERRCODE='23503';END IF;
 IF EXISTS(SELECT 1 FROM inventory_transactions WHERE inventory_id=p_id) OR EXISTS(SELECT 1 FROM appointment_product_usage WHERE inventory_id=p_id) OR EXISTS(SELECT 1 FROM service_inventory_requirements WHERE inventory_id=p_id) OR EXISTS(SELECT 1 FROM inventory_service_consumption WHERE inventory_id=p_id) THEN
  INSERT INTO inventory_details(inventory_id,active) VALUES(p_id,false) ON CONFLICT(inventory_id) DO UPDATE SET active=false;RETURN 'archived';
 END IF;
 DELETE FROM inventory WHERE id=p_id;RETURN 'removed';
END $$;


--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_create_inventory_item(p_name text,p_brand text,p_category text,p_stock integer,p_threshold integer,p_price integer,p_actor uuid)
RETURNS TABLE(id uuid,product_name text,brand text,category text,current_stock integer,minimum_threshold integer,unit_price integer,status product_status,last_restocked timestamp,created_at timestamp) LANGUAGE plpgsql AS $$
DECLARE item_id uuid;BEGIN
 item_id:=beautycore_inventory_save(p_actor,NULL,jsonb_build_object('productName',p_name,'brand',p_brand,'category',p_category,'currentStock',p_stock,'minimumThreshold',p_threshold,'sellingPrice',p_price,'unit','piece','itemType','consumable','active',true));
 UPDATE inventory SET unit_price=p_price WHERE inventory.id=item_id;
 RETURN QUERY SELECT i.id,i.product_name::text,i.brand::text,i.category::text,i.current_stock::integer,i.minimum_threshold::integer,i.unit_price,i.status,i.last_restocked,i.created_at FROM inventory i WHERE i.id=item_id;
END $$;

--> statement-breakpoint
CREATE INDEX IF NOT EXISTS inventory_requirements_product_idx ON service_inventory_requirements(inventory_id);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS inventory_consumption_product_idx ON inventory_service_consumption(inventory_id);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS inventory_transaction_appointment_idx ON inventory_transaction_details(appointment_id);
