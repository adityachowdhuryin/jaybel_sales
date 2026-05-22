import type { DataAvailability } from "@/types/questionCatalog";

const LABELS: Record<string, { label: string; className: string }> = {
  full: { label: "In BigQuery", className: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30" },
  partial: { label: "Partial data", className: "bg-amber-500/15 text-amber-300 border-amber-500/30" },
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
