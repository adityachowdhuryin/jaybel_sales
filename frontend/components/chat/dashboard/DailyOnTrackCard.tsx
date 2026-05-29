import { formatCompactCurrency } from "@/lib/formatCompact";
import { formatCurrency, formatNumber } from "@/lib/formatters";
import type { MonthlyOnTrack } from "@/types/dashboard";
import { SummaryCard } from "./SummaryCard";

function ProgressRow({
  label,
  value,
  pct,
  tone,
}: {
  label: string;
  value: string;
  pct: number;
  tone: "green" | "blue";
}) {
  const bar =
    tone === "green" ? "bg-[var(--intent-success)]" : "bg-[var(--chat-send-bg)]";
  return (
    <div>
      <div className="flex justify-between text-xs text-[var(--text-secondary)] mb-1">
        <span>{label}</span>
        <span className="tabular-nums">
          {value}{" "}
          <span className="text-[var(--text-tertiary)]">{formatNumber(pct, 0)}%</span>
        </span>
      </div>
      <div className="h-2 rounded-full bg-[var(--surface-2)] overflow-hidden">
        <div
          className={`h-full rounded-full ${bar}`}
          style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
        />
      </div>
    </div>
  );
}

export function DailyOnTrackCard({ data }: { data: MonthlyOnTrack }) {
  return (
    <SummaryCard title="Daily average and monthly on-track check">
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="rounded-lg bg-[var(--surface-1)] p-2.5 text-center">
          <p className="text-[10px] text-[var(--text-tertiary)] leading-tight">
            Daily avg
            <br />
            (this month)
          </p>
          <p className="mt-1 text-sm font-bold text-[var(--text-primary)] tabular-nums">
            {formatCurrency(data.daily_avg_mtd)}
          </p>
          <p className="text-[10px] text-[var(--text-tertiary)]">{data.days_completed} days done</p>
        </div>
        <div className="rounded-lg bg-[var(--surface-1)] p-2.5 text-center">
          <p className="text-[10px] text-[var(--text-tertiary)] leading-tight">
            Daily avg
            <br />
            needed
          </p>
          <p className="mt-1 text-sm font-bold text-[var(--text-primary)] tabular-nums">
            {formatCurrency(data.daily_avg_needed)}
          </p>
          <p className="text-[10px] text-[var(--text-tertiary)]">{data.days_remaining} days left</p>
        </div>
        <div className="rounded-lg bg-[var(--surface-1)] p-2.5 text-center">
          <p className="text-[10px] text-[var(--text-tertiary)]">Monthly target</p>
          <p className="mt-1 text-sm font-bold text-[var(--text-primary)] tabular-nums">
            {formatCompactCurrency(data.monthly_target)}
          </p>
          <p className="text-[10px] text-[var(--text-tertiary)]">100%</p>
        </div>
      </div>
      <div className="space-y-3">
        <ProgressRow
          label="Closed MTD"
          value={formatCompactCurrency(data.closed_mtd)}
          pct={data.closed_mtd_pct}
          tone="green"
        />
        <ProgressRow
          label="Projected to close"
          value={formatCompactCurrency(data.projected_close)}
          pct={data.projected_pct}
          tone="blue"
        />
      </div>
      <p className="mt-3 text-[10px] text-[var(--text-tertiary)]">
        Projected figures use run-rate estimate (MTD actuals ÷ completed working days × month
        working days).
      </p>
    </SummaryCard>
  );
}
