"use client";

import { useState, type FormEvent } from "react";
import { useQuestionCatalog } from "@/hooks/useQuestionCatalog";
import { CategoryGrid } from "./CategoryGrid";
import { StarterList } from "./StarterList";
import type { QuestionCategory, StarterQuestion } from "@/types/questionCatalog";

const INTENT_OPTIONS = [
  "",
  "aggregation",
  "trend",
  "comparison",
  "ranking",
  "lookup",
];

export function ExplorePanel({
  hasRepCode,
  onPickStarter,
  onSearchPick,
  onCategoryChange,
}: {
  hasRepCode: boolean;
  onPickStarter: (starter: StarterQuestion) => void;
  onSearchPick: (text: string) => void;
  onCategoryChange?: (category: QuestionCategory | null) => void;
}) {
  const {
    categories,
    starters,
    activeCategoryId,
    loading,
    error,
    selectCategory,
    search,
    clearCategory,
  } = useQuestionCatalog();
  const [searchQ, setSearchQ] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [filterIntent, setFilterIntent] = useState("");
  const [filterTable, setFilterTable] = useState("");
  const [searchMode, setSearchMode] = useState(false);
  const activeCategory = categories.find((c) => c.id === activeCategoryId);

  async function handleSearchSubmit(e: FormEvent) {
    e.preventDefault();
    setSearchMode(true);
    const hits = await search(searchQ.trim(), {
      category_id: filterCategory || undefined,
      intent: filterIntent || undefined,
      table_id: filterTable || undefined,
    });
    if (hits.length === 1) {
      onSearchPick(hits[0].text);
    }
  }

  return (
    <div className="py-6 px-4">
      <div className="text-center mb-6 max-w-xl mx-auto">
        <h2 className="text-lg font-semibold text-[var(--text)]">
          What would you like to explore?
        </h2>
        <p className="text-sm text-[var(--muted)] mt-1">
          Pick a category or search curated questions. Starters fill the input so you can edit
          before sending.
        </p>
        <p className="text-xs text-brand-400/90 mt-2">
          Or type your own question in the box below
        </p>
        <form onSubmit={handleSearchSubmit} className="mt-4 space-y-2 max-w-md mx-auto">
          <input
            type="search"
            value={searchQ}
            onChange={(e) => setSearchQ(e.target.value)}
            placeholder="Search starters…"
            className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-sm"
          />
          <div className="flex gap-2">
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--bg)] px-2 py-1.5 text-xs"
            >
              <option value="">All categories</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
            <select
              value={filterIntent}
              onChange={(e) => setFilterIntent(e.target.value)}
              className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--bg)] px-2 py-1.5 text-xs"
            >
              {INTENT_OPTIONS.map((i) => (
                <option key={i || "all"} value={i}>
                  {i ? i : "All intents"}
                </option>
              ))}
            </select>
            <select
              value={filterTable}
              onChange={(e) => setFilterTable(e.target.value)}
              className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--bg)] px-2 py-1.5 text-xs"
            >
              <option value="">All tables</option>
              <option value="fact_sales_report">fact_sales_report</option>
              <option value="fact_new_business_frazer">fact_new_business_frazer</option>
              <option value="dim_date">dim_date</option>
              <option value="stg_total_working_days">stg_total_working_days</option>
            </select>
          </div>
          <button
            type="submit"
            className="w-full px-3 py-2 rounded-lg bg-brand-600 text-white text-sm"
          >
            Search
          </button>
        </form>
      </div>

      {error && <p className="text-center text-sm text-red-400 mb-4">{error}</p>}
      {loading && !activeCategoryId && !searchMode && (
        <p className="text-center text-sm text-[var(--muted)]">Loading…</p>
      )}

      {searchMode && starters.length > 0 && !activeCategoryId ? (
        <StarterList
          starters={starters}
          categoryLabel="Search results"
          onBack={() => {
            setSearchQ("");
            setFilterCategory("");
            setFilterIntent("");
            setFilterTable("");
            setSearchMode(false);
            clearCategory();
          }}
          onPick={onPickStarter}
        />
      ) : activeCategoryId && starters.length > 0 ? (
        <>
          {activeCategoryId === "projections" && (
            <p className="max-w-xl mx-auto mb-4 text-xs text-amber-300/90 text-center px-4">
              Projection starters use a run-rate estimate from BigQuery actuals and working days —
              not the exact Power BI forecast measures.
            </p>
          )}
          {activeCategoryId === "targets" && (
            <p className="max-w-xl mx-auto mb-4 text-xs text-sky-300/90 text-center px-4">
              Targets are compared to FY goals from configured Office Supplies BI values, not a
              BigQuery budget table.
            </p>
          )}
        <StarterList
          starters={starters}
          categoryLabel={activeCategory?.label}
          onBack={() => {
            clearCategory();
            onCategoryChange?.(null);
          }}
          onPick={onPickStarter}
        />
        </>
      ) : (
        <CategoryGrid
          categories={categories}
          hasRepCode={hasRepCode}
          onSelect={(c: QuestionCategory) => {
            selectCategory(c.id);
            onCategoryChange?.(c);
            setSearchMode(false);
          }}
        />
      )}
    </div>
  );
}
