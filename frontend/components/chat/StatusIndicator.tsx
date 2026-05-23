"use client";

import { Loader2 } from "lucide-react";

const STEPS = [
  { match: /analyzing/i, label: "Understanding question" },
  { match: /generating/i, label: "Building SQL" },
  { match: /running/i, label: "Querying BigQuery" },
  { match: /summarizing/i, label: "Formatting answer" },
];

export function StatusIndicator({ message }: { message?: string }) {
  if (!message) return null;
  const step = STEPS.find((s) => s.match.test(message));
  return (
    <div className="flex items-center gap-2 mb-3 py-2 px-3 rounded-lg bg-brand-500/10 border border-brand-500/20">
      <Loader2 className="w-4 h-4 text-brand-400 animate-spin shrink-0" />
      <p className="text-sm text-brand-200">{step?.label ?? message}</p>
    </div>
  );
}
