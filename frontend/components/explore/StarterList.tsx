"use client";

import { DataAvailabilityBadge } from "./DataAvailabilityBadge";
import type { StarterQuestion } from "@/types/questionCatalog";

export function StarterList({
  starters,
  categoryLabel,
  onBack,
  onPick,
}: {
  starters: StarterQuestion[];
  categoryLabel?: string;
  onBack: () => void;
  onPick: (starter: StarterQuestion) => void;
}) {
  return (
    <div className="max-w-3xl mx-auto w-full">
      <div className="flex items-center gap-2 mb-4">
        <button
          type="button"
          onClick={onBack}
          className="text-xs text-brand-400 hover:text-brand-300"
        >
          ← Categories
        </button>
        {categoryLabel && (
          <span className="text-xs text-[var(--muted)]">/ {categoryLabel}</span>
        )}
      </div>
      <ul className="space-y-2">
        {starters.map((s) => (
          <li key={s.id}>
            <button
              type="button"
              onClick={() => onPick(s)}
              className="w-full text-left rounded-xl border border-[var(--border)] bg-[var(--panel)] px-4 py-3 hover:border-brand-500/40 hover:bg-brand-600/5"
            >
              <div className="flex flex-wrap items-start gap-2 justify-between">
                <p className="text-sm text-[var(--text)] flex-1 min-w-0">{s.text}</p>
                <DataAvailabilityBadge value={s.data_availability} />
              </div>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
