"use client";

import { ArrowLeft } from "lucide-react";
import { ExplorePanel } from "./ExplorePanel";
import type { QuestionCategory } from "@/types/questionCatalog";

export function FAQFullScreen({
  hasRepCode,
  onClose,
  onPickStarter,
}: {
  hasRepCode: boolean;
  activeCategory?: QuestionCategory | null;
  onCategoryChange?: (category: QuestionCategory | null) => void;
  onClose: () => void;
  onPickStarter: (starter: import("@/types/questionCatalog").StarterQuestion) => void;
  onSearchPick?: (text: string) => void;
}) {
  return (
    <div className="h-full min-h-0 flex flex-col bg-[var(--bg)]">
      <div className="px-4 py-2.5 border-b border-[var(--border)] bg-[var(--surface-0)] shrink-0 flex justify-end">
        <button
          type="button"
          onClick={onClose}
          className="ui-btn-secondary px-3 py-1.5 text-xs"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to chat
        </button>
      </div>
      <div className="flex-1 min-h-0 overflow-y-auto">
        <ExplorePanel hasRepCode={hasRepCode} onPickStarter={onPickStarter} />
      </div>
    </div>
  );
}
