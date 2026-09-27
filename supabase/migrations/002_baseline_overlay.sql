-- Migration 002: AEC baseline and firm overlay.
-- For a database created from an earlier schema.sql. Run once in the Supabase
-- SQL editor. (A fresh install gets all of this from schema.sql and seed.sql.)

begin;

create type override_status as enum ('proposed', 'confirmed', 'dismissed');

alter table firms add column is_baseline boolean not null default false;

-- ---------------------------------------------------------------------------
-- AEC baseline and firm overlay
-- ---------------------------------------------------------------------------
-- The baseline is the one firm row with is_baseline = true. Its manual,
-- modules, and passages use the tables above and are shared by every firm.
-- Each firm's choices about baseline content live in the tables below, and a
-- firm passage can override a baseline passage: the firm's version wins.

create unique index firms_one_baseline on firms (is_baseline) where is_baseline;

-- A firm's settings for a baseline module. No row means the baseline defaults.
create table firm_baseline_modules (
  id          uuid primary key default gen_random_uuid(),
  firm_id     uuid not null references firms (id) on delete cascade,
  module_id   uuid not null references modules (id) on delete cascade,
  priority    module_priority,  -- null = baseline default
  is_required boolean,          -- null = baseline default
  ordinal     integer,          -- null = after the firm's own modules
  is_hidden   boolean not null default false,
  updated_at  timestamptz not null default now(),
  unique (firm_id, module_id)
);

-- Baseline passages a firm marks critical for its final check.
create table firm_baseline_passages (
  id          uuid primary key default gen_random_uuid(),
  firm_id     uuid not null references firms (id) on delete cascade,
  passage_id  uuid not null references module_passages (id) on delete cascade,
  is_critical boolean not null default false,
  unique (firm_id, passage_id)
);

-- A firm passage that states a different practice than a baseline passage.
-- Proposed by the AI with verbatim excerpts; the firm admin confirms.
create table baseline_overrides (
  id                  uuid primary key default gen_random_uuid(),
  firm_id             uuid not null references firms (id) on delete cascade,
  manual_id           uuid references manuals (id) on delete cascade,
  firm_passage_id     uuid not null references module_passages (id) on delete cascade,
  baseline_passage_id uuid not null references module_passages (id) on delete cascade,
  firm_excerpt        text not null,
  baseline_excerpt    text not null,
  difference          text not null,  -- for the admin; employees see a fixed note
  status              override_status not null default 'proposed',
  reviewed_by         uuid references profiles (id) on delete set null,
  reviewed_at         timestamptz,
  created_at          timestamptz not null default now(),
  unique (firm_passage_id, baseline_passage_id)
);

create index on baseline_overrides (firm_id, status);
create index on baseline_overrides (baseline_passage_id);

alter table firm_baseline_modules  enable row level security;
alter table firm_baseline_passages enable row level security;
alter table baseline_overrides     enable row level security;

-- The shared AEC baseline (see supabase/seed.sql).
insert into firms (id, name, slug, is_baseline) values
  ('b0000000-0000-4000-8000-000000000001', 'FIRM FLOW AEC Baseline', 'firmflow-baseline', true)
on conflict (id) do nothing;

commit;
