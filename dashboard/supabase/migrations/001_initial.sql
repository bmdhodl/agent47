-- Users (managed by app, not Supabase Auth)
create table if not exists public.users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  password_hash text not null,
  created_at timestamptz not null default now()
);

-- Teams (created on signup)
create table if not exists public.teams (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  owner_id uuid not null references public.users(id) on delete cascade,
  plan text not null default 'free' check (plan in ('free', 'pro', 'team')),
  stripe_customer_id text,
  stripe_subscription_id text,
  created_at timestamptz not null default now()
);

-- API Keys (hashed, only prefix shown after creation)
create table if not exists public.api_keys (
  id uuid primary key default gen_random_uuid(),
  team_id uuid not null references public.teams(id) on delete cascade,
  key_hash text not null,
  prefix text not null,
  name text not null default 'Default',
  created_at timestamptz not null default now(),
  revoked_at timestamptz
);
create unique index if not exists idx_api_keys_hash on public.api_keys(key_hash) where revoked_at is null;

-- Events (trace data from HttpSink)
create table if not exists public.events (
  id bigint generated always as identity primary key,
  team_id uuid not null references public.teams(id) on delete cascade,
  trace_id text not null,
  span_id text not null,
  parent_id text,
  kind text not null,
  phase text not null,
  name text not null,
  ts double precision not null,
  duration_ms double precision,
  data jsonb not null default '{}',
  error jsonb,
  service text not null default 'app',
  created_at timestamptz not null default now()
);
create index if not exists idx_events_team_trace on public.events(team_id, trace_id);
create index if not exists idx_events_team_created on public.events(team_id, created_at desc);
create index if not exists idx_events_trace_id on public.events(trace_id);

-- Usage tracking (monthly event counts)
create table if not exists public.usage (
  team_id uuid not null references public.teams(id) on delete cascade,
  month text not null,
  event_count bigint not null default 0,
  primary key (team_id, month)
);
