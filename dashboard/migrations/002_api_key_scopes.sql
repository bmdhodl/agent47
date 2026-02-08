-- Add scope column to api_keys for read/write permission separation
DO $$ BEGIN
  CREATE TYPE api_key_scope AS ENUM ('ingest', 'read', 'full');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS scope api_key_scope NOT NULL DEFAULT 'full';
