"use client";

import { FormEvent, useEffect, useState } from "react";
import { Compass, Send } from "lucide-react";
import { MessageList } from "./MessageList";
import type { AppUser, ChatMessage } from "@/types";
import type { QuestionCategory, StarterQuestion } from "@/types/questionCatalog";

export function ChatWindow({
  messages,
  sessionId,
  user,
  onSend,
  disabled,
  draftInput,
  onDraftChange,
  exploreOpen,
  onOpenExplore,
  activeCategory,
  onPickStarter,
  onFollowUpPick,
  onClarificationPick,
  hideFollowUps,
}: {
  messages: ChatMessage[];
  sessionId: string | null;
  user: AppUser | null;
  onSend: (text: string) => void;
  disabled?: boolean;
  draftInput: string;
  onDraftChange: (value: string) => void;
  exploreOpen: boolean;
  onOpenExplore: () => void;
  activeCategory: QuestionCategory | null;
  onPickStarter: (starter: StarterQuestion) => void;
  onFollowUpPick: (text: string) => void;
  onClarificationPick?: (text: string) => void;
  hideFollowUps?: boolean;
}) {
  const [localInput, setLocalInput] = useState(draftInput);

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
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)] bg-[var(--panel)]/80 backdrop-blur-sm shrink-0">
        <div className="text-xs text-[var(--muted)] truncate flex items-center gap-1">
          <button
            type="button"
            onClick={onOpenExplore}
            className="inline-flex items-center gap-1.5 text-brand-400 hover:text-brand-300 font-medium transition"
          >
            <Compass className="w-3.5 h-3.5" />
            Browse questions
          </button>
          {activeCategory && (
            <>
              <span className="mx-1">/</span>
              <span className="text-[var(--text)]">{activeCategory.label}</span>
            </>
          )}
        </div>
        {exploreOpen && (
          <span className="text-[10px] text-[var(--muted)]">Explore open</span>
        )}
      </div>
      <MessageList
        messages={messages}
        sessionId={sessionId}
        user={user}
        onFollowUpPick={onFollowUpPick}
        onClarificationPick={onClarificationPick}
        hideFollowUps={hideFollowUps}
      />
      <form
        onSubmit={handleSubmit}
        className="border-t border-[var(--border)] p-4 bg-[var(--panel)]/90 backdrop-blur-sm shrink-0"
      >
        <div className="flex gap-2 max-w-3xl mx-auto">
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
            placeholder="Ask about sales, revenue, customers…"
            rows={2}
            disabled={disabled}
            className="flex-1 resize-none rounded-xl border border-[var(--border)] bg-[var(--bg-elevated)] px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/60 focus:border-brand-500/40 disabled:opacity-50 placeholder:text-[var(--muted)]"
          />
          {localInput.length > 200 && (
            <span className="self-end text-[10px] text-[var(--muted)] tabular-nums">
              {localInput.length}
            </span>
          )}
          <button
            type="submit"
            disabled={disabled || !localInput.trim()}
            className="self-end inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 text-white text-sm font-medium hover:from-brand-500 hover:to-brand-400 disabled:opacity-40 shadow-md transition"
          >
            <Send className="w-4 h-4" />
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
