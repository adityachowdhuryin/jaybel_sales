"use client";

import { useMemo, useState } from "react";

function formatCell(value: unknown): string {
  if (value == null) return "";
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
    <div className="mt-3 rounded-lg border border-[var(--border)] overflow-hidden">
      <div className="px-3 py-2 text-xs text-[var(--muted)] bg-[var(--panel)] flex justify-between items-center">
        <span>
          {tableDisplay && (
            <span className="font-medium text-[var(--text)]">{tableDisplay}</span>
          )}
          {tableDisplay && " · "}
          {total} row{total !== 1 ? "s" : ""}
        </span>
        {pageCount > 1 && (
          <span>
            Page {page + 1} / {pageCount}
          </span>
        )}
      </div>
      <div className="overflow-x-auto max-h-80">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--border)] bg-black/20">
              {cols.map((c) => (
                <th
                  key={c}
                  className={`px-3 py-2 font-medium text-[var(--muted)] cursor-pointer hover:text-[var(--text)] ${
                    isNumericColumn(rows, c) ? "text-right" : "text-left"
                  }`}
                  onClick={() => toggleSort(c)}
                >
                  {c}
                  {sortCol === c ? (sortDir === "asc" ? " ↑" : " ↓") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, i) => (
              <tr key={i} className="border-b border-[var(--border)]/50">
                {cols.map((c) => (
                  <td
                    key={c}
                    className={`px-3 py-2 ${
                      isNumericColumn(rows, c) ? "text-right tabular-nums" : ""
                    }`}
                  >
                    {formatCell(row[c])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pageCount > 1 && (
        <div className="flex justify-end gap-2 px-3 py-2 border-t border-[var(--border)] text-xs">
          <button
            type="button"
            disabled={page === 0}
            className="px-2 py-1 rounded border border-[var(--border)] disabled:opacity-40"
            onClick={() => setPage((p) => p - 1)}
          >
            Prev
          </button>
          <button
            type="button"
            disabled={page >= pageCount - 1}
            className="px-2 py-1 rounded border border-[var(--border)] disabled:opacity-40"
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
