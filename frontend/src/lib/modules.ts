import type { Priority } from "./types";

const PRIORITY_ORDER: Record<Priority, number> = { day_1: 0, week_1: 1, later: 2 };

/** Same order the backend uses (services/content.py module_sort_key): priority, then position, then title. */
export function sortModules<T extends { priority: Priority; ordinal: number; title: string }>(modules: T[]): T[] {
  return [...modules].sort(
    (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority] || a.ordinal - b.ordinal || a.title.localeCompare(b.title),
  );
}
