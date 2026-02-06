ALTER TABLE public.events
  ADD COLUMN api_key_id uuid REFERENCES public.api_keys(id) ON DELETE SET NULL;

CREATE INDEX idx_events_api_key_id ON public.events(api_key_id);
