"use client";

import { useRef, useState } from "react";
import { submitTurnFeedback } from "@/lib/api";
import { AnswerMarkdown } from "./AnswerMarkdown";
import { ChartPanel } from "./ChartPanel";
import { CostWarning } from "./CostWarning";
import { DataTable } from "./DataTable";
import { DownloadBar } from "./DownloadBar";
import { MetricCards, shouldShowMetricCards } from "./MetricCards";
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
  const [saving, setSaving] = useState(false);
  const chartRef = useRef<HTMLDivElement>(null);

  const hasChart = Boolean(message.chartSpec);
  const hasTable = Boolean(message.rows?.length && message.rows.length > 1);
  const showKpis = shouldShowMetricCards(
    message.rows,
    hasChart,
    message.chartSpec?.chart_type
  );
  const answerReady = !message.streaming && !message.error && message.content;

  async function handleFeedback(value: number) {
    if (!sessionId || !message.turnId || saving) return;
    setSaving(true);
    try {
      await submitTurnFeedback(sessionId, message.turnId, value);
      setRating(value);
      onFeedbackChange?.(value);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mb-8 max-w-4xl mx-auto w-full animate-fade-in">
      <div className="rounded-2xl rounded-bl-md border border-[var(--border)] bg-[var(--surface-0)] shadow-panel overflow-hidden">
        <div className="h-1 w-full bg-gradient-to-r from-sky-500 via-cyan-500 to-violet-500" />
        <div className="px-4 py-3 sm:px-5 sm:py-4">
          <StatusIndicator message={message.status} />
          {showTableLabel && (
            <p className="text-xs font-medium text-[var(--text-tertiary)] mb-2">
              Source: <span className="text-sky-700 font-semibold">{message.tableDisplay}</span>
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
          {showKpis && !message.streaming && (
            <MetricCards
              rows={message.rows}
              columns={message.columns}
              currencyContext={[message.question, message.content].filter(Boolean).join(" ")}
            />
          )}

          {message.error ? (
            <p className="text-sm text-[var(--intent-danger)]">{message.error}</p>
          ) : message.streaming ? (
            <StreamingText content={message.content} streaming />
          ) : answerReady ? (
            <AnswerMarkdown content={message.content} />
          ) : (
            <StreamingText content={message.content} />
          )}

          <div className="mt-3 space-y-3">
            {hasTable && (
              <DataTable
                rows={message.rows}
                columns={message.columns}
                rowCount={message.rowCount}
                tableDisplay={message.tableDisplay}
              />
            )}
            {hasChart && message.chartSpec && (
              <div ref={chartRef}>
                <ChartPanel spec={message.chartSpec} rows={message.rows} />
              </div>
            )}
          </div>
          <DownloadBar message={message} chartRef={chartRef} />
        </div>
      </div>
      <div className="flex items-center gap-3 mt-2 pl-1 max-w-4xl mx-auto">
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
                  ? "bg-emerald-500/15 text-emerald-700"
                  : "text-[var(--muted)] hover:bg-[var(--surface-2)] hover:text-emerald-700"
              }`}
              aria-label="Helpful"
            >
              👍
            </button>
            <button
              type="button"
              disabled={saving}
              onClick={() => handleFeedback(-1)}
              className={`text-xs px-2 py-1 rounded-md transition ${
                rating === -1
                  ? "bg-rose-500/15 text-rose-700"
                  : "text-[var(--muted)] hover:bg-[var(--surface-2)] hover:text-rose-700"
              }`}
              aria-label="Not helpful"
            >
              👎
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
