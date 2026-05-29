import { ArrowDown, ArrowUp } from "lucide-react";
import { formatCompactCurrency, formatCompactPercent, formatFyLabel } from "@/lib/formatCompact";
import type { SalesPerformance } from "@/types/dashboard";
import { SummaryCard } from "./SummaryCard";

export function SalesPerformanceCard({ data }: { data: SalesPerformance }) {
  const down = data.yoy_pct < 0;
  return (
    <SummaryCard title="Sales Performance">
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg bg-[var(--surface-1)] p-3">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--text-tertiary)]">
            {formatFyLabel(data.current_fy)}
          </p>
          <p className="mt-1 text-xl font-bold text-[var(--text-primary)] tabular-nums">
            {formatCompactCurrency(data.current_sales)}
          </p>
          <p className="text-xs text-[var(--text-tertiary)] mt-0.5">Total Sales</p>
          <p
            className={`mt-2 inline-flex items-center gap-0.5 text-xs font-medium tabular-nums ${
              down ? "text-[var(--intent-danger)]" : "text-[var(--intent-success)]"
            }`}
          >
            {down ? <ArrowDown className="w-3 h-3" /> : <ArrowUp className="w-3 h-3" />}
            {formatCompactPercent(data.yoy_pct)} vs LY
          </p>
        </div>
        <div className="rounded-lg bg-[var(--surface-1)] p-3">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--text-tertiary)]">
            {formatFyLabel(data.prior_fy)}
          </p>
          <p className="mt-1 text-xl font-bold text-[var(--text-primary)] tabular-nums">
            {formatCompactCurrency(data.prior_sales)}
          </p>
          <p className="text-xs text-[var(--text-tertiary)] mt-0.5">Total sales</p>
        </div>
      </div>
    </SummaryCard>
  );
}
