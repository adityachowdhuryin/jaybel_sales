"use client";

import { useState } from "react";
import { ChevronDown, PanelLeftClose, Plus, Search, Settings } from "lucide-react";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import type { ChatSession } from "@/types";

export function SessionSidebar({
  width,
  sessions,
  activeId,
  newChatActive,
  faqActive,
  searchQuery,
  onSearchChange,
  onSelect,
  onNew,
  onOpenFaq,
  onDelete,
  onCollapse,
}: {
  width?: number;
  sessions: ChatSession[];
  activeId: string | null;
  newChatActive?: boolean;
  faqActive: boolean;
  searchQuery?: string;
  onSearchChange?: (q: string) => void;
  onSelect: (id: string) => void;
  onNew: () => void;
  onOpenFaq: () => void;
  onDelete: (id: string) => void;
  onCollapse: () => void;
}) {
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <aside
      className="shrink-0 border-r border-[var(--border)] bg-[var(--surface-0)] flex flex-col min-w-0 overflow-hidden box-border"
      style={{ width: width ?? 320 }}
    >
      <div className="px-4 py-5 border-b border-[var(--border)]">
        <div className="flex items-center justify-between gap-2">
          <h1 className="text-4xl leading-none font-semibold tracking-tight text-[var(--text)]">
            Jaybel Analytics
          </h1>
          <button
            type="button"
            onClick={onCollapse}
            className="inline-flex items-center justify-center rounded-md p-1.5 text-[var(--text-secondary)] hover:bg-[var(--surface-2)] transition"
            aria-label="Collapse sidebar"
          >
            <PanelLeftClose className="w-5 h-5" />
          </button>
        </div>
      </div>
      {onSearchChange && (
        <div className="px-4 pt-4">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]" />
            <input
              type="search"
              value={searchQuery ?? ""}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Search chats"
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-0)] pl-9 pr-3 py-2 text-sm text-[var(--text-secondary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-sky-200"
            />
          </div>
        </div>
      )}
      <div className="px-4 pt-3">
        <button
          type="button"
          onClick={onNew}
          className={`w-full inline-flex items-center gap-2 rounded-md px-3 py-2.5 text-lg font-semibold transition ${
            newChatActive
              ? "bg-[#dbeafe] border border-[#bfdbfe] text-[#4264b3]"
              : "text-[#5f78bd] hover:bg-[var(--surface-2)] border border-transparent"
          }`}
        >
          <Plus className="w-4 h-4 shrink-0" />
          New chat
        </button>
      </div>
      <div className="flex-1 min-w-0 overflow-y-auto overflow-x-hidden pt-4 pl-4 pr-4">
        <div className="mb-3 flex items-center gap-2 text-xl font-semibold text-[var(--text)]">
          Recent Chats
          <ChevronDown className="w-4 h-4 text-[var(--text-secondary)]" />
        </div>
        <ul className="space-y-2">
          {sessions.map((s) => (
            <li key={s.id} className="group relative min-w-0">
              <button
                type="button"
                onClick={() => onSelect(s.id)}
                className={`w-full min-w-0 text-left px-2 py-1.5 pr-7 rounded-md text-base ${
                  activeId === s.id
                    ? "bg-[var(--surface-accent)] text-[var(--text-primary)]"
                    : "text-[var(--text-secondary)] hover:bg-[var(--surface-2)]"
                }`}
                title={s.title}
              >
                <span className="block truncate">{s.title}</span>
              </button>
              <button
                type="button"
                onClick={() => onDelete(s.id)}
                className="absolute right-0 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 px-1.5 text-xs text-[var(--intent-danger)] hover:brightness-90"
                aria-label="Delete session"
              >
                ×
              </button>
            </li>
          ))}
        </ul>
        <button
          type="button"
          onClick={onOpenFaq}
          className={`mt-4 block text-left text-xl font-semibold transition ${
            faqActive
              ? "text-sky-800"
              : "text-[var(--text)] hover:text-sky-700"
          }`}
        >
          FAQ
        </button>
      </div>
      <div className="px-4 py-4 border-t border-[var(--border)]">
        <button
          type="button"
          onClick={() => setSettingsOpen((v) => !v)}
          className="inline-flex items-center gap-2 text-left text-xl font-semibold text-[var(--text)] hover:text-sky-700 transition"
        >
          <Settings className="w-5 h-5" />
          Settings
        </button>
        {settingsOpen && (
          <div className="mt-2 rounded-lg border border-[var(--border)] bg-[var(--surface-1)] px-3 py-2.5">
            <p className="text-xs text-[var(--text-tertiary)] mb-2">Appearance</p>
            <ThemeToggle showLabel />
          </div>
        )}
      </div>
    </aside>
  );
}
