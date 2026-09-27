import { supabase } from "./supabase";
import type {
  AdminModule,
  AdminPassage,
  AdminProgress,
  BaselineModule,
  FailedQuestion,
  Me,
  ModuleList,
  Priority,
} from "./types";

const API_URL = ((import.meta.env.VITE_API_URL as string | undefined) || "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

function describe(detail: unknown, status: number): string {
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object" && "message" in detail) return String((detail as { message: unknown }).message);
  if (Array.isArray(detail)) return detail.map((d) => d?.msg ?? "Invalid request").join("; ");
  if (status === 429) return "Too many requests. Wait a moment and try again.";
  return `Request failed (${status})`;
}

async function request<T>(path: string, init: { method?: string; body?: unknown } = {}): Promise<T> {
  const token = supabase ? (await supabase.auth.getSession()).data.session?.access_token : undefined;
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: init.method ?? "GET",
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(init.body !== undefined ? { "Content-Type": "application/json" } : {}),
      },
      body: init.body !== undefined ? JSON.stringify(init.body) : undefined,
    });
  } catch {
    throw new ApiError(0, `Can't reach the FIRM FLOW API at ${API_URL}.`);
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, describe(data?.detail, response.status));
  return data as T;
}

export const api = {
  me: () => request<Me>("/api/me"),

  // Employee
  modules: () => request<ModuleList>("/api/modules"),
  setProgress: (moduleId: string, status: "in_progress" | "completed") =>
    request(`/api/modules/${moduleId}/progress`, { method: "POST", body: { status } }),

  // Admin
  manuals: () => request<{ id: string; title: string; status: string; created_at: string }[]>("/api/manuals"),
  review: (manualId: string) => request<{ modules: AdminModule[] }>(`/api/manuals/${manualId}/review`),
  adminProgress: () => request<AdminProgress>("/api/admin/progress"),
  failedQuestions: () => request<FailedQuestion[]>("/api/admin/failed-questions"),
  baselineModules: () => request<BaselineModule[]>("/api/baseline/modules"),
  updateBaselineModule: (id: string, body: Partial<{ priority: Priority; is_required: boolean; ordinal: number; is_hidden: boolean }>) =>
    request<BaselineModule>(`/api/baseline/modules/${id}`, { method: "PATCH", body }),
  updateModule: (id: string, body: Partial<{ priority: Priority; is_required: boolean; ordinal: number; status: string; title: string; summary: string; confirm_flagged: boolean }>) =>
    request<AdminModule>(`/api/modules/${id}`, { method: "PATCH", body }),
  updatePassage: (id: string, body: Partial<{ content: string; heading: string; is_critical: boolean }>) =>
    request<AdminPassage & { grounding_error: string | null }>(`/api/passages/${id}`, { method: "PATCH", body }),
};
