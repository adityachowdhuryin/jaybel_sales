"use client";

import { DataAvailabilityBadge } from "./DataAvailabilityBadge";
import type { StarterQuestion } from "@/types/questionCatalog";

export function FAQQuestionCard({
  starter,
  disabled,
  onPick,
}: {
  starter: StarterQuestion;
  disabled?: boolean;
  onPick: (starter: StarterQuestion) => void;
}) {
  return (
    <li>
      <button
        type="button"
        disabled={disabled}
        onClick={() => onPick(starter)}
        className={`w-full text-left rounded-xl border border-[var(--border)] bg-[var(--surface-0)] px-4 py-3.5 transition ${
          disabled
            ? "cursor-not-allowed opacity-60"
            : "hover:border-sky-300 hover:shadow-sm"
        }`}
      >
        <p className="text-sm text-[var(--text-primary)] leading-snug">{starter.text}</p>
        {starter.data_availability !== "full" && (
          <div className="mt-2">
            <DataAvailabilityBadge value={starter.data_availability} />
          </div>
        )}
      </button>
    </li>
  );
}
