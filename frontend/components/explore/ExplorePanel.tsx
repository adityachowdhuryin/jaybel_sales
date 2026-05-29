"use client";

import { useMemo, useState } from "react";
import { BarChart3, Search } from "lucide-react";
import { useFaqCatalog } from "@/hooks/useFaqCatalog";
import { FAQQuestionCard } from "./FAQQuestionCard";
import type { QuestionCategory, StarterQuestion } from "@/types/questionCatalog";

const CHIP_LABELS: Record<string, string> = {
  executive_kpi: "Executive & KPIs",
  product: "Product & Category",
  customer: "Customers",
  retention: "Customer Retention",
  orders: "Orders & Line Items",
  sales_rep: "My Performance",
  targets: "Targets",
  projections: "Forecasting",
};

function sectionHeading(category: QuestionCategory): string {
  return (CHIP_LABELS[category.id] ?? category.label).toUpperCase();
}

export function ExplorePanel({
  hasRepCode,
  onPickStarter,
}: {
  hasRepCode: boolean;
  onPickStarter: (starter: StarterQuestion) => void;
  onSearchPick?: (text: string) => void;
  onCategoryChange?: (category: QuestionCategory | null) => void;
}) {
  const { categories, starters, loading, error } = useFaqCatalog();
  const [searchQ, setSearchQ] = useState("");
  const [activeChip, setActiveChip] = useState<string>("all");

  const filteredStarters = useMemo(() => {
    const q = searchQ.trim().toLowerCase();
    return starters.filter((s) => {
      if (activeChip !== "all" && s.category_id !== activeChip) return false;
      if (q && !s.text.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [starters, searchQ, activeChip]);

  const visibleCategories = useMemo(() => {
    const ids = new Set(filteredStarters.map((s) => s.category_id));
    return categories.filter((c) => ids.has(c.id));
  }, [categories, filteredStarters]);

  return (
    <div className="py-8 px-4 pb-16">
      <div className="max-w-2xl mx-auto">
        <header className="text-center mb-8">
          <div className="inline-flex items-center gap-2.5 mb-8">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--chat-send-bg)]">
              <BarChart3 className="h-5 w-5 text-white" strokeWidth={2.25} />
            </div>
            <span className="text-lg font-semibold text-[var(--text-primary)]">
              Jaybel Analytics
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[var(--text-primary)]">
            What would you like to explore?
          </h1>
          <p className="mt-2 text-sm text-[var(--text-tertiary)]">
            Click a question to ask it, or type your own.
          </p>
        </header>

        <div className="relative mb-4">
          <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-tertiary)]" />
          <input
            type="search"
            value={searchQ}
            onChange={(e) => setSearchQ(e.target.value)}
            placeholder="Search questions…"
            className="w-full rounded-full border border-[var(--border)] bg-[var(--surface-0)] py-3 pl-11 pr-4 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] outline-none focus:ring-2 focus:ring-sky-200"
          />
        </div>

        <div className="flex flex-wrap gap-2 mb-8">
          <button
            type="button"
            onClick={() => setActiveChip("all")}
            className={`rounded-full border px-3.5 py-1.5 text-sm font-medium transition ${
              activeChip === "all"
                ? "border-[var(--chat-send-bg)] text-[var(--chat-send-bg)] bg-[var(--surface-0)]"
                : "border-[var(--border)] text-[var(--text-secondary)] bg-[var(--surface-0)] hover:border-sky-200"
            }`}
          >
            All
          </button>
          {categories.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => setActiveChip(c.id)}
              className={`rounded-full border px-3.5 py-1.5 text-sm font-medium transition ${
                activeChip === c.id
                  ? "border-[var(--chat-send-bg)] text-[var(--chat-send-bg)] bg-[var(--surface-0)]"
                  : "border-[var(--border)] text-[var(--text-secondary)] bg-[var(--surface-0)] hover:border-sky-200"
              }`}
            >
              {CHIP_LABELS[c.id] ?? c.label}
            </button>
          ))}
        </div>

        {error && <p className="text-center text-sm text-red-600 mb-4">{error}</p>}
        {loading && (
          <p className="text-center text-sm text-[var(--muted)]">Loading questions…</p>
        )}

        {!loading && filteredStarters.length === 0 && (
          <p className="text-center text-sm text-[var(--muted)]">No questions match your search.</p>
        )}

        {!loading &&
          visibleCategories.map((category) => {
            const items = filteredStarters.filter((s) => s.category_id === category.id);
            if (!items.length) return null;
            const needsRep = category.requires_rep_code && !hasRepCode;
            return (
              <section key={category.id} className="mb-8">
                <h2 className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">
                  {sectionHeading(category)}
                </h2>
                <ul className="space-y-2">
                  {items.map((s) => (
                    <FAQQuestionCard
                      key={s.id}
                      starter={s}
                      disabled={needsRep}
                      onPick={onPickStarter}
                    />
                  ))}
                </ul>
                {needsRep && (
                  <p className="mt-2 text-xs text-[var(--status-warning-text)]">
                    Set your sales rep code in Settings to use these questions.
                  </p>
                )}
              </section>
            );
          })}
      </div>
    </div>
  );
}
