-- Create shared_traces table for public trace sharing
CREATE TABLE IF NOT EXISTS shared_traces (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  trace_id TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  expires_at TIMESTAMPTZ,
  UNIQUE(team_id, trace_id)
);

CREATE INDEX IF NOT EXISTS idx_shared_traces_slug ON shared_traces(slug);
