// Response shapes from the FastAPI backend (backend/app/schemas.py).

export type Role = "admin" | "employee";
export type Priority = "day_1" | "week_1" | "later";
export type ProgressStatus = "not_started" | "in_progress" | "completed";
export type Layer = "firm" | "baseline";

export interface Me {
  id: string;
  full_name: string;
  email: string;
  role: Role;
  firm_id: string;
  firm_name: string | null;
}

export interface EmployeePassage {
  id: string;
  ordinal: number;
  heading: string | null;
  content: string;
  kind: "text" | "steps" | "checklist" | "summary";
  overridden_by_firm: boolean;
  firm_note: string | null;
  firm_passage_id: string | null;
}

export interface EmployeeModule {
  id: string;
  layer: Layer;
  title: string;
  summary: string | null;
  priority: Priority;
  is_required: boolean;
  progress: ProgressStatus;
  passages: EmployeePassage[];
}

export interface ModuleList {
  full_name: string;
  required_modules: number;
  completed_required: number;
  final_check_unlocked: boolean;
  modules: EmployeeModule[];
}

export interface SectionLink {
  module_id: string;
  module_title: string;
  passage_id: string;
  passage_heading: string | null;
}

export interface ModuleStatus {
  module_id: string;
  layer: Layer;
  title: string;
  priority: Priority;
  is_required: boolean;
  status: ProgressStatus;
}

export interface FinalCheck {
  status: "locked" | "not_started" | "in_progress" | "completed";
  score: number | null;
  attempts: number;
  completed_at: string | null;
}

export interface EmployeeProgress {
  profile_id: string;
  full_name: string;
  email: string;
  start_date: string | null;
  stage: "not_started" | "in_progress" | "modules_done" | "complete";
  required_modules: number;
  completed_required: number;
  modules: ModuleStatus[];
  final_check: FinalCheck;
  last_activity_at: string | null;
}

export interface AdminProgress {
  required_modules: number;
  employees: EmployeeProgress[];
}

export interface FailedQuestion {
  question_id: string;
  prompt: string;
  type: string;
  status: string;
  first_tries: number;
  first_try_misses: number;
  miss_rate: number;
  link: SectionLink | null;
}

export interface BaselinePassage {
  id: string;
  ordinal: number;
  heading: string | null;
  content: string;
  kind: string;
  is_critical: boolean;
  overridden_by: string | null;
}

export interface BaselineModule {
  id: string;
  title: string;
  summary: string | null;
  priority: Priority;
  is_required: boolean;
  ordinal: number;
  is_hidden: boolean;
  passages: BaselinePassage[];
}

export interface AdminPassage {
  id: string;
  source_section_id: string;
  ordinal: number;
  heading: string | null;
  content: string;
  kind: string;
  is_critical: boolean;
  grounding_ok: boolean | null;
  unsupported_spans: { text: string }[]; // text the source section doesn't support
}

export interface AdminModule {
  id: string;
  title: string;
  summary: string | null;
  ordinal: number;
  priority: Priority;
  is_required: boolean;
  status: string;
  passages: AdminPassage[];
}

// Final check
export interface AttemptQuestion {
  id: string;
  type: "multiple_choice" | "scenario";
  prompt: string;
  choices: string[] | null;
  state: "unanswered" | "missed" | "correct";
  tries: number;
  link: SectionLink | null; // shown once the question has been missed
}

export interface Attempt {
  id: string;
  status: "in_progress" | "completed";
  score: number | null;
  started_at: string;
  completed_at: string | null;
  questions: AttemptQuestion[];
}

export interface AnswerResult {
  question_id: string;
  is_correct: boolean;
  feedback: string;
  try_number: number;
  link: SectionLink | null;
  attempt: Attempt;
}

// "Who do I ask?"
export interface ContactCard {
  person_id: string;
  name: string;
  title: string;
  department: string;
  email: string;
  phone_ext: string | null;
  working_hours: string;
  is_in_today: boolean;
  out_of_office_until: string | null;
  reason: string;
  mailto: string;
  backup: ContactCard | null;
}

export interface ChatReply {
  intent: string;
  answer: string;
  links: SectionLink[];
  contacts: ContactCard[];
  used_fallback: boolean;
}

// Manuals
export interface Manual {
  id: string;
  title: string;
  file_type: string;
  page_count: number | null;
  status: "uploaded" | "processing" | "processed" | "failed";
  error: string | null;
  processing_notes: { warnings?: string[]; input_tokens?: number; output_tokens?: number; [k: string]: unknown };
  created_at: string;
}

export interface SourceSection {
  id: string;
  ordinal: number;
  heading: string | null;
  content: string;
  page_start: number | null;
  page_end: number | null;
}

export interface PassageRef {
  passage_id: string;
  heading: string | null;
  module_id: string;
  module_title: string;
}

export interface Override {
  id: string;
  status: "proposed" | "confirmed" | "dismissed";
  difference: string;
  firm_excerpt: string;
  baseline_excerpt: string;
  firm_passage: PassageRef;
  baseline_passage: PassageRef;
}

export interface Review {
  manual: Manual;
  sections: SourceSection[];
  modules: AdminModule[];
  overrides: Override[];
}

export interface Issue {
  id: string;
  type: string;
  description: string;
  excerpt: string | null;
  status: string;
  module_id: string | null;
  source_section_id: string | null;
  related_section_id: string | null;
  section_heading: string | null;
  pages: string | null;
}
