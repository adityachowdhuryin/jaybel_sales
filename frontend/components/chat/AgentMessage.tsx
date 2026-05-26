"use client";

import { useState } from "react";
import { submitTurnFeedback } from "@/lib/api";
import { AnswerMarkdown } from "./AnswerMarkdown";
import { ChartPanel } from "./ChartPanel";
import { CostWarning } from "./CostWarning";
import { DataTable } from "./DataTable";
import { DownloadBar } from "./DownloadBar";
import { MetricCards, shouldShowMetricCards } from "./MetricCards";
import { SQLAccordion } from "./SQLAccordion";
import { StatusIndicator } from "./StatusIndicator";
import { StreamingText } from "./StreamingText";
import { ClarificationCard } from "./ClarificationCard";
import { GuidanceBanner } from "./GuidanceBanner";
import type { ChatMessage } from "@/types";

function formatTime(iso?: string) {
  if (!iso) return null;
  try {
    return new Date(iso).toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return null;
  }
}

export function AgentMessage({
  message,
  sessionId,
  onFeedbackChange,
  onClarificationPick,
}: {
  message: ChatMessage;
  sessionId?: string | null;
  onFeedbackChange?: (rating: number) => void;
  onClarificationPick?: (sendText: string) => void;
}) {
  const time = formatTime(message.createdAt);
  const showTableLabel = message.tableDisplay && !message.status && !message.streaming;
  const [rating, setRating] = useState<number | null>(message.feedbackRating ?? null);
  const [comment, setComment] = useState("");
  const [showComment, setShowComment] = useState(false);
  const [saving, setSaving] = useState(false);

  const hasChart = Boolean(message.chartSpec);
  const hasTable = Boolean(message.rows?.length && message.rows.length > 1);
  const showKpis = shouldShowMetricCards(
    message.rows,
    hasChart,
    message.chartSpec?.chart_type
  );
  const splitView = hasChart && hasTable && !message.streaming;
  const answerReady = !message.streaming && !message.error && message.content;

  async function handleFeedback(value: number) {
    if (!sessionId || !message.turnId || saving) return;
    setSaving(true);
    try {
      await submitTurnFeedback(
        sessionId,
        message.turnId,
        value,
        comment.trim() || undefined
      );
      setRating(value);
      onFeedbackChange?.(value);
      setShowComment(false);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mb-8 max-w-4xl animate-fade-in">
      <div className="rounded-2xl rounded-bl-md border border-[var(--border)] bg-[var(--panel)] shadow-panel overflow-hidden border-l-4 border-l-brand-500/70">
        <div className="px-4 py-3 sm:px-5 sm:py-4">
          <StatusIndicator message={message.status} />
          {showTableLabel && (
            <p className="text-[11px] font-medium text-[var(--muted)] mb-2">
              Source: <span className="text-brand-300">{message.tableDisplay}</span>
            </p>
          )}
          <CostWarning bytes={message.costWarningBytes} />
          {message.guidance && (
            <GuidanceBanner
              code={message.guidance.code}
              message={message.guidance.message}
              suggestions={message.guidance.suggestions}
            />
          )}
          {message.clarification && onClarificationPick && !message.streaming && (
            <ClarificationCard
              message={message.clarification.message}
              options={message.clarification.options}
              onPick={onClarificationPick}
            />
          )}
          {message.error ? (
            <p className="text-sm text-red-400">{message.error}</p>
          ) : message.streaming ? (
            <StreamingText content={message.content} streaming />
          ) : answerReady ? (
            <AnswerMarkdown content={message.content} />
          ) : (
            <StreamingText content={message.content} />
          )}

          {showKpis && !message.streaming && (
            <MetricCards rows={message.rows} columns={message.columns} />
          )}

          <SQLAccordion sql={message.sql} />

          <div
            className={
              splitView
                ? "sticky top-0 z-10 grid lg:grid-cols-2 gap-4 mt-4 max-h-[min(440px,55vh)] overflow-auto"
                : "mt-3 space-y-3"
            }
          >
            {hasChart && message.chartSpec && (
              <ChartPanel spec={message.chartSpec} rows={message.rows} />
            )}
            {hasTable && (
              <DataTable
                rows={message.rows}
                columns={message.columns}
                rowCount={message.rowCount}
                tableDisplay={message.tableDisplay}
              />
            )}
          </div>
          <DownloadBar message={message} />
        </div>
      </div>
      <div className="flex items-center gap-3 mt-2 pl-1">
        {time && !message.streaming && (
          <p className="text-[10px] text-[var(--muted)]">{time}</p>
        )}
        {sessionId && message.turnId && !message.streaming && (
          <div className="flex gap-1">
            <button
              type="button"
              disabled={saving}
              onClick={() => handleFeedback(1)}
              className={`text-xs px-2 py-1 rounded-md transition ${
                rating === 1
                  ? "bg-emerald-500/20 text-emerald-300"
                  : "text-[var(--muted)] hover:bg-[var(--bg-elevated)] hover:text-emerald-300"
              }`}
              aria-label="Helpful"
            >
              👍
            </button>
            <button
              type="button"
              disabled={saving}
              onClick={() => {
                setShowComment(true);
                handleFeedback(-1);
              }}
              className={`text-xs px-2 py-1 rounded-md transition ${
                rating === -1
                  ? "bg-red-500/20 text-red-300"
                  : "text-[var(--muted)] hover:bg-[var(--bg-elevated)] hover:text-red-300"
              }`}
              aria-label="Not helpful"
            >
              👎
            </button>
            <button
              type="button"
              onClick={() => setShowComment((v) => !v)}
              className="text-[10px] text-[var(--muted)] hover:text-brand-300 px-1"
            >
              Comment
            </button>
          </div>
        )}
        {showComment && sessionId && message.turnId && (
          <div className="mt-2 pl-1 max-w-md w-full">
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={2}
              placeholder="Optional feedback…"
              className="w-full text-xs rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2 focus:outline-none focus:ring-1 focus:ring-brand-500/50"
            />
            <button
              type="button"
              disabled={saving || rating === null}
              onClick={() => rating !== null && handleFeedback(rating)}
              className="mt-1 text-[10px] font-medium text-brand-400 hover:text-brand-300"
            >
              Save comment
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
