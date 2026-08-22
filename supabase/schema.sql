-- Paste into Supabase → SQL Editor → Run (once, and again after schema changes).

create table if not exists public.job_status (
  user_id uuid not null references auth.users (id) on delete cascade,
  url text not null,
  state text not null check (state in ('applied', 'hidden', 'flagged')),
  updated_at timestamptz not null default now(),
  primary key (user_id, url)
);

alter table public.job_status drop constraint if exists job_status_state_check;
alter table public.job_status
  add constraint job_status_state_check
  check (state in ('applied', 'hidden', 'flagged'));

alter table public.job_status enable row level security;

drop policy if exists "job_status_own" on public.job_status;
create policy "job_status_own"
  on public.job_status
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
