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
