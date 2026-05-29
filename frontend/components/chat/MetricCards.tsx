"use client";

import { useMemo } from "react";
import { ArrowDown, ArrowRight, ArrowUp } from "lucide-react";
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
  currencyContext,
}: {
  rows?: Record<string, unknown>[];
  columns?: string[];
  currencyContext?: string;
}) {
  const metrics = useMemo(() => {
    if (!rows?.length || rows.length > 3) return [];
    const row = rows[0];
    const cols =
      columns?.length ? columns : Object.keys(row);
    const out: {
      label: string;
      value: string;
      format: string;
      numericValue: number | null;
      deltaHint: boolean;
      deltaPercent: string | null;
    }[] = [];

    function pickNumberByPattern(pattern: RegExp): number | null {
      for (const col of cols) {
        if (!pattern.test(col)) continue;
        const v = Number(row[col]);
        if (!Number.isNaN(v)) return v;
      }
      return null;
    }

    const currentVal = pickNumberByPattern(/current|this[_\s-]*fy|latest/i);
    const lastVal = pickNumberByPattern(/last|previous|prior/i);
    for (const col of cols) {
      const v = row[col];
      if (v == null || v === "") continue;
      const num = Number(v);
      if (Number.isNaN(num) && typeof v !== "string") continue;
      if (typeof v === "string" && v.length > 80) continue;
      const fmt = inferValueFormat(col, currencyContext);
      if (fmt === "number" && typeof v === "string" && !/^-?\d/.test(v.trim())) {
        continue;
      }
      out.push({
        label: humanizeColumn(col),
        value: formatByColumn(col, v, currencyContext),
        format: fmt,
        numericValue: Number.isNaN(num) ? null : num,
        deltaHint: /(change|difference|delta|variance|vs|increase|decrease)/i.test(col),
        deltaPercent: null,
      });
    }
    const result = out.slice(0, 6);

    // For comparison cards, prefer explicit percent-style columns first.
    const explicitPct = pickNumberByPattern(/percent|percentage|pct|growth[_\s-]*rate|change[_\s-]*rate/i);
    for (const item of result) {
      if (!item.deltaHint) continue;
      if (explicitPct !== null) {
        item.deltaPercent = `${explicitPct.toFixed(1)}%`;
        continue;
      }
      if (currentVal !== null && lastVal !== null && Math.abs(lastVal) > 1e-9) {
        const pct = ((currentVal - lastVal) / Math.abs(lastVal)) * 100;
        item.deltaPercent = `${pct.toFixed(1)}%`;
      }
    }
    return result;
  }, [rows, columns, currencyContext]);

  if (!metrics.length) return null;

  return (
    <div className="mt-3 mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {metrics.map((m, idx) => (
        <div
          key={m.label}
          className={`rounded-xl border bg-[var(--bg-elevated)] px-4 py-3 shadow-sm ${
            idx % 3 === 0
              ? "border-sky-200"
              : idx % 3 === 1
                ? "border-emerald-200"
                : "border-violet-200"
          }`}
        >
          <p className="text-xs font-semibold uppercase tracking-wide text-[var(--text-tertiary)]">
            {m.label}
          </p>
          <div className="mt-1 flex items-start justify-between gap-2">
            <div>
              <p
                className={`font-semibold tabular-nums ${
                  m.format === "currency" ? "text-2xl text-sky-700 tracking-tight" : "text-xl text-[var(--text)] tracking-tight"
                }`}
              >
                {m.value}
              </p>
              {m.deltaHint && m.deltaPercent && (
                <p className="text-xs text-[var(--muted)] tabular-nums mt-0.5">
                  {m.deltaPercent} change
                </p>
              )}
            </div>
            {m.deltaHint && m.numericValue !== null && (
              m.numericValue > 0 ? (
                <ArrowUp className="w-4 h-4 mt-1 text-[var(--intent-success)] shrink-0" />
              ) : m.numericValue < 0 ? (
                <ArrowDown className="w-4 h-4 mt-1 text-[var(--intent-danger)] shrink-0" />
              ) : (
                <ArrowRight className="w-4 h-4 mt-1 text-[var(--intent-insight)] shrink-0" />
              )
            )}
          </div>
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
