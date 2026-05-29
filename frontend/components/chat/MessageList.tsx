"use client";

import { useEffect, useRef } from "react";
import { AgentMessage } from "./AgentMessage";
import { DailyBusinessSummary } from "./dashboard/DailyBusinessSummary";
import { FollowUpChips } from "./FollowUpChips";
import { UserMessage } from "./UserMessage";
import type { ChatMessage } from "@/types";

export function MessageList({
  messages,
  sessionId,
  onFollowUpPick,
  onClarificationPick,
  onRetry,
  hideFollowUps,
  streaming,
}: {
  messages: ChatMessage[];
  sessionId: string | null;
  onFollowUpPick: (text: string) => void;
  onClarificationPick?: (text: string) => void;
  onRetry?: (
    question: string,
    replaceTurnId: string,
    meta: { starterId?: string; categoryId?: string }
  ) => void;
  hideFollowUps?: boolean;
  streaming?: boolean;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const shouldAutoScroll = useRef(true);

  const lastUserIndex = (() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === "user") return i;
    }
    return -1;
  })();

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
      {messages.length === 0 && <DailyBusinessSummary />}
      {messages.map((m, i) => {
        const isLastAgent =
          m.role === "agent" && i === messages.length - 1 && !m.streaming;
        const isLastUser = i === lastUserIndex;
        const nextMsg = messages[i + 1];
        const canRetry =
          isLastUser &&
          nextMsg?.role === "agent" &&
          !nextMsg.streaming &&
          Boolean(nextMsg.turnId) &&
          Boolean(onRetry);

        return m.role === "user" ? (
          <UserMessage
            key={m.id}
            content={m.content}
            createdAt={m.createdAt}
            showRetry={canRetry}
            retryDisabled={streaming}
            onRetry={
              canRetry && nextMsg?.turnId
                ? () =>
                    onRetry!(m.content, nextMsg.turnId!, {
                      starterId: nextMsg.starterId,
                      categoryId: nextMsg.categoryId,
                    })
                : undefined
            }
          />
        ) : (
          <div key={m.id} className="max-w-4xl mx-auto w-full">
            <AgentMessage
              message={m}
              sessionId={sessionId}
              onClarificationPick={onClarificationPick}
            />
            {isLastAgent && sessionId && m.question && !m.clarification && (
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
