"use client";

import { useMemo, type RefObject } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChartSpec } from "@/types";
import { formatChartValue } from "@/lib/formatters";
import { getChartPalette, getThemeMode } from "@/lib/themeTokens";

function buildChartData(
  spec: ChartSpec,
  rows: Record<string, unknown>[]
): Record<string, unknown>[] {
  const type = (spec.chart_type || "bar").toLowerCase();

  if (type === "paired_bar" && spec.series?.length && rows[0]) {
    const row = rows[0];
    return spec.series.map((s) => ({
      name: s.label,
      value: Number(row[s.key]) || 0,
    }));
  }

  if (type === "grouped_bar" && spec.series?.length && spec.x) {
    const series = spec.series;
    return rows.map((r) => {
      const point: Record<string, unknown> = {
        name: String(r[spec.x!] ?? ""),
      };
      for (const s of series) {
        point[s.key] = Number(r[s.key]) || 0;
      }
      return point;
    });
  }

  if (!spec.x) return [];
  const yKey = spec.y || Object.keys(rows[0]).find((k) => k !== spec.x) || "";
  return rows.map((r) => ({
    name: String(r[spec.x!] ?? ""),
    value: Number(r[yKey]) || 0,
  }));
}

export function ChartPanel({
  spec,
  rows,
  chartRef,
}: {
  spec: ChartSpec;
  rows?: Record<string, unknown>[];
  chartRef?: RefObject<HTMLDivElement | null>;
}) {
  const data = useMemo(() => {
    if (!rows?.length) return [];
    return buildChartData(spec, rows);
  }, [rows, spec]);

  if (!data.length) return null;

  const type = (spec.chart_type || "bar").toLowerCase();
  const horizontal =
    spec.orientation === "horizontal" ||
    type === "horizontal_bar" ||
    (type === "bar" && data.length > 0 && String(data[0].name).length > 12);
  const title = spec.title || "Chart";
  const fmt = spec.format;
  const series = spec.series ?? [];
  const colors = getChartPalette(getThemeMode());

  const tooltipFmt = (v: number, format?: string) =>
    formatChartValue(format || fmt, v);

  return (
    <div
      ref={chartRef as RefObject<HTMLDivElement>}
      className="mt-3 rounded-xl border border-[var(--border)] bg-[var(--bg-elevated)] p-4 shadow-sm"
    >
      <p className="text-xs font-semibold text-[var(--text)] mb-3">{title}</p>
      <div className="h-64 w-full min-h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          {type === "line" ? (
            <LineChart data={data} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.45} />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: "var(--muted)" }} stroke="var(--border)" />
              <YAxis
                tick={{ fontSize: 11, fill: "var(--muted)" }}
                stroke="var(--border)"
                tickFormatter={(v) => formatChartValue(fmt, Number(v))}
              />
              <Tooltip
                formatter={(v: number) => tooltipFmt(v)}
                contentStyle={{
                  background: "var(--surface-0)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  boxShadow: "0 8px 24px rgba(var(--shadow-color), 0.15)",
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="value"
                stroke={colors[0]}
                strokeWidth={2}
                dot={{ r: 3, fill: colors[0] }}
              />
            </LineChart>
          ) : type === "pie" ? (
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={90}
                label={({ name, percent }) =>
                  `${String(name).slice(0, 12)} ${((percent ?? 0) * 100).toFixed(0)}%`
                }
              >
                {data.map((_, i) => (
                  <Cell key={i} fill={colors[i % colors.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(v: number) => tooltipFmt(Number(v))} />
              <Legend />
            </PieChart>
          ) : type === "grouped_bar" && series.length ? (
            <BarChart data={data} margin={{ top: 8, right: 12, left: 4, bottom: 48 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.45} />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 10, fill: "var(--muted)" }}
                angle={data.length > 5 ? -30 : 0}
                textAnchor={data.length > 5 ? "end" : "middle"}
                height={data.length > 5 ? 60 : 30}
              />
              <YAxis tickFormatter={(v) => formatChartValue(fmt, Number(v))} tick={{ fontSize: 11, fill: "var(--muted)" }} />
              <Tooltip />
              <Legend />
              {series.map((s, i) => (
                <Bar
                  key={s.key}
                  dataKey={s.key}
                  name={s.label}
                  fill={colors[i % colors.length]}
                  radius={[4, 4, 0, 0]}
                />
              ))}
            </BarChart>
          ) : type === "paired_bar" ? (
            <BarChart data={data} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.45} />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: "var(--muted)" }} />
              <YAxis tickFormatter={(v) => formatChartValue(fmt, Number(v))} tick={{ fontSize: 11, fill: "var(--muted)" }} />
              <Tooltip formatter={(v: number) => tooltipFmt(v)} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {data.map((_, i) => (
                  <Cell key={i} fill={colors[i % colors.length]} />
                ))}
              </Bar>
            </BarChart>
          ) : horizontal ? (
            <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.45} />
              <XAxis
                type="number"
                tickFormatter={(v) => formatChartValue(fmt, Number(v))}
                tick={{ fontSize: 11, fill: "var(--muted)" }}
              />
              <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 10, fill: "var(--muted)" }} />
              <Tooltip formatter={(v: number) => tooltipFmt(v)} />
              <Bar dataKey="value" fill={colors[0]} radius={[0, 4, 4, 0]} />
            </BarChart>
          ) : (
            <BarChart data={data} margin={{ top: 8, right: 12, left: 4, bottom: 48 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.45} />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 10, fill: "var(--muted)" }}
                angle={data.length > 6 ? -35 : 0}
                textAnchor={data.length > 6 ? "end" : "middle"}
                height={data.length > 6 ? 70 : 30}
              />
              <YAxis tickFormatter={(v) => formatChartValue(fmt, Number(v))} tick={{ fontSize: 11, fill: "var(--muted)" }} />
              <Tooltip formatter={(v: number) => tooltipFmt(v)} />
              <Bar dataKey="value" fill={colors[0]} radius={[4, 4, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
