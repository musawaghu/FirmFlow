import { supabase } from "./supabase";
import type {
  AdminModule,
  AnswerResult,
  Attempt,
  ChatReply,
  Issue,
  Manual,
  Override,
  Review,
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

async function request<T>(path: string, init: { method?: string; body?: unknown; form?: FormData } = {}): Promise<T> {
  const token = supabase ? (await supabase.auth.getSession()).data.session?.access_token : undefined;
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: init.method ?? "GET",
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(init.body !== undefined ? { "Content-Type": "application/json" } : {}),
      },
      body: init.form ?? (init.body !== undefined ? JSON.stringify(init.body) : undefined),
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

  // Final check
  currentAttempt: () => request<Attempt>("/api/quiz/attempts/current"),
  startAttempt: () => request<Attempt>("/api/quiz/attempts", { method: "POST" }),
  answer: (attemptId: string, body: { question_id: string; selected_choice?: number; answer_text?: string }) =>
    request<AnswerResult>(`/api/quiz/attempts/${attemptId}/answers`, { method: "POST", body }),

  // "Who do I ask?"
  ask: (question: string) => request<ChatReply>("/api/chat", { method: "POST", body: { question } }),

  // Admin
  manuals: () => request<Manual[]>("/api/manuals"),
  manual: (id: string) => request<Manual>(`/api/manuals/${id}`),
  uploadManual: (file: File, title: string) => {
    const form = new FormData();
    form.append("file", file);
    if (title.trim()) form.append("title", title.trim());
    return request<Manual>("/api/manuals", { method: "POST", form });
  },
  processManual: (id: string, moduleTopics: string[]) =>
    request<Manual>(`/api/manuals/${id}/process`, { method: "POST", body: moduleTopics.length ? { module_topics: moduleTopics } : {} }),
  review: (manualId: string) => request<Review>(`/api/manuals/${manualId}/review`),
  issues: (manualId: string) => request<Issue[]>(`/api/manuals/${manualId}/issues`),
  updateOverride: (id: string, status: Override["status"]) => request<Override>(`/api/overrides/${id}`, { method: "PATCH", body: { status } }),
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
