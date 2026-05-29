"use client";

import { X } from "lucide-react";
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
        className="flex-1 bg-slate-900/25 backdrop-blur-sm"
        onClick={onClose}
        aria-label="Close explore"
      />
      <div className="w-full max-w-lg h-full bg-[var(--surface-0)] backdrop-blur-md border-l border-[var(--border)] shadow-2xl flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-4 py-4 border-b border-[var(--border)] shrink-0 bg-[var(--surface-0)] shadow-sm">
          <div className="text-sm font-medium text-[var(--muted)]">
            <span className="text-sky-700">Explore questions</span>
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
            className="p-2 rounded-lg text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--bg-elevated)] transition"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          <ExplorePanel
            hasRepCode={hasRepCode}
            onPickStarter={(s) => {
              onPickStarter(s);
              onClose();
            }}
          />
        </div>
      </div>
    </div>
  );
}
