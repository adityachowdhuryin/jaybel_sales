import { formatCurrency, formatNumber } from "@/lib/formatters";
import type { YesterdaySales } from "@/types/dashboard";
import { SummaryCard } from "./SummaryCard";

function StatusPill({ label, tone }: { label: string; tone: "good" | "bad" }) {
  return (
    <span
      className={`shrink-0 rounded-full px-2.5 py-0.5 text-[10px] font-semibold ${
        tone === "good"
          ? "bg-emerald-500/15 text-emerald-700"
          : "bg-rose-500/15 text-rose-700"
      }`}
    >
      {label}
    </span>
  );
}

export function YesterdaySalesCard({ data }: { data: YesterdaySales }) {
  return (
    <SummaryCard title="Yesterdays Sales">
      <div className="space-y-2">
        <div className="flex items-center justify-between rounded-lg bg-[var(--surface-1)] px-3 py-2.5">
          <div>
            <p className="text-xs text-[var(--text-tertiary)]">Sales</p>
            <p className="text-sm font-bold text-[var(--text-primary)] tabular-nums">
              {formatCurrency(data.sales)}
            </p>
          </div>
          <StatusPill
            label={data.sales_status}
            tone={data.sales_status === "Good" ? "good" : "bad"}
          />
        </div>
        <div className="flex items-center justify-between rounded-lg bg-[var(--surface-1)] px-3 py-2.5">
          <div>
            <p className="text-xs text-[var(--text-tertiary)]">Gross profit $</p>
            <p className="text-sm font-bold text-[var(--text-primary)] tabular-nums">
              {formatCurrency(data.gp_dollar)}
            </p>
          </div>
        </div>
        <div className="flex items-center justify-between rounded-lg bg-[var(--surface-1)] px-3 py-2.5">
          <div>
            <p className="text-xs text-[var(--text-tertiary)]">GP%</p>
            <p className="text-sm font-bold text-[var(--text-primary)] tabular-nums">
              {formatNumber(data.gp_pct, 2)}%
            </p>
            <p className="text-[10px] text-[var(--text-tertiary)]">
              vs {formatNumber(data.fy_avg_gp_pct, 2)}% FY avg
            </p>
          </div>
          <StatusPill
            label={data.gp_status}
            tone={data.gp_status === "Good" ? "good" : "bad"}
          />
        </div>
      </div>
    </SummaryCard>
  );
}
