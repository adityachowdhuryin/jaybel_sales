"use client";

const STYLES: Record<string, string> = {
  rep_context_required: "border-amber-500/40 bg-amber-500/10 text-amber-100",
  empty_result: "border-sky-500/30 bg-sky-500/10 text-sky-100",
  off_topic: "border-rose-500/30 bg-rose-500/10 text-rose-100",
  out_of_dataset: "border-violet-500/30 bg-violet-500/10 text-violet-100",
  vague: "border-brand-500/30 bg-brand-500/10 text-brand-100",
  sql_validation_failed: "border-orange-500/30 bg-orange-500/10 text-orange-100",
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
  const style = STYLES[code] || "border-[var(--border)] bg-[var(--bg)] text-[var(--text)]";

  return (
    <div className={`mb-4 rounded-xl border px-4 py-3 ${style}`}>
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
