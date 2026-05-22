"use client";

import { useState } from "react";

export function SQLAccordion({ sql }: { sql?: string }) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  if (!sql) return null;

  async function copy() {
    await navigator.clipboard.writeText(sql!);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="mt-3 rounded-lg border border-[var(--border)] overflow-hidden">
      <div className="flex items-center bg-[var(--panel)]">
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className="flex-1 px-3 py-2 text-left text-sm font-medium hover:bg-[#243044]"
        >
          {open ? "▼" : "▶"} View SQL
        </button>
        <button
          type="button"
          onClick={copy}
          className="px-3 py-2 text-xs text-[var(--muted)] hover:text-[var(--text)] border-l border-[var(--border)]"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      {open && (
        <pre className="p-3 text-xs overflow-x-auto bg-black/30 text-emerald-200/90">
          {sql}
        </pre>
      )}
    </div>
  );
}
