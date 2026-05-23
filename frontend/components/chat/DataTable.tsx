"use client";

import { useMemo, useState } from "react";
import { formatByColumn, inferValueFormat } from "@/lib/formatters";

function formatCell(value: unknown, col: string): string {
  if (value == null) return "";
  const fmt = inferValueFormat(col);
  if (fmt !== "number") return formatByColumn(col, value);
  if (typeof value === "number") {
    return value.toLocaleString(undefined, { maximumFractionDigits: 4 });
  }
  const n = Number(value);
  if (!Number.isNaN(n) && String(value).trim() !== "" && /^-?\d/.test(String(value))) {
    return n.toLocaleString(undefined, { maximumFractionDigits: 4 });
  }
  return String(value);
}

function isNumericColumn(rows: Record<string, unknown>[], col: string) {
  const sample = rows.slice(0, 20);
  return sample.every((r) => {
    const v = r[col];
    return v == null || typeof v === "number" || !Number.isNaN(Number(v));
  });
}

export function DataTable({
  rows,
  columns,
  rowCount,
  tableDisplay,
}: {
  rows?: Record<string, unknown>[];
  columns?: string[];
  rowCount?: number;
  tableDisplay?: string;
}) {
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(0);
  const pageSize = 10;

  const cols = useMemo(
    () => (columns?.length ? columns : rows?.[0] ? Object.keys(rows[0]) : []),
    [columns, rows]
  );

  const sorted = useMemo(() => {
    if (!rows?.length) return [];
    const copy = [...rows];
    if (sortCol) {
      copy.sort((a, b) => {
        const av = a[sortCol];
        const bv = b[sortCol];
        const an = Number(av);
        const bn = Number(bv);
        const cmp =
          !Number.isNaN(an) && !Number.isNaN(bn)
            ? an - bn
            : String(av ?? "").localeCompare(String(bv ?? ""));
        return sortDir === "asc" ? cmp : -cmp;
      });
    }
    return copy;
  }, [rows, sortCol, sortDir]);

  if (!rows?.length) return null;

  const total = rowCount ?? rows.length;
  const pageCount = Math.ceil(sorted.length / pageSize);
  const pageRows = sorted.slice(page * pageSize, page * pageSize + pageSize);

  function toggleSort(col: string) {
    if (sortCol === col) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortCol(col);
      setSortDir("asc");
    }
    setPage(0);
  }

  return (
    <div className="mt-3 rounded-xl border border-[var(--border)] overflow-hidden bg-[var(--bg-elevated)] shadow-sm">
      <div className="px-4 py-2.5 text-xs text-[var(--muted)] bg-[var(--panel)] flex justify-between items-center border-b border-[var(--border)]">
        <span>
          {tableDisplay && (
            <span className="font-medium text-brand-300">{tableDisplay}</span>
          )}
          {tableDisplay && " · "}
          <span className="tabular-nums">
            {total} row{total !== 1 ? "s" : ""}
          </span>
        </span>
        {pageCount > 1 && (
          <span className="tabular-nums">
            Page {page + 1} / {pageCount}
          </span>
        )}
      </div>
      <div className="overflow-x-auto max-h-80">
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-[1]">
            <tr className="border-b border-[var(--border)] bg-[var(--panel)]">
              {cols.map((c) => (
                <th
                  key={c}
                  className={`px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-[var(--muted)] cursor-pointer hover:text-brand-300 transition ${
                    isNumericColumn(rows, c) ? "text-right" : "text-left"
                  }`}
                  onClick={() => toggleSort(c)}
                >
                  {c.replace(/_/g, " ")}
                  {sortCol === c ? (sortDir === "asc" ? " ↑" : " ↓") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, i) => (
              <tr
                key={i}
                className={`border-b border-[var(--border)]/40 ${
                  i % 2 === 0 ? "bg-transparent" : "bg-black/15"
                } hover:bg-brand-500/5 transition`}
              >
                {cols.map((c) => (
                  <td
                    key={c}
                    className={`px-3 py-2 text-[13px] ${
                      isNumericColumn(rows, c)
                        ? "text-right tabular-nums text-[var(--text)]"
                        : "text-[var(--text)]/90"
                    }`}
                  >
                    {formatCell(row[c], c)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pageCount > 1 && (
        <div className="flex justify-end gap-2 px-4 py-2.5 border-t border-[var(--border)] text-xs bg-[var(--panel)]">
          <button
            type="button"
            disabled={page === 0}
            className="px-3 py-1 rounded-lg border border-[var(--border)] hover:bg-[var(--bg-elevated)] disabled:opacity-40 transition"
            onClick={() => setPage((p) => p - 1)}
          >
            Prev
          </button>
          <button
            type="button"
            disabled={page >= pageCount - 1}
            className="px-3 py-1 rounded-lg border border-[var(--border)] hover:bg-[var(--bg-elevated)] disabled:opacity-40 transition"
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
