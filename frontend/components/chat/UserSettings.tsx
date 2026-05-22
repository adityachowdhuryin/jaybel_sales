"use client";

import { FormEvent, useState } from "react";
import type { AppUser } from "@/types";

export function UserSettings({
  user,
  onSave,
}: {
  user: AppUser;
  onSave: (data: { sales_rep_code: string | null; display_name?: string }) => Promise<void>;
}) {
  const [repCode, setRepCode] = useState(user.sales_rep_code ?? "");
  const [name, setName] = useState(user.display_name);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMsg(null);
    try {
      await onSave({
        sales_rep_code: repCode.trim() || null,
        display_name: name.trim() || user.display_name,
      });
      setMsg("Saved");
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="p-4 border-b border-[var(--border)] space-y-2">
      <p className="text-xs font-medium text-[var(--muted)]">Local user</p>
      <p className="text-xs text-[var(--text)] truncate">{user.email ?? user.id}</p>
      <label className="block text-xs text-[var(--muted)]">
        Display name
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="mt-1 w-full rounded-lg border border-[var(--border)] bg-[var(--bg)] px-2 py-1.5 text-sm"
        />
      </label>
      <label className="block text-xs text-[var(--muted)]">
        Sales rep code (for &quot;my sales&quot; questions)
        <input
          value={repCode}
          onChange={(e) => setRepCode(e.target.value)}
          placeholder="e.g. REP01"
          className="mt-1 w-full rounded-lg border border-[var(--border)] bg-[var(--bg)] px-2 py-1.5 text-sm"
        />
      </label>
      <button
        type="submit"
        disabled={saving}
        className="w-full py-1.5 text-xs rounded-lg bg-brand-600/80 hover:bg-brand-600 disabled:opacity-50"
      >
        {saving ? "Saving…" : "Save profile"}
      </button>
      {msg && <p className="text-xs text-[var(--muted)]">{msg}</p>}
    </form>
  );
}
