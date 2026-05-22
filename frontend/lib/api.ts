import type { AppUser, ChatSession, ChatTurn } from "@/types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function getMe(): Promise<AppUser> {
  return request<AppUser>("/api/sessions/me");
}

export async function updateProfile(data: {
  display_name?: string;
  email?: string;
  sales_rep_code?: string | null;
}): Promise<AppUser> {
  return request<AppUser>("/api/sessions/me", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function listSessions(search?: string): Promise<ChatSession[]> {
  const q = search?.trim();
  const path = q ? `/api/sessions?q=${encodeURIComponent(q)}` : "/api/sessions";
  return request<ChatSession[]>(path);
}

export async function submitTurnFeedback(
  sessionId: string,
  turnId: string,
  rating: number,
  comment?: string
): Promise<void> {
  await request<void>(`/api/sessions/${sessionId}/turns/${turnId}/feedback`, {
    method: "POST",
    body: JSON.stringify({ rating, comment }),
  });
}

export async function createSession(title = "New chat"): Promise<ChatSession> {
  return request<ChatSession>("/api/sessions", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

export async function deleteSession(sessionId: string): Promise<void> {
  await request<void>(`/api/sessions/${sessionId}`, { method: "DELETE" });
}

export async function listTurns(sessionId: string): Promise<ChatTurn[]> {
  return request<ChatTurn[]>(`/api/sessions/${sessionId}/turns`);
}

export { API_BASE };
