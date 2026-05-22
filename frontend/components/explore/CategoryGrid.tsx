"use client";

import type { QuestionCategory } from "@/types/questionCatalog";

const ICONS: Record<string, string> = {
  "chart-bar": "📊",
  currency: "💰",
  cube: "📦",
  users: "👥",
  "arrow-path": "🔄",
  sparkles: "✨",
  user: "🧑",
  flag: "🎯",
  "trending-up": "📈",
  document: "📄",
  calendar: "📅",
};

export function CategoryGrid({
  categories,
  hasRepCode,
  onSelect,
}: {
  categories: QuestionCategory[];
  hasRepCode: boolean;
  onSelect: (category: QuestionCategory) => void;
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 max-w-4xl mx-auto">
      {categories.map((c) => {
        const needsRep = c.requires_rep_code && !hasRepCode;
        return (
          <button
            key={c.id}
            type="button"
            disabled={needsRep}
            onClick={() => onSelect(c)}
            className={`text-left rounded-xl border border-[var(--border)] bg-[var(--panel)] p-4 transition ${
              needsRep
                ? "opacity-60 cursor-not-allowed"
                : "hover:border-brand-500/50 hover:bg-brand-600/5"
            }`}
          >
            <span className="text-2xl" aria-hidden>
              {ICONS[c.icon] ?? "❓"}
            </span>
            <h3 className="mt-2 text-sm font-semibold text-[var(--text)]">{c.label}</h3>
            <p className="mt-1 text-xs text-[var(--muted)] line-clamp-2">{c.description}</p>
            <p className="mt-2 text-[10px] text-[var(--muted)]">
              {c.starter_count ?? 0} starter questions
            </p>
            {needsRep && (
              <p className="mt-1 text-[10px] text-amber-400">Set rep code in sidebar first</p>
            )}
          </button>
        );
      })}
    </div>
  );
}
