"use client";

import { useState } from "react";
import { ChevronDown, Copy } from "lucide-react";

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
    <div className="mt-3 rounded-xl border border-[var(--border)] overflow-hidden bg-[var(--surface-0)]">
      <div className="flex items-center">
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className="flex-1 flex items-center gap-2 px-3 py-2.5 text-left text-xs font-medium text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] transition"
        >
          <ChevronDown
            className={`w-4 h-4 transition-transform ${open ? "rotate-180" : ""}`}
          />
          View SQL
        </button>
        <button
          type="button"
          onClick={copy}
          className="flex items-center gap-1 px-3 py-2.5 text-xs text-[var(--muted)] hover:text-[var(--intent-insight)] border-l border-[var(--border)]"
        >
          <Copy className="w-3.5 h-3.5" />
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      {open && (
        <pre className="p-4 text-[11px] leading-relaxed overflow-x-auto font-mono bg-[var(--code-bg)] text-[var(--code-text)] border-t border-[var(--border)]">
          {sql}
        </pre>
      )}
    </div>
  );
}
