"use client";

import { useState } from "react";
import { useFollowUps } from "@/hooks/useFollowUps";
import { DataAvailabilityBadge } from "@/components/explore/DataAvailabilityBadge";

const VISIBLE = 5;

export function FollowUpChips({
  sessionId,
  turnId,
  question,
  starterId,
  onPick,
  hidden,
}: {
  sessionId: string;
  turnId?: string;
  question: string;
  starterId?: string;
  onPick: (text: string) => void;
  hidden?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const { items, source, loading } = useFollowUps({
    sessionId,
    turnId,
    question,
    starterId,
    enabled: !hidden && Boolean(turnId),
  });

  if (hidden || loading || !items.length) return null;

  const visible = expanded ? items : items.slice(0, VISIBLE);
  const hasMore = items.length > VISIBLE;

  return (
    <div className="mt-3 pl-1">
      <p className="text-[10px] uppercase tracking-wide text-[var(--muted)] mb-2">
        Suggested follow-ups{source ? ` · ${source}` : ""}
      </p>
      <div className="flex flex-wrap gap-2">
        {visible.map((f) => (
          <button
            key={f.id}
            type="button"
            onClick={() => onPick(f.text)}
            className="inline-flex items-center gap-2 max-w-full rounded-full border border-[var(--border)] bg-[var(--bg)] px-3 py-1.5 text-xs hover:border-brand-500/50 text-left"
          >
            <span className="truncate">{f.text}</span>
            {f.data_availability && f.data_availability !== "full" && (
              <DataAvailabilityBadge value={f.data_availability} />
            )}
          </button>
        ))}
      </div>
      {hasMore && !expanded && (
        <button
          type="button"
          onClick={() => setExpanded(true)}
          className="mt-2 text-xs text-brand-400 hover:text-brand-300"
        >
          Show {items.length - VISIBLE} more
        </button>
      )}
    </div>
  );
}
