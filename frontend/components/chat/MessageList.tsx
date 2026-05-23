"use client";

import { useEffect, useRef } from "react";
import { AgentMessage } from "./AgentMessage";
import { FollowUpChips } from "./FollowUpChips";
import { UserMessage } from "./UserMessage";
import type { AppUser, ChatMessage } from "@/types";

export function MessageList({
  messages,
  sessionId,
  user,
  onFollowUpPick,
  hideFollowUps,
}: {
  messages: ChatMessage[];
  sessionId: string | null;
  user: AppUser | null;
  onFollowUpPick: (text: string) => void;
  hideFollowUps?: boolean;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const shouldAutoScroll = useRef(true);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const onScroll = () => {
      const dist = el.scrollHeight - el.scrollTop - el.clientHeight;
      shouldAutoScroll.current = dist < 120;
    };
    el.addEventListener("scroll", onScroll);
    return () => el.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (shouldAutoScroll.current) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto px-4 py-6">
      {messages.length === 0 && (
        <div className="text-center max-w-lg mx-auto mt-20 px-4">
          <h2 className="text-2xl font-semibold tracking-tight text-[var(--text)]">
            What would you like to explore?
          </h2>
          <p className="text-sm text-[var(--muted)] mt-3 leading-relaxed">
            Open{" "}
            <strong className="font-medium text-brand-400">Browse questions</strong> for curated
            starters, or ask in plain English below.
          </p>
          {!user?.sales_rep_code && (
            <p className="text-xs text-amber-400/90 mt-3">
              My Performance and commission questions need your{" "}
              <strong className="font-medium">sales rep code</strong> in the sidebar (Settings).
              Other categories work without it.
            </p>
          )}
        </div>
      )}
      {messages.map((m, i) => {
        const isLastAgent =
          m.role === "agent" && i === messages.length - 1 && !m.streaming;
        return m.role === "user" ? (
          <UserMessage key={m.id} content={m.content} createdAt={m.createdAt} />
        ) : (
          <div key={m.id}>
            <AgentMessage message={m} sessionId={sessionId} />
            {isLastAgent && sessionId && m.question && (
              <FollowUpChips
                sessionId={sessionId}
                turnId={m.turnId}
                question={m.question}
                starterId={m.starterId}
                onPick={onFollowUpPick}
                hidden={hideFollowUps || m.streaming}
              />
            )}
          </div>
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
}
