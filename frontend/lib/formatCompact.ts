/** Compact currency display for dashboard cards (A$ with M/K suffixes). */

import { formatCurrency } from "./formatters";

export function formatCompactCurrency(value: number): string {
  const n = Number(value);
  if (Number.isNaN(n)) return "—";
  const abs = Math.abs(n);
  const sign = n < 0 ? "-" : "";
  if (abs >= 1_000_000) {
    return `${sign}A$${(abs / 1_000_000).toFixed(2)}M`;
  }
  if (abs >= 10_000) {
    return `${sign}A$${Math.round(abs / 1_000)}K`;
  }
  return formatCurrency(n);
}

export function formatCompactPercent(value: number, decimals = 1): string {
  const n = Number(value);
  if (Number.isNaN(n)) return "—";
  const sign = n > 0 ? "+" : "";
  return `${sign}${n.toFixed(decimals)}%`;
}

export function formatFyLabel(fy: string): string {
  const parts = fy.split("-");
  if (parts.length === 2) {
    return `FY ${parts[0].slice(-2)}–${parts[1].slice(-2)}`;
  }
  return fy;
}
