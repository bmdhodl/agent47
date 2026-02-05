-- Teams (auto-created on signup via trigger)
create table public.teams (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  owner_id uuid not null references auth.users(id) on delete cascade,
  plan text not null default 'free' check (plan in ('free', 'pro', 'team')),
  stripe_customer_id text,
  stripe_subscription_id text,
  created_at timestamptz not null default now()
);
alter table public.teams enable row level security;

-- API Keys (hashed, only prefix shown after creation)
create table public.api_keys (
  id uuid primary key default gen_random_uuid(),
  team_id uuid not null references public.teams(id) on delete cascade,
  key_hash text not null,
  prefix text not null,
  name text not null default 'Default',
  created_at timestamptz not null default now(),
  revoked_at timestamptz
);
alter table public.api_keys enable row level security;
create unique index idx_api_keys_hash on public.api_keys(key_hash) where revoked_at is null;

-- Events (trace data from HttpSink)
create table public.events (
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
alter table public.events enable row level security;
create index idx_events_team_trace on public.events(team_id, trace_id);
create index idx_events_team_created on public.events(team_id, created_at desc);
create index idx_events_trace_id on public.events(trace_id);

-- Usage tracking (monthly event counts)
create table public.usage (
  team_id uuid not null references public.teams(id) on delete cascade,
  month text not null,
  event_count bigint not null default 0,
  primary key (team_id, month)
);
alter table public.usage enable row level security;

-- RLS Policies: Teams
create policy "Users can read own team"
  on public.teams for select
  using (owner_id = auth.uid());

create policy "Users can update own team"
  on public.teams for update
  using (owner_id = auth.uid());

-- RLS Policies: API Keys
create policy "Team owner can manage keys"
  on public.api_keys for all
  using (team_id in (select id from public.teams where owner_id = auth.uid()));

-- RLS Policies: Events
create policy "Team owner can read events"
  on public.events for select
  using (team_id in (select id from public.teams where owner_id = auth.uid()));

-- RLS Policies: Usage
create policy "Team owner can read usage"
  on public.usage for select
  using (team_id in (select id from public.teams where owner_id = auth.uid()));

-- Auto-create team on user signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.teams (name, owner_id, plan)
  values (
    coalesce(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1)),
    new.id,
    'free'
  );
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- Usage increment RPC (atomic upsert)
create or replace function public.increment_usage(
  p_team_id uuid,
  p_month text,
  p_count bigint
) returns void as $$
begin
  insert into public.usage (team_id, month, event_count)
  values (p_team_id, p_month, p_count)
  on conflict (team_id, month)
  do update set event_count = public.usage.event_count + p_count;
end;
$$ language plpgsql security definer;

-- Trace summary view
create view public.trace_summary as
select
  team_id,
  trace_id,
  min(ts) as started_at,
  max(duration_ms) as total_duration_ms,
  count(*) as event_count,
  count(*) filter (where error is not null) as error_count,
  max(name) filter (where parent_id is null and phase = 'start') as root_name,
  max(service) as service
from public.events
group by team_id, trace_id;

-- Retention cleanup RPC
create or replace function public.delete_expired_events(
  p_plan text,
  p_cutoff timestamptz
) returns bigint as $$
declare
  deleted_count bigint;
begin
  with deleted as (
    delete from public.events
    where team_id in (select id from public.teams where plan = p_plan)
      and created_at < p_cutoff
    returning 1
  )
  select count(*) into deleted_count from deleted;
  return deleted_count;
end;
$$ language plpgsql security definer;
