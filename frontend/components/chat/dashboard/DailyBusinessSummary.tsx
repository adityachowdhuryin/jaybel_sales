"use client";

import { useDailySummary } from "@/hooks/useDailySummary";
import { DailyOnTrackCard } from "./DailyOnTrackCard";
import { GrossProfitCard } from "./GrossProfitCard";
import { SalesPerformanceCard } from "./SalesPerformanceCard";
import { YesterdaySalesCard } from "./YesterdaySalesCard";

function SummarySkeleton() {
  return (
    <div className="max-w-4xl mx-auto w-full animate-pulse space-y-4">
      <div className="h-6 w-64 bg-[var(--surface-2)] rounded" />
      <div className="grid gap-4 md:grid-cols-2">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-40 bg-[var(--surface-2)] rounded-xl" />
        ))}
      </div>
    </div>
  );
}

export function DailyBusinessSummary() {
  const { data, loading, error } = useDailySummary();

  if (loading) {
    return (
      <div className="py-4">
        <SummarySkeleton />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-lg mx-auto text-center py-12 px-4">
        <p className="text-sm text-[var(--intent-danger)] mb-2">Could not load daily summary</p>
        <p className="text-xs text-[var(--muted)]">{error ?? "Unknown error"}</p>
        <p className="text-xs text-[var(--muted)] mt-2">
          Check that the API is running and BigQuery credentials are configured.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto w-full py-2">
      <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
        Here&apos;s your daily business summary:
      </h2>
      <div className="grid gap-4 md:grid-cols-2">
        <SalesPerformanceCard data={data.sales_performance} />
        <GrossProfitCard data={data.gross_profit} />
        <DailyOnTrackCard data={data.monthly_on_track} />
        <YesterdaySalesCard data={data.yesterday} />
      </div>
      <p className="mt-6 text-center text-xs text-[var(--text-tertiary)]">{data.disclaimer}</p>
    </div>
  );
}
