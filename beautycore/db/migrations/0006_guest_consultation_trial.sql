-- Durable anonymous allowance only: no image, chat content or account rows.
CREATE TABLE IF NOT EXISTS ai_guest_trials (
 token_hash text PRIMARY KEY CHECK (token_hash ~ '^[a-f0-9]{64}$'),
 owner_id text NOT NULL UNIQUE CHECK (owner_id ~ '^guest_[a-f0-9]{32}$'),
 network_tag text NOT NULL CHECK (network_tag ~ '^[a-f0-9]{64}$'),
 created_at timestamptz NOT NULL DEFAULT now(), expires_at timestamptz NOT NULL,
 updated_at timestamptz NOT NULL DEFAULT now(),
 state text NOT NULL DEFAULT 'available' CHECK (state IN ('available','reserved','spent')),
 counters jsonb NOT NULL DEFAULT '{}'::jsonb, operation_id uuid,
 consultation_id uuid, consultation_expires_at timestamptz,
 recommendation_id text, job_id uuid, attempt_at timestamptz
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS ai_guest_trials_network_created_idx ON ai_guest_trials(network_tag,created_at);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS ai_guest_trials_updated_idx ON ai_guest_trials(updated_at);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS ai_guest_trials_attempt_idx ON ai_guest_trials(attempt_at) WHERE attempt_at IS NOT NULL;
--> statement-breakpoint
CREATE OR REPLACE FUNCTION beautycore_guest_trial(
 p_action text, p_hash text, p_network text, p_data jsonb DEFAULT '{}'::jsonb
) RETURNS jsonb LANGUAGE plpgsql SET search_path=public,pg_temp AS $$
DECLARE v ai_guest_trials%ROWTYPE; k text; cap integer; n integer;
BEGIN
 IF p_hash !~ '^[a-f0-9]{64}$' THEN RETURN jsonb_build_object('ok',false,'code','invalid'); END IF;
 IF p_action='status' THEN
  SELECT * INTO v FROM ai_guest_trials WHERE token_hash=p_hash AND expires_at>now();
  IF NOT FOUND THEN RETURN jsonb_build_object('ok',false,'code','missing'); END IF;
  RETURN jsonb_build_object('ok',true,'trial',to_jsonb(v));
 END IF;
 -- Only short DB admissions are serialized. No external work runs in this transaction.
 IF p_action IN ('issue','prepare') THEN PERFORM pg_advisory_xact_lock(71623003); END IF;
 SELECT * INTO v FROM ai_guest_trials WHERE token_hash=p_hash FOR UPDATE;
 IF p_action='issue' THEN
  IF FOUND AND v.expires_at>now() THEN RETURN jsonb_build_object('ok',true,'trial',to_jsonb(v)); END IF;
  IF p_network IS NULL OR p_network !~ '^[a-f0-9]{64}$' THEN RETURN jsonb_build_object('ok',false,'code','network'); END IF;
  SELECT count(*) INTO n FROM ai_guest_trials WHERE network_tag=p_network AND created_at>now()-interval '1 day';
  IF n>=least(10,greatest(1,coalesce((p_data->>'network_limit')::int,2))) THEN RETURN jsonb_build_object('ok',false,'code','network_limit'); END IF;
  SELECT count(*) INTO n FROM ai_guest_trials WHERE created_at>now()-interval '1 day';
  IF n>=least(100,greatest(1,coalesce((p_data->>'daily_limit')::int,12))) THEN RETURN jsonb_build_object('ok',false,'code','daily_limit'); END IF;
  DELETE FROM ai_guest_trials WHERE expires_at<now()-interval '1 day';
  INSERT INTO ai_guest_trials(token_hash,owner_id,network_tag,expires_at)
   VALUES(p_hash,'guest_'||replace(gen_random_uuid()::text,'-',''),p_network,
    now()+least(90,greatest(1,coalesce((p_data->>'days')::int,30)))*interval '1 day') RETURNING * INTO v;
  RETURN jsonb_build_object('ok',true,'trial',to_jsonb(v));
 END IF;
 IF v.token_hash IS NULL OR v.expires_at<=now() THEN RETURN jsonb_build_object('ok',false,'code','missing'); END IF;
 IF p_action='finish' THEN
  IF v.operation_id IS NULL OR v.operation_id IS DISTINCT FROM (p_data->>'operation_id')::uuid THEN RETURN jsonb_build_object('ok',false,'code','conflict'); END IF;
  IF p_data->>'kind'='create' AND p_data ? 'consultation_id' THEN
   v.consultation_id:=(p_data->>'consultation_id')::uuid; v.consultation_expires_at:=(p_data->>'consultation_expires_at')::timestamptz;
  END IF;
  IF p_data->>'kind'='generation' THEN
   IF p_data->>'release'='busy' THEN
    v.state:='available'; v.recommendation_id:=NULL; v.attempt_at:=NULL;
   ELSIF p_data ? 'job_id' THEN v.state:='spent'; v.job_id:=(p_data->>'job_id')::uuid;
   END IF;
  END IF;
  UPDATE ai_guest_trials SET operation_id=NULL,state=v.state,job_id=v.job_id,
   recommendation_id=v.recommendation_id,attempt_at=v.attempt_at,
   consultation_id=v.consultation_id,consultation_expires_at=v.consultation_expires_at,
   updated_at=now() WHERE token_hash=p_hash RETURNING * INTO v;
  RETURN jsonb_build_object('ok',true,'trial',to_jsonb(v));
 END IF;
 IF p_action<>'prepare' THEN RETURN jsonb_build_object('ok',false,'code','invalid'); END IF;
 k:=p_data->>'kind';
 IF k NOT IN ('create','photo','state','turn','recommendations','generation') OR k IS NULL THEN RETURN jsonb_build_object('ok',false,'code','invalid'); END IF;
 IF k<>'create' AND (v.consultation_id IS NULL OR v.consultation_id::text IS DISTINCT FROM p_data->>'consultation_id') THEN RETURN jsonb_build_object('ok',false,'code','ownership'); END IF;
 IF k='generation' AND v.state<>'available' THEN
  IF v.recommendation_id=p_data->>'recommendation_id' AND v.job_id IS NOT NULL THEN RETURN jsonb_build_object('ok',true,'replay',true,'trial',to_jsonb(v)); END IF;
  RETURN jsonb_build_object('ok',false,'code','spent');
 END IF;
 IF v.state<>'available' THEN RETURN jsonb_build_object('ok',false,'code','spent'); END IF;
 IF v.operation_id IS NOT NULL THEN RETURN jsonb_build_object('ok',false,'code','in_progress'); END IF;
 cap:=CASE k WHEN 'create' THEN 2 WHEN 'photo' THEN 2 WHEN 'state' THEN 4 WHEN 'turn' THEN 6 WHEN 'recommendations' THEN 2 ELSE 8 END;
 IF coalesce((v.counters->>k)::int,0)>=cap THEN RETURN jsonb_build_object('ok',false,'code','activity_limit'); END IF;
 IF k IN ('create','turn','recommendations') THEN
  SELECT coalesce(sum(coalesce((counters->>k)::int,0)),0) INTO n FROM ai_guest_trials WHERE updated_at>now()-interval '1 day';
  IF n>=(CASE k WHEN 'create' THEN 6 WHEN 'turn' THEN 24 ELSE 12 END) THEN RETURN jsonb_build_object('ok',false,'code','capacity'); END IF;
 END IF;
 IF k='generation' THEN
  SELECT count(*) INTO n FROM ai_guest_trials WHERE attempt_at>now()-interval '1 day';
  IF n>=least(50,greatest(1,coalesce((p_data->>'generation_limit')::int,4))) THEN RETURN jsonb_build_object('ok',false,'code','capacity'); END IF;
  v.state:='reserved'; v.recommendation_id:=p_data->>'recommendation_id'; v.attempt_at:=now();
 END IF;
 UPDATE ai_guest_trials SET operation_id=(p_data->>'operation_id')::uuid,
  counters=jsonb_set(counters,ARRAY[k],to_jsonb(coalesce((counters->>k)::int,0)+1)),
  state=v.state,recommendation_id=v.recommendation_id,attempt_at=v.attempt_at,
  consultation_id=CASE WHEN k='create' THEN NULL ELSE consultation_id END,
  consultation_expires_at=CASE WHEN k='create' THEN NULL ELSE consultation_expires_at END,
  updated_at=now() WHERE token_hash=p_hash RETURNING * INTO v;
 RETURN jsonb_build_object('ok',true,'trial',to_jsonb(v));
END;
$$;
