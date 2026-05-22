"use client";

import { ExplorePanel } from "./ExplorePanel";
import type { QuestionCategory } from "@/types/questionCatalog";

export function ExploreDrawer({
  open,
  onClose,
  hasRepCode,
  activeCategory,
  onCategoryChange,
  onPickStarter,
  onSearchPick,
}: {
  open: boolean;
  onClose: () => void;
  hasRepCode: boolean;
  activeCategory: QuestionCategory | null;
  onCategoryChange?: (category: QuestionCategory | null) => void;
  onPickStarter: (starter: import("@/types/questionCatalog").StarterQuestion) => void;
  onSearchPick: (text: string) => void;
}) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-40 flex justify-end"
      role="dialog"
      aria-label="Browse questions"
    >
      <button
        type="button"
        className="flex-1 bg-black/50"
        onClick={onClose}
        aria-label="Close explore"
      />
      <div className="w-full max-w-lg h-full bg-[var(--bg)] border-l border-[var(--border)] shadow-xl flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)] shrink-0">
          <div className="text-xs text-[var(--muted)]">
            <span className="text-brand-400">Explore</span>
            {activeCategory && (
              <>
                {" "}
                / <span className="text-[var(--text)]">{activeCategory.label}</span>
              </>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-sm text-[var(--muted)] hover:text-[var(--text)]"
          >
            Close
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          <ExplorePanel
            hasRepCode={hasRepCode}
            onCategoryChange={onCategoryChange}
            onPickStarter={(s) => {
              onPickStarter(s);
              onClose();
            }}
            onSearchPick={(t) => {
              onSearchPick(t);
              onClose();
            }}
          />
        </div>
      </div>
    </div>
  );
}
