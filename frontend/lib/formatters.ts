/** Display formatters for metrics, charts, and tables. */

export function formatNumber(value: unknown, maxFraction = 2): string {
  const n = Number(value);
  if (Number.isNaN(n)) return String(value ?? "");
  return n.toLocaleString(undefined, { maximumFractionDigits: maxFraction });
}

export function formatCurrency(value: unknown): string {
  const n = Number(value);
  if (Number.isNaN(n)) return String(value ?? "");
  return n.toLocaleString(undefined, {
    style: "currency",
    currency: "AUD",
    maximumFractionDigits: 2,
  });
}

export function formatPercent(value: unknown): string {
  const n = Number(value);
  if (Number.isNaN(n)) return String(value ?? "");
  const pct = Math.abs(n) <= 1 && n !== 0 ? n * 100 : n;
  return `${pct.toLocaleString(undefined, { maximumFractionDigits: 1 })}%`;
}

export function inferValueFormat(columnName: string): "currency" | "percent" | "number" {
  const n = columnName.toLowerCase();
  if (n.includes("percent") || n.includes("pct") || n.includes("gp%") || n.includes("margin")) {
    return "percent";
  }
  if (
    n.includes("sales") ||
    n.includes("revenue") ||
    n.includes("gp") ||
    n.includes("cost") ||
    n.includes("variance") ||
    n.includes("target") ||
    n.includes("actual") ||
    n.includes("amount")
  ) {
    return "currency";
  }
  return "number";
}

export function formatByColumn(columnName: string, value: unknown): string {
  const fmt = inferValueFormat(columnName);
  if (fmt === "currency") return formatCurrency(value);
  if (fmt === "percent") return formatPercent(value);
  return formatNumber(value);
}

export function formatChartValue(format: string | undefined, value: number): string {
  if (format === "currency") return formatCurrency(value);
  if (format === "percent") return formatPercent(value);
  return formatNumber(value);
}
