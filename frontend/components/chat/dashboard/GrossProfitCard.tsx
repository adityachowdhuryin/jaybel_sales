import { ArrowDown } from "lucide-react";
import { formatCompactCurrency, formatFyLabel } from "@/lib/formatCompact";
import { formatNumber } from "@/lib/formatters";
import type { GrossProfitSummary } from "@/types/dashboard";
import { SummaryCard } from "./SummaryCard";

export function GrossProfitCard({ data }: { data: GrossProfitSummary }) {
  const gpDown = data.gp_variance_dollars < 0;
  return (
    <SummaryCard title="Gross profit">
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg bg-[var(--surface-1)] p-3">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--text-tertiary)]">
            {formatFyLabel("2025-2026")}
          </p>
          <p className="mt-1 text-xl font-bold text-[var(--text-primary)] tabular-nums">
            {formatCompactCurrency(data.current_gp)}
          </p>
          <p className="text-xs text-[var(--text-tertiary)] tabular-nums">
            GP$ · {formatNumber(data.current_gp_pct, 2)}% GP%
          </p>
          <p
            className={`mt-2 inline-flex items-center gap-0.5 text-xs font-medium tabular-nums ${
              gpDown ? "text-[var(--intent-danger)]" : "text-[var(--intent-success)]"
            }`}
          >
            {gpDown && <ArrowDown className="w-3 h-3" />}
            {formatCompactCurrency(data.gp_variance_dollars)} vs LY
          </p>
        </div>
        <div className="rounded-lg bg-[var(--surface-1)] p-3">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--text-tertiary)]">
            {formatFyLabel("2024-2025")}
          </p>
          <p className="mt-1 text-xl font-bold text-[var(--text-primary)] tabular-nums">
            {formatCompactCurrency(data.prior_gp)}
          </p>
          <p className="text-xs text-[var(--text-tertiary)] mt-0.5 tabular-nums">
            GP$ · {formatNumber(data.prior_gp_pct, 2)}% GP%
          </p>
        </div>
      </div>
    </SummaryCard>
  );
}
