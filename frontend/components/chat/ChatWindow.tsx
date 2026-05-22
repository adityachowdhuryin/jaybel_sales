"use client";

import { FormEvent, useEffect, useState } from "react";
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
      <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border)] bg-[var(--panel)] shrink-0">
        <div className="text-xs text-[var(--muted)] truncate">
          <button
            type="button"
            onClick={onOpenExplore}
            className="text-brand-400 hover:text-brand-300"
          >
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
        hideFollowUps={hideFollowUps}
      />
      <form
        onSubmit={handleSubmit}
        className="border-t border-[var(--border)] p-4 bg-[var(--panel)] shrink-0"
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
            className="flex-1 resize-none rounded-xl border border-[var(--border)] bg-[var(--bg)] px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:opacity-50"
          />
          {localInput.length > 200 && (
            <span className="self-end text-[10px] text-[var(--muted)] tabular-nums">
              {localInput.length}
            </span>
          )}
          <button
            type="submit"
            disabled={disabled || !localInput.trim()}
            className="self-end px-5 py-3 rounded-xl bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-40"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
