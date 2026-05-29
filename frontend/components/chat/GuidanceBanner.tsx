"use client";

const STYLES: Record<string, string> = {
  rep_context_required: "border-[var(--status-warning-border)] bg-[var(--status-warning-bg)] text-[var(--status-warning-text)]",
  empty_result: "border-[var(--status-info-border)] bg-[var(--status-info-bg)] text-[var(--status-info-text)]",
  off_topic: "border-[var(--status-danger-border)] bg-[var(--status-danger-bg)] text-[var(--status-danger-text)]",
  out_of_dataset: "border-[var(--status-info-border)] bg-[var(--status-info-bg)] text-[var(--status-info-text)]",
  vague: "border-[var(--status-info-border)] bg-[var(--status-info-bg)] text-[var(--status-info-text)]",
  sql_validation_failed: "border-[var(--status-warning-border)] bg-[var(--status-warning-bg)] text-[var(--status-warning-text)]",
};

export function GuidanceBanner({
  code,
  message,
  suggestions,
}: {
  code: string;
  message: string;
  suggestions?: string[];
}) {
  if (!message) return null;
  const style =
    STYLES[code] || "border-[var(--border)] bg-[var(--surface-0)] text-[var(--text-primary)]";

  return (
    <div className={`mb-4 rounded-xl border px-4 py-3 shadow-sm ${style}`}>
      <p className="text-sm font-medium leading-relaxed">{message}</p>
      {suggestions && suggestions.length > 0 && (
        <ul className="mt-2 text-xs opacity-90 list-disc pl-4 space-y-1">
          {suggestions.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
