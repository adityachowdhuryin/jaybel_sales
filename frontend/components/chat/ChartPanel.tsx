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

const COLORS = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#a855f7", "#06b6d4"];

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
    if (!rows?.length || !spec.x) return [];
    const yKey = spec.y || Object.keys(rows[0]).find((k) => k !== spec.x) || "";
    return rows.map((r) => ({
      name: String(r[spec.x!] ?? ""),
      value: Number(r[yKey]) || 0,
      [spec.x!]: r[spec.x!],
      [yKey]: r[yKey],
    }));
  }, [rows, spec]);

  if (!data.length) return null;

  const type = (spec.chart_type || "bar").toLowerCase();
  const title = spec.title || "Chart";

  return (
    <div
      ref={chartRef as RefObject<HTMLDivElement>}
      className="mt-3 rounded-lg border border-[var(--border)] bg-[var(--bg)] p-3"
    >
      <p className="text-xs font-medium text-[var(--muted)] mb-2">{title}</p>
      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {type === "line" ? (
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d3a4f" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="#94a3b8" />
              <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
              <Tooltip
                contentStyle={{ background: "#1a2332", border: "1px solid #2d3a4f" }}
              />
              <Legend />
              <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          ) : type === "pie" ? (
            <PieChart>
              <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80}>
                {data.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "#1a2332", border: "1px solid #2d3a4f" }}
              />
              <Legend />
            </PieChart>
          ) : (
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d3a4f" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="#94a3b8" />
              <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
              <Tooltip
                contentStyle={{ background: "#1a2332", border: "1px solid #2d3a4f" }}
              />
              <Legend />
              <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
