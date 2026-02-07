ALTER TABLE public.events ADD COLUMN cost_usd double precision;

CREATE INDEX idx_events_cost ON public.events(team_id, created_at) WHERE cost_usd IS NOT NULL;
