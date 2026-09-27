-- FIRM FLOW schema
-- Run in the Supabase SQL editor, then run seed.sql.
--
-- RLS is enabled on every table with no policies: only the backend (service
-- role key) reads and writes data. The frontend uses Supabase only for auth.

-- ---------------------------------------------------------------------------
-- Enums
-- ---------------------------------------------------------------------------

create type user_role        as enum ('admin', 'employee');
create type manual_status    as enum ('uploaded', 'processing', 'processed', 'failed');
create type file_type        as enum ('pdf', 'docx');
create type review_status    as enum ('draft', 'approved', 'rejected');
create type module_priority  as enum ('day_1', 'week_1', 'later');
create type passage_kind     as enum ('text', 'steps', 'checklist', 'summary');
create type issue_type       as enum ('broken_link', 'outdated_reference', 'contradiction', 'missing_step');
create type issue_status     as enum ('open', 'resolved', 'dismissed');
create type progress_status  as enum ('not_started', 'in_progress', 'completed');
create type question_type    as enum ('multiple_choice', 'scenario');
create type attempt_status   as enum ('in_progress', 'completed');
create type chat_intent      as enum ('where_is', 'who_can_help', 'personal_matter', 'other');
create type override_status  as enum ('proposed', 'confirmed', 'dismissed');
create type project_role     as enum (
  'principal_in_charge',
  'project_manager',
  'design_manager',
  'project_architect',
  'bim_lead',
  'designer',
  'intern'
);

-- ---------------------------------------------------------------------------
-- Firm and directory
-- ---------------------------------------------------------------------------

create table firms (
  id                 uuid primary key default gen_random_uuid(),
  name               text not null,
  slug               text not null unique,
  timezone           text not null default 'America/Los_Angeles',
  default_contact_id uuid,  -- fk added after people exists
  is_baseline        boolean not null default false,  -- the shared AEC baseline, not a real firm
  created_at         timestamptz not null default now()
);

-- The firm's staff directory. The assistant looks people up here through tool
-- calls; names and emails are never generated.
create table people (
  id                  uuid primary key default gen_random_uuid(),
  firm_id             uuid not null references firms (id) on delete cascade,
  full_name           text not null,
  title               text not null,
  department          text not null,
  email               text not null,
  phone_ext           text,
  work_days           smallint[] not null default '{1,2,3,4,5}',  -- ISO weekday, 1 = Monday
  work_start          time not null default '09:00',
  work_end            time not null default '17:30',
  is_out_of_office    boolean not null default false,
  out_of_office_until date,
  backup_person_id    uuid references people (id) on delete set null,
  created_at          timestamptz not null default now(),
  unique (firm_id, email)
);

alter table firms
  add constraint firms_default_contact_fk
  foreign key (default_contact_id) references people (id) on delete set null;

-- Who handles what ("who do I ask about payroll?").
create table responsibilities (
  id          uuid primary key default gen_random_uuid(),
  firm_id     uuid not null references firms (id) on delete cascade,
  person_id   uuid not null references people (id) on delete cascade,
  topic       text not null,
  description text not null,
  keywords    text[] not null default '{}',
  is_personal boolean not null default false,  -- route without discussing details in chat
  rank        smallint not null default 1,     -- 1 = primary contact for the topic
  unique (firm_id, topic, person_id)
);

create table projects (
  id         uuid primary key default gen_random_uuid(),
  firm_id    uuid not null references firms (id) on delete cascade,
  code       text not null,
  name       text not null,
  client     text not null,
  phase      text not null,
  location   text,
  is_active  boolean not null default true,
  created_at timestamptz not null default now(),
  unique (firm_id, code)
);

create table project_roles (
  id         uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects (id) on delete cascade,
  person_id  uuid not null references people (id) on delete cascade,
  role       project_role not null,
  unique (project_id, person_id, role)
);

-- App users. One row per Supabase auth user.
create table profiles (
  id         uuid primary key references auth.users (id) on delete cascade,
  firm_id    uuid not null references firms (id) on delete cascade,
  person_id  uuid references people (id) on delete set null,  -- their own directory row
  role       user_role not null default 'employee',
  full_name  text not null,
  email      text not null,
  start_date date,
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Manual Enhancer
-- ---------------------------------------------------------------------------

create table manuals (
  id          uuid primary key default gen_random_uuid(),
  firm_id     uuid not null references firms (id) on delete cascade,
  uploaded_by uuid references profiles (id) on delete set null,
  title       text not null,
  file_path   text not null,  -- path in the `manuals` storage bucket
  file_type   file_type not null,
  page_count  integer,
  status      manual_status not null default 'uploaded',
  error       text,
  processing_notes jsonb not null default '{}',  -- sections left out, omissions, warnings, token usage
  created_at  timestamptz not null default now()
);

-- The original manual text, split into sections with page numbers.
create table source_sections (
  id         uuid primary key default gen_random_uuid(),
  manual_id  uuid not null references manuals (id) on delete cascade,
  ordinal    integer not null,
  heading    text,
  content    text not null,
  page_start integer,
  page_end   integer,
  unique (manual_id, ordinal)
);

create table modules (
  id          uuid primary key default gen_random_uuid(),
  firm_id     uuid not null references firms (id) on delete cascade,
  manual_id   uuid references manuals (id) on delete set null,
  title       text not null,
  summary     text,
  ordinal     integer not null default 0,
  priority    module_priority not null default 'later',
  is_required boolean not null default true,
  status      review_status not null default 'draft',
  reviewed_by uuid references profiles (id) on delete set null,
  reviewed_at timestamptz,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- Enhanced text. Every passage must point at the source section it came from.
create table module_passages (
  id                uuid primary key default gen_random_uuid(),
  module_id         uuid not null references modules (id) on delete cascade,
  source_section_id uuid not null references source_sections (id) on delete restrict,
  ordinal           integer not null,
  heading           text,
  content           text not null,  -- markdown
  kind              passage_kind not null default 'text',
  is_critical       boolean not null default false,
  grounding_ok      boolean,        -- null until the grounding check runs
  unsupported_spans jsonb not null default '[]',  -- [{"text": ..., "reason": ...}]
  unique (module_id, ordinal)
);

-- Problems the AI found in the source. Flagged for the admin, never silently fixed.
create table issues (
  id                uuid primary key default gen_random_uuid(),
  firm_id           uuid not null references firms (id) on delete cascade,
  manual_id         uuid not null references manuals (id) on delete cascade,
  source_section_id uuid references source_sections (id) on delete set null,
  related_section_id uuid references source_sections (id) on delete set null,  -- other side of a contradiction
  module_id         uuid references modules (id) on delete set null,
  type              issue_type not null,
  description       text not null,
  excerpt           text,
  status            issue_status not null default 'open',
  created_at        timestamptz not null default now()
);

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

create table module_progress (
  id           uuid primary key default gen_random_uuid(),
  profile_id   uuid not null references profiles (id) on delete cascade,
  module_id    uuid not null references modules (id) on delete cascade,
  status       progress_status not null default 'not_started',
  started_at   timestamptz,
  completed_at timestamptz,
  unique (profile_id, module_id)
);

-- ---------------------------------------------------------------------------
-- Final Onboarding Check
-- ---------------------------------------------------------------------------

create table quiz_questions (
  id             uuid primary key default gen_random_uuid(),
  firm_id        uuid not null references firms (id) on delete cascade,
  passage_id     uuid not null references module_passages (id) on delete cascade,
  type           question_type not null,
  prompt         text not null,
  choices        jsonb,     -- multiple choice: ["...", "..."]
  correct_choice smallint,  -- multiple choice: index into choices
  rubric         text,      -- scenario: grading rubric built from the source
  explanation    text not null,
  status         review_status not null default 'draft',
  created_at     timestamptz not null default now(),
  check (
    (type = 'multiple_choice' and choices is not null and correct_choice is not null)
    or (type = 'scenario' and rubric is not null)
  )
);

create table quiz_attempts (
  id           uuid primary key default gen_random_uuid(),
  firm_id      uuid not null references firms (id) on delete cascade,
  profile_id   uuid not null references profiles (id) on delete cascade,
  question_ids uuid[] not null default '{}',  -- the questions drawn for this attempt, in order
  status       attempt_status not null default 'in_progress',
  score        numeric(5, 2),  -- percent correct on first tries
  started_at   timestamptz not null default now(),
  completed_at timestamptz
);

-- One row per try; retries on missed questions add rows with a higher try_number.
create table quiz_answers (
  id              uuid primary key default gen_random_uuid(),
  attempt_id      uuid not null references quiz_attempts (id) on delete cascade,
  question_id     uuid not null references quiz_questions (id) on delete cascade,
  try_number      smallint not null default 1,
  selected_choice smallint,
  answer_text     text,
  is_correct      boolean not null,
  feedback        text,
  created_at      timestamptz not null default now(),
  unique (attempt_id, question_id, try_number)
);

-- ---------------------------------------------------------------------------
-- Assistant
-- ---------------------------------------------------------------------------

create table chat_logs (
  id                 uuid primary key default gen_random_uuid(),
  firm_id            uuid not null references firms (id) on delete cascade,
  profile_id         uuid references profiles (id) on delete set null,
  question           text not null,
  answer             text,
  intent             chat_intent,
  matched_person_id  uuid references people (id) on delete set null,
  matched_passage_id uuid references module_passages (id) on delete set null,
  used_fallback      boolean not null default false,  -- shown to admin as unanswered
  created_at         timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------

create index on people (firm_id);
create index on responsibilities (firm_id, topic);
create index on responsibilities using gin (keywords);
create index on project_roles (person_id);
create index on source_sections (manual_id);
create index on modules (firm_id, status);
create index on module_passages (source_section_id);
create index on issues (manual_id, status);
create index on module_progress (module_id);
create index on quiz_questions (firm_id, status);
create index on quiz_answers (question_id);
create index on chat_logs (firm_id, used_fallback);
create index on baseline_overrides (firm_id, status);
create index on baseline_overrides (baseline_passage_id);

-- ---------------------------------------------------------------------------
-- Views
-- ---------------------------------------------------------------------------

-- Directory with "is in today" computed in the firm's timezone.
create view people_availability as
select
  p.*,
  (
    not p.is_out_of_office
    and extract(isodow from (now() at time zone f.timezone))::smallint = any (p.work_days)
  ) as is_in_today
from people p
join firms f on f.id = p.firm_id;

-- Per-employee progress for the admin dashboard.
create view employee_progress as
select
  pr.id        as profile_id,
  pr.firm_id,
  pr.full_name,
  count(m.id) filter (where m.is_required)                                  as required_modules,
  count(mp.id) filter (where m.is_required and mp.status = 'completed')     as completed_required,
  count(mp.id) filter (where mp.status = 'completed')                       as completed_modules,
  exists (
    select 1 from quiz_attempts qa
    where qa.profile_id = pr.id and qa.status = 'completed'
  )                                                                         as final_check_done
from profiles pr
left join modules m
  on m.firm_id = pr.firm_id and m.status = 'approved'
left join module_progress mp
  on mp.profile_id = pr.id and mp.module_id = m.id
where pr.role = 'employee'
group by pr.id, pr.firm_id, pr.full_name;

-- Most-failed questions, counting only first tries.
create view question_failure_stats as
select
  q.id      as question_id,
  q.firm_id,
  q.prompt,
  q.passage_id,
  count(a.id)                                as first_tries,
  count(a.id) filter (where not a.is_correct) as first_try_misses
from quiz_questions q
left join quiz_answers a
  on a.question_id = q.id and a.try_number = 1
group by q.id;

-- ---------------------------------------------------------------------------
-- Row level security: enabled everywhere, no policies (backend only)
-- ---------------------------------------------------------------------------

alter table firms            enable row level security;
alter table people           enable row level security;
alter table responsibilities enable row level security;
alter table projects         enable row level security;
alter table project_roles    enable row level security;
alter table profiles         enable row level security;
alter table manuals          enable row level security;
alter table source_sections  enable row level security;
alter table modules          enable row level security;
alter table module_passages  enable row level security;
alter table issues           enable row level security;
alter table module_progress  enable row level security;
alter table quiz_questions   enable row level security;
alter table quiz_attempts    enable row level security;
alter table quiz_answers     enable row level security;
alter table chat_logs        enable row level security;
alter table firm_baseline_modules  enable row level security;
alter table firm_baseline_passages enable row level security;
alter table baseline_overrides     enable row level security;

-- Views run with the caller's permissions so RLS still applies.
alter view people_availability    set (security_invoker = true);
alter view employee_progress      set (security_invoker = true);
alter view question_failure_stats set (security_invoker = true);
