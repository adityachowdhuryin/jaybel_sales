/** Display formatters for metrics, charts, and tables. */

export function formatNumber(value: unknown, maxFraction = 2): string {
  const n = Number(value);
  if (Number.isNaN(n)) return String(value ?? "");
  return n.toLocaleString(undefined, { maximumFractionDigits: maxFraction });
}

export function formatCurrency(value: unknown): string {
  const n = Number(value);
  if (Number.isNaN(n)) return String(value ?? "");
  const formatted = Math.abs(n).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return n < 0 ? `-A$ ${formatted}` : `A$ ${formatted}`;
}

/** Normalize markdown currency literals to A$ for display. */
export function normalizeCurrencyDisplay(content: string): string {
  return content.replace(/(?<![A-Za-z])\$(\d)/g, "A$$$1");
}

export function formatPercent(value: unknown): string {
  const n = Number(value);
  if (Number.isNaN(n)) return String(value ?? "");
  const pct = Math.abs(n) <= 1 && n !== 0 ? n * 100 : n;
  return `${pct.toLocaleString(undefined, { maximumFractionDigits: 1 })}%`;
}

export function inferValueFormat(
  columnName: string,
  context?: string
): "currency" | "percent" | "number" {
  const n = columnName.toLowerCase();
  if (n.includes("percent") || n.includes("pct") || n.includes("gp%") || n.includes("margin")) {
    return "percent";
  }
  if (
    n.includes("sales") ||
    n.includes("revenue") ||
    n.includes("profit") ||
    n.includes("gp") ||
    n.includes("cost") ||
    n.includes("variance") ||
    n.includes("target") ||
    n.includes("actual") ||
    n.includes("amount")
  ) {
    return "currency";
  }
  if (context && isGenericMetricColumn(n) && contextSuggestsCurrency(context)) {
    return "currency";
  }
  return "number";
}

const GENERIC_METRIC_COLUMN =
  /^(value|total|result|metric|measure|sum|avg|average|amount|f\d+_?)$/;

function isGenericMetricColumn(columnName: string): boolean {
  return GENERIC_METRIC_COLUMN.test(columnName);
}

function contextSuggestsCurrency(context: string): boolean {
  const text = context.toLowerCase();
  return (
    /\ba\$|\$\d/.test(context) ||
    /\b(sales|revenue|profit|gross profit|gp\b|cost|variance|target|actual|turnover|income)\b/.test(
      text
    )
  );
}

export function formatByColumn(
  columnName: string,
  value: unknown,
  context?: string
): string {
  const fmt = inferValueFormat(columnName, context);
  if (fmt === "currency") return formatCurrency(value);
  if (fmt === "percent") return formatPercent(value);
  return formatNumber(value);
}

export function formatChartValue(format: string | undefined, value: number): string {
  if (format === "currency") return formatCurrency(value);
  if (format === "percent") return formatPercent(value);
  return formatNumber(value);
}
