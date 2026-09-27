import type { Priority, ProgressStatus } from "./types";

export const PRIORITIES: Priority[] = ["day_1", "week_1", "later"];

/** Backend priorities, named the way the checklist talks about them. */
export const PRIORITY_LABEL: Record<Priority, string> = {
  day_1: "Day 1",
  week_1: "Week 1",
  later: "First month",
};

export const PROGRESS_LABEL: Record<ProgressStatus, string> = {
  not_started: "Not started",
  in_progress: "In progress",
  completed: "Completed",
};

export function percent(part: number, whole: number): number {
  return whole === 0 ? 0 : Math.round((part / whole) * 100);
}

export function shortDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
