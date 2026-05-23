"use client";

import { useMemo } from "react";
import { formatByColumn, inferValueFormat } from "@/lib/formatters";

function humanizeColumn(col: string): string {
  return col
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/^F\d+ $/, "Value");
}

export function MetricCards({
  rows,
  columns,
}: {
  rows?: Record<string, unknown>[];
  columns?: string[];
}) {
  const metrics = useMemo(() => {
    if (!rows?.length || rows.length > 3) return [];
    const row = rows[0];
    const cols =
      columns?.length ? columns : Object.keys(row);
    const out: { label: string; value: string; format: string }[] = [];
    for (const col of cols) {
      const v = row[col];
      if (v == null || v === "") continue;
      const num = Number(v);
      if (Number.isNaN(num) && typeof v !== "string") continue;
      if (typeof v === "string" && v.length > 80) continue;
      const fmt = inferValueFormat(col);
      if (fmt === "number" && typeof v === "string" && !/^-?\d/.test(v.trim())) {
        continue;
      }
      out.push({
        label: humanizeColumn(col),
        value: formatByColumn(col, v),
        format: fmt,
      });
    }
    return out.slice(0, 6);
  }, [rows, columns]);

  if (!metrics.length) return null;

  return (
    <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {metrics.map((m) => (
        <div
          key={m.label}
          className="rounded-xl border border-[var(--border)] bg-[var(--bg-elevated)] px-4 py-3 shadow-sm"
        >
          <p className="text-[11px] font-medium uppercase tracking-wide text-[var(--muted)]">
            {m.label}
          </p>
          <p
            className={`mt-1 font-semibold tabular-nums ${
              m.format === "currency" ? "text-xl text-brand-300" : "text-lg text-[var(--text)]"
            }`}
          >
            {m.value}
          </p>
        </div>
      ))}
    </div>
  );
}

export function shouldShowMetricCards(
  rows?: Record<string, unknown>[],
  hasChart?: boolean,
  chartType?: string
): boolean {
  if (!rows?.length) return false;
  if (rows.length > 2) return false;
  if (hasChart && chartType === "paired_bar") return true;
  if (hasChart) return false;
  return true;
}
