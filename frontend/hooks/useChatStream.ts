"use client";

import { useCallback, useRef, useState } from "react";
import { streamChat } from "@/lib/sse";
import type {
  ChartSpec,
  ChatMessage,
  ChatSendMeta,
  ClarificationOption,
  UIEvent,
} from "@/types";

function newId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function chartFromEvent(ev: UIEvent): ChartSpec | null {
  if (ev.type !== "chart_spec") return null;
  const { type: _t, ...rest } = ev;
  if (rest.chart_type || rest.x || rest.y) return rest as ChartSpec;
  return null;
}

export function useChatStream() {
  const [streaming, setStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (
      sessionId: string,
      question: string,
      onUpdate: (updater: (prev: ChatMessage[]) => ChatMessage[]) => void,
      meta?: ChatSendMeta
    ) => {
      const now = new Date().toISOString();
      const userMsg: ChatMessage = {
        id: newId(),
        role: "user",
        content: question,
        createdAt: now,
      };
      const agentId = newId();
      onUpdate((prev) => [
        ...prev,
        userMsg,
        {
          id: agentId,
          role: "agent",
          content: "",
          question,
          starterId: meta?.starter_id,
          categoryId: meta?.category_id,
          createdAt: now,
          streaming: true,
          status: "Starting…",
        },
      ]);

      abortRef.current?.abort();
      abortRef.current = new AbortController();
      setStreaming(true);

      try {
        await streamChat(
          sessionId,
          question,
          (ev: UIEvent) => {
            onUpdate((prev) =>
              prev.map((m) => {
                if (m.id !== agentId) return m;
                const next = { ...m };
                switch (ev.type) {
                  case "status":
                    next.status = ev.message as string;
                    break;
                  case "table_name":
                    next.tableDisplay = (ev.display as string) || (ev.table as string);
                    break;
                  case "sql":
                    next.sql = ev.sql as string;
                    break;
                  case "results":
                    next.rows = (ev.rows as Record<string, unknown>[]) ?? [];
                    next.columns = (ev.columns as string[]) ?? [];
                    next.rowCount = (ev.row_count as number) ?? 0;
                    break;
                  case "token":
                    next.content += (ev.text as string) ?? "";
                    break;
                  case "chart_spec": {
                    const spec = chartFromEvent(ev);
                    if (spec) next.chartSpec = spec;
                    break;
                  }
                  case "cost_warning":
                    next.costWarningBytes = (ev.bytes_scanned as number) ?? 0;
                    break;
                  case "clarification_needed":
                    next.clarification = {
                      code: (ev.code as string) || "clarification",
                      message: (ev.message as string) || "",
                      options: (ev.options as ClarificationOption[]) || [],
                    };
                    if (!next.content && next.clarification.message) {
                      next.content = next.clarification.message;
                    }
                    break;
                  case "user_guidance":
                    next.guidance = {
                      code: (ev.code as string) || "guidance",
                      message: (ev.message as string) || "",
                      suggestions: ev.suggestions as string[] | undefined,
                    };
                    break;
                  case "error":
                    next.error = (ev.message as string) || "Error";
                    next.streaming = false;
                    next.status = undefined;
                    break;
                  case "done":
                    next.streaming = false;
                    next.status = undefined;
                    next.queryId = (ev.query_id as string) || next.queryId;
                    if (ev.turn_id) next.turnId = ev.turn_id as string;
                    break;
                  default:
                    break;
                }
                return next;
              })
            );
          },
          abortRef.current.signal,
          meta
        );
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Request failed";
        onUpdate((prev) =>
          prev.map((m) =>
            m.id === agentId
              ? { ...m, error: msg, streaming: false, status: undefined }
              : m
          )
        );
      } finally {
        setStreaming(false);
      }
    },
    []
  );

  return { sendMessage, streaming };
}
