import type { DataAvailability } from "@/types/questionCatalog";

const LABELS: Record<string, { label: string; className: string }> = {
  full: { label: "In BigQuery", className: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30" },
  full_with_config_target: {
    label: "Target from config",
    className: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  },
  partial_run_rate: {
    label: "Run-rate estimate",
    className: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  },
  partial_pattern: {
    label: "Pattern match",
    className: "bg-violet-500/15 text-violet-300 border-violet-500/30",
  },
  requires_rep_context: {
    label: "Set rep code",
    className: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  },
  not_in_bq_forecast: {
    label: "BI forecast only",
    className: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  },
  partial: { label: "Partial data", className: "bg-amber-500/15 text-amber-300 border-amber-500/30" },
  requires_target_table: {
    label: "Target from config",
    className: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  },
  target_not_in_bq: {
    label: "Target not in BQ",
    className: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  },
};

export function DataAvailabilityBadge({ value }: { value: DataAvailability }) {
  const meta = LABELS[value] ?? {
    label: value.replace(/_/g, " "),
    className: "bg-slate-500/15 text-slate-300 border-slate-500/30",
  };
  return (
    <span
      className={`inline-flex shrink-0 items-center rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide ${meta.className}`}
    >
      {meta.label}
    </span>
  );
}
