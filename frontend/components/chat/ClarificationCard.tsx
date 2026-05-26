"use client";

export interface ClarificationOption {
  id: string;
  label: string;
  send_text: string;
}

export function ClarificationCard({
  message,
  options,
  onPick,
}: {
  message: string;
  options: ClarificationOption[];
  onPick: (sendText: string) => void;
}) {
  if (!message && !options.length) return null;

  return (
    <div className="mb-4 rounded-xl border border-brand-500/30 bg-brand-500/5 px-4 py-3">
      {message && (
        <p className="text-sm text-[var(--text)] leading-relaxed mb-3">{message}</p>
      )}
      {options.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {options.map((opt) => (
            <button
              key={opt.id}
              type="button"
              onClick={() => onPick(opt.send_text)}
              className="rounded-full border border-brand-500/40 bg-[var(--bg)] px-3 py-1.5 text-xs hover:border-brand-400 hover:bg-brand-500/10 text-left"
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
