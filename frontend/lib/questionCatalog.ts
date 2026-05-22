import type {
  FollowUpsResponse,
  QuestionCategory,
  StarterQuestion,
} from "@/types/questionCatalog";
import { API_BASE } from "./api";

async function catalogRequest<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchCategories(): Promise<QuestionCategory[]> {
  return catalogRequest<QuestionCategory[]>("/api/question-catalog/categories");
}

export async function fetchStarters(categoryId: string): Promise<StarterQuestion[]> {
  return catalogRequest<StarterQuestion[]>(
    `/api/question-catalog/categories/${encodeURIComponent(categoryId)}/starters`
  );
}

export async function searchStarters(
  q: string,
  filters?: { category_id?: string; table_id?: string; intent?: string }
): Promise<StarterQuestion[]> {
  const params = new URLSearchParams({ q });
  if (filters?.category_id) params.set("category_id", filters.category_id);
  if (filters?.table_id) params.set("table_id", filters.table_id);
  if (filters?.intent) params.set("intent", filters.intent);
  return catalogRequest<StarterQuestion[]>(`/api/question-catalog/search?${params}`);
}

export async function fetchFollowUps(params: {
  starter_id?: string;
  question?: string;
  session_id?: string;
  turn_id?: string;
}): Promise<FollowUpsResponse> {
  const res = await fetch(`${API_BASE}/api/question-catalog/follow-ups`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      starter_id: params.starter_id,
      question: params.question,
      session_id: params.session_id,
      turn_id: params.turn_id,
    }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json() as Promise<FollowUpsResponse>;
}
