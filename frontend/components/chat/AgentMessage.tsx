"use client";

import { useState } from "react";
import { submitTurnFeedback } from "@/lib/api";
import { ChartPanel } from "./ChartPanel";
import { CostWarning } from "./CostWarning";
import { DataTable } from "./DataTable";
import { DownloadBar } from "./DownloadBar";
import { SQLAccordion } from "./SQLAccordion";
import { StatusIndicator } from "./StatusIndicator";
import { StreamingText } from "./StreamingText";
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
}: {
  message: ChatMessage;
  sessionId?: string | null;
  onFeedbackChange?: (rating: number) => void;
}) {
  const time = formatTime(message.createdAt);
  const showTableLabel = message.tableDisplay && !message.status && !message.streaming;
  const [rating, setRating] = useState<number | null>(message.feedbackRating ?? null);
  const [comment, setComment] = useState("");
  const [showComment, setShowComment] = useState(false);
  const [saving, setSaving] = useState(false);

  const hasChart = Boolean(message.chartSpec);
  const hasTable = Boolean(message.rows?.length);
  const splitView = hasChart && hasTable && !message.streaming;

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
    <div className="mb-6 max-w-[95%]">
      <div className="rounded-2xl rounded-bl-md border border-[var(--border)] bg-[var(--panel)] px-4 py-3">
        <StatusIndicator message={message.status} />
        {showTableLabel && (
          <p className="text-xs text-[var(--muted)] mb-2">Table: {message.tableDisplay}</p>
        )}
        <CostWarning bytes={message.costWarningBytes} />
        {message.error ? (
          <p className="text-sm text-red-400">{message.error}</p>
        ) : (
          <StreamingText content={message.content} streaming={message.streaming} />
        )}
        <SQLAccordion sql={message.sql} />
        <div
          className={
            splitView
              ? "sticky top-0 z-10 grid lg:grid-cols-2 gap-4 mt-3 max-h-[min(420px,50vh)] overflow-auto"
              : ""
          }
        >
          {hasChart && message.chartSpec && (
            <ChartPanel spec={message.chartSpec} rows={message.rows} />
          )}
          <DataTable
            rows={message.rows}
            columns={message.columns}
            rowCount={message.rowCount}
            tableDisplay={message.tableDisplay}
          />
        </div>
        <DownloadBar message={message} />
      </div>
      <div className="flex items-center gap-3 mt-1 pl-1">
        {time && !message.streaming && (
          <p className="text-[10px] text-[var(--muted)]">{time}</p>
        )}
        {sessionId && message.turnId && !message.streaming && (
          <div className="flex gap-1">
            <button
              type="button"
              disabled={saving}
              onClick={() => handleFeedback(1)}
              className={`text-xs px-1.5 py-0.5 rounded ${
                rating === 1 ? "text-emerald-400" : "text-[var(--muted)] hover:text-emerald-300"
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
              className={`text-xs px-1.5 py-0.5 rounded ${
                rating === -1 ? "text-red-400" : "text-[var(--muted)] hover:text-red-300"
              }`}
              aria-label="Not helpful"
            >
              👎
            </button>
            <button
              type="button"
              onClick={() => setShowComment((v) => !v)}
              className="text-[10px] text-[var(--muted)] hover:text-brand-300"
            >
              Comment
            </button>
          </div>
        )}
        {showComment && sessionId && message.turnId && (
          <div className="mt-2 pl-1 max-w-md">
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={2}
              placeholder="Optional feedback…"
              className="w-full text-xs rounded border border-[var(--border)] bg-[var(--bg)] px-2 py-1"
            />
            <button
              type="button"
              disabled={saving || rating === null}
              onClick={() => rating !== null && handleFeedback(rating)}
              className="mt-1 text-[10px] text-brand-400"
            >
              Save comment
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
