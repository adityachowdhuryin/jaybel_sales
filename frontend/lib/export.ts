export function downloadCsv(
  rows: Record<string, unknown>[],
  columns: string[],
  filename: string
) {
  const escape = (v: unknown) => {
    const s = String(v ?? "");
    if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
    return s;
  };
  const header = columns.map(escape).join(",");
  const body = rows.map((r) => columns.map((c) => escape(r[c])).join(",")).join("\n");
  const blob = new Blob([`${header}\n${body}`], { type: "text/csv;charset=utf-8" });
  triggerDownload(blob, filename);
}

export async function downloadChartPng(element: HTMLElement, filename: string) {
  const { default: html2canvas } = await import("html2canvas");
  const theme =
    typeof document !== "undefined"
      ? document.documentElement.getAttribute("data-theme")
      : "light";
  const canvas = await html2canvas(element, {
    backgroundColor: theme === "dark" ? "#111827" : "#ffffff",
    scale: 2,
  });
  canvas.toBlob((blob) => {
    if (blob) triggerDownload(blob, filename);
  });
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function printReportWindow(opts: {
  question: string;
  answer: string;
  sql?: string;
  rows?: Record<string, unknown>[];
  columns?: string[];
}) {
  const cols = opts.columns ?? (opts.rows?.[0] ? Object.keys(opts.rows[0]) : []);
  const tableRows = (opts.rows ?? [])
    .slice(0, 100)
    .map(
      (r) =>
        `<tr>${cols.map((c) => `<td>${escapeHtml(String(r[c] ?? ""))}</td>`).join("")}</tr>`
    )
    .join("");
  const html = `<!DOCTYPE html><html><head><title>Report</title>
<style>body{font-family:system-ui;padding:24px}pre{background:#f4f4f4;padding:12px;overflow:auto}
table{border-collapse:collapse;width:100%}td,th{border:1px solid #cbd5e1;padding:6px;text-align:left}th{background:#f8fafc}</style>
</head><body>
<h1>Jaybel Sales Analytics</h1>
<p><strong>Question:</strong> ${escapeHtml(opts.question)}</p>
<p><strong>Answer:</strong> ${escapeHtml(opts.answer)}</p>
${opts.sql ? `<h3>SQL</h3><pre>${escapeHtml(opts.sql)}</pre>` : ""}
${tableRows ? `<h3>Data</h3><table><thead><tr>${cols.map((c) => `<th>${escapeHtml(c)}</th>`).join("")}</tr></thead><tbody>${tableRows}</tbody></table>` : ""}
</body></html>`;
  const w = window.open("", "_blank");
  if (!w) return;
  w.document.write(html);
  w.document.close();
  w.focus();
  w.print();
}

function escapeHtml(s: string) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
