"use client";

import { useState } from "react";
import { Check, Copy, RotateCcw } from "lucide-react";

function formatTime(iso?: string) {
  if (!iso) return null;
  try {
    return new Date(iso).toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return null;
  }
}

export function UserMessage({
  content,
  createdAt,
  showRetry,
  onRetry,
  retryDisabled,
}: {
  content: string;
  createdAt?: string;
  showRetry?: boolean;
  onRetry?: () => void;
  retryDisabled?: boolean;
}) {
  const time = formatTime(createdAt);
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="mb-4 max-w-4xl mx-auto w-full">
      <div className="flex justify-end">
        <div className="group relative max-w-full">
          <div className="rounded-2xl rounded-tr-none bg-[var(--user-bubble-bg)] px-4 py-3 pr-10 text-sm text-[var(--user-bubble-text)]">
            {content}
          </div>
          <button
            type="button"
            onClick={handleCopy}
            className="absolute top-2.5 right-2.5 inline-flex items-center justify-center rounded-md p-1 text-[var(--user-bubble-text)] opacity-0 group-hover:opacity-70 hover:opacity-100 transition focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-[var(--ring-focus)]"
            aria-label={copied ? "Copied" : "Copy question"}
          >
            {copied ? (
              <Check className="w-3.5 h-3.5" />
            ) : (
              <Copy className="w-3.5 h-3.5" />
            )}
          </button>
        </div>
      </div>
      <div className="flex justify-end items-center gap-2 mt-1 pr-1">
        {time && <p className="text-[10px] text-[var(--muted)]">{time}</p>}
        {showRetry && onRetry && (
          <button
            type="button"
            onClick={onRetry}
            disabled={retryDisabled}
            className="inline-flex items-center gap-1 text-xs text-[var(--text-secondary)] hover:text-[var(--intent-primary)] disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            <RotateCcw className="w-3 h-3" />
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
