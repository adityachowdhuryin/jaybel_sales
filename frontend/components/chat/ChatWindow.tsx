"use client";

import { FormEvent, useEffect, useState } from "react";
import { ArrowUp, PanelLeftOpen, Sparkles } from "lucide-react";
import { MessageList } from "./MessageList";
import type { ChatMessage } from "@/types";

const PLACEHOLDER = "Ask about sales, revenue, customers…";

export function ChatWindow({
  messages,
  sessionId,
  onSend,
  disabled,
  draftInput,
  onDraftChange,
  onFollowUpPick,
  onClarificationPick,
  onRetry,
  hideFollowUps,
  streaming,
  sidebarCollapsed,
  onExpandSidebar,
}: {
  messages: ChatMessage[];
  sessionId: string | null;
  onSend: (text: string) => void;
  onRetry?: (
    question: string,
    replaceTurnId: string,
    meta: { starterId?: string; categoryId?: string }
  ) => void;
  disabled?: boolean;
  draftInput: string;
  onDraftChange: (value: string) => void;
  onFollowUpPick: (text: string) => void;
  onClarificationPick?: (text: string) => void;
  hideFollowUps?: boolean;
  streaming?: boolean;
  sidebarCollapsed?: boolean;
  onExpandSidebar?: () => void;
}) {
  const [localInput, setLocalInput] = useState(draftInput);
  const hasText = localInput.trim().length > 0;

  useEffect(() => {
    setLocalInput(draftInput);
  }, [draftInput]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const q = localInput.trim();
    if (!q || disabled) return;
    setLocalInput("");
    onDraftChange("");
    onSend(q);
  }

  return (
    <div className="flex flex-col h-full min-h-0">
      {sidebarCollapsed && onExpandSidebar && (
        <div className="flex items-center px-4 py-2 border-b border-[var(--border)] bg-[var(--surface-0)] shrink-0">
          <button
            type="button"
            onClick={onExpandSidebar}
            className="inline-flex items-center justify-center rounded-md p-1.5 text-[var(--text-secondary)] hover:bg-[var(--surface-2)] transition"
            aria-label="Expand sidebar"
          >
            <PanelLeftOpen className="w-5 h-5" />
          </button>
        </div>
      )}
      <MessageList
        messages={messages}
        sessionId={sessionId}
        onFollowUpPick={onFollowUpPick}
        onClarificationPick={onClarificationPick}
        onRetry={onRetry}
        hideFollowUps={hideFollowUps}
        streaming={streaming}
      />
      <form
        onSubmit={handleSubmit}
        className="border-t border-[var(--border)] px-4 py-4 bg-[var(--panel)] shrink-0"
      >
        <div className="flex items-center gap-3 max-w-3xl mx-auto w-full min-h-[52px] rounded-2xl bg-[var(--surface-0)] px-4 py-2.5 shadow-sm border border-[var(--border)]">
          {!hasText && (
            <Sparkles
              className="w-5 h-5 shrink-0 text-[var(--text-tertiary)]"
              strokeWidth={1.5}
              aria-hidden
            />
          )}
          <textarea
            value={localInput}
            onChange={(e) => {
              setLocalInput(e.target.value);
              onDraftChange(e.target.value);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder={PLACEHOLDER}
            rows={1}
            disabled={disabled}
            className={`flex-1 min-w-0 resize-none bg-transparent border-0 outline-none text-sm leading-6 text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] disabled:opacity-50 ${
              hasText ? "py-1" : "py-1"
            }`}
          />
          {localInput.length > 200 && (
            <span className="shrink-0 text-[10px] text-[var(--muted)] tabular-nums self-end pb-1">
              {localInput.length}
            </span>
          )}
          <button
            type="submit"
            disabled={disabled || !hasText}
            aria-label="Send message"
            className={`shrink-0 w-9 h-9 rounded-full inline-flex items-center justify-center transition disabled:cursor-not-allowed ${
              hasText
                ? "bg-[var(--chat-send-bg)] text-white hover:bg-[var(--chat-send-bg-hover)] disabled:opacity-40"
                : "bg-[var(--surface-2)] text-[var(--text-tertiary)]"
            }`}
          >
            <ArrowUp className="w-4 h-4 text-white" strokeWidth={2.25} />
          </button>
        </div>
      </form>
    </div>
  );
}
