"use client";

import {
  BarChart3,
  Calendar,
  FileText,
  Flag,
  Package,
  RefreshCw,
  Sparkles,
  TrendingUp,
  User,
  Users,
  Wallet,
  type LucideIcon,
} from "lucide-react";
import type { QuestionCategory } from "@/types/questionCatalog";

const ICONS: Record<string, LucideIcon> = {
  "chart-bar": BarChart3,
  currency: Wallet,
  cube: Package,
  users: Users,
  "arrow-path": RefreshCw,
  sparkles: Sparkles,
  user: User,
  flag: Flag,
  "trending-up": TrendingUp,
  document: FileText,
  calendar: Calendar,
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
        const Icon = ICONS[c.icon] ?? BarChart3;
        return (
          <button
            key={c.id}
            type="button"
            disabled={needsRep}
            onClick={() => onSelect(c)}
            className={`group text-left rounded-xl border border-[var(--border)] bg-[var(--panel)] p-4 transition-all ${
              needsRep
                ? "cursor-not-allowed bg-[var(--surface-1)] text-[var(--text-tertiary)]"
                : "hover:border-sky-300 hover:bg-[var(--surface-accent)] hover:shadow-panel"
            }`}
          >
            <div
              className={`inline-flex p-2 rounded-lg ${
                needsRep ? "bg-[var(--surface-2)] text-[var(--text-tertiary)]" : "bg-sky-100 text-sky-700"
              }`}
            >
              <Icon className="w-5 h-5" aria-hidden />
            </div>
            <h3 className="mt-3 text-sm font-semibold text-[var(--text)] group-hover:text-brand-700 transition">
              {c.label}
            </h3>
            <p className="mt-1 text-xs text-[var(--muted)] line-clamp-2 leading-relaxed">
              {c.description}
            </p>
            <p className="mt-2 text-[10px] font-medium text-[var(--muted)]">
              {c.starter_count ?? 0} starters
            </p>
            {needsRep && (
              <p className="mt-1 text-[10px] text-[var(--status-warning-text)]">
                Set rep code in sidebar first
              </p>
            )}
          </button>
        );
      })}
    </div>
  );
}
