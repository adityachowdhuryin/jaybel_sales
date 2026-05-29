import type { ChatSendMeta, UIEvent } from "@/types";
import { API_BASE } from "./api";
import { buildAuthHeaders } from "./authHeaders";

export async function streamChat(
  sessionId: string,
  question: string,
  onEvent: (event: UIEvent) => void,
  signal?: AbortSignal,
  meta?: ChatSendMeta
): Promise<void> {
  const authHeaders = await buildAuthHeaders({
    "Content-Type": "application/json",
  });
  const res = await fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers: authHeaders,
    body: JSON.stringify({
      session_id: sessionId,
      question,
      starter_id: meta?.starter_id,
      category_id: meta?.category_id,
      replace_turn_id: meta?.replace_turn_id,
    }),
    signal,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Stream failed: ${res.status}`);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      for (const line of part.split("\n")) {
        if (line.startsWith("data: ")) {
          try {
            onEvent(JSON.parse(line.slice(6)) as UIEvent);
          } catch {
            /* ignore malformed */
          }
        }
      }
    }
  }
}
