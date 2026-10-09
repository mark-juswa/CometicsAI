-- Additive operational metadata only. No business tables, users, images or secrets are modified.
CREATE TABLE IF NOT EXISTS ai_runtime_endpoints (
  slot text PRIMARY KEY CHECK (slot = 'primary'),
  session_id uuid NOT NULL,
  endpoint varchar(256) NOT NULL CHECK (endpoint ~ '^https://[a-z0-9-]+[.]trycloudflare[.]com$'),
  started_at bigint NOT NULL CHECK (started_at > 0),
  last_issued_at bigint NOT NULL CHECK (last_issued_at >= started_at),
  lease_expires_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);
