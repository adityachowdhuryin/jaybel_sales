"use client";

import { groupSessions } from "@/lib/sessionGroups";
import type { AppUser, ChatSession } from "@/types";
import { UserSettings } from "./UserSettings";

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function SessionSidebar({
  sessions,
  activeId,
  user,
  searchQuery,
  onSearchChange,
  onSelect,
  onNew,
  onDelete,
  onSaveProfile,
}: {
  sessions: ChatSession[];
  activeId: string | null;
  user: AppUser | null;
  searchQuery?: string;
  onSearchChange?: (q: string) => void;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  onSaveProfile: (data: {
    sales_rep_code: string | null;
    display_name?: string;
  }) => Promise<void>;
}) {
  const groups = groupSessions(sessions);

  return (
    <aside className="w-72 shrink-0 border-r border-[var(--border)] bg-[var(--panel)] flex flex-col">
      <div className="p-4 border-b border-[var(--border)]">
        <h1 className="text-sm font-semibold text-[var(--text)]">
          Sales and analytics agent
        </h1>
        <p className="text-xs text-[var(--muted)] mt-1">Local · BigQuery via Agent Engine</p>
        <button
          type="button"
          onClick={onNew}
          className="mt-3 w-full py-2 rounded-lg border border-[var(--border)] text-sm hover:bg-[#243044]"
        >
          + New chat
        </button>
      </div>
      {user && <UserSettings user={user} onSave={onSaveProfile} />}
      {onSearchChange && (
        <div className="px-3 pb-2">
          <input
            type="search"
            value={searchQuery ?? ""}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search chats…"
            className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-1.5 text-xs"
          />
        </div>
      )}
      <div className="flex-1 overflow-y-auto p-2">
        {groups.map(({ label, sessions: groupSessions }) => (
          <div key={label} className="mb-3">
            <p className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-[var(--muted)]">
              {label}
            </p>
            <ul className="space-y-1">
              {groupSessions.map((s) => (
                <li key={s.id} className="group flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => onSelect(s.id)}
                    className={`flex-1 text-left px-3 py-2 rounded-lg text-sm ${
                      activeId === s.id
                        ? "bg-brand-600/20 border border-brand-500/40"
                        : "hover:bg-black/20 border border-transparent"
                    }`}
                  >
                    <span className="block truncate font-medium">{s.title}</span>
                    <span className="text-xs text-[var(--muted)]">
                      {formatDate(s.updated_at)}
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => onDelete(s.id)}
                    className="opacity-0 group-hover:opacity-100 px-2 text-xs text-red-400 hover:text-red-300"
                    aria-label="Delete session"
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </aside>
  );
}
