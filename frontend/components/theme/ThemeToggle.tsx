"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/hooks/useTheme";

export function ThemeToggle({ showLabel = false }: { showLabel?: boolean }) {
  const { theme, toggleTheme } = useTheme();
  const isLight = theme === "light";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={`inline-flex items-center gap-2 rounded-md text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition ${
        showLabel ? "w-full px-2 py-1.5 text-sm hover:bg-[var(--surface-2)]" : "p-1.5 hover:bg-[var(--surface-2)]"
      }`}
      aria-label="Toggle theme"
    >
      {isLight ? <Moon className="w-4 h-4 shrink-0" /> : <Sun className="w-4 h-4 shrink-0" />}
      {showLabel && (isLight ? "Switch to dark mode" : "Switch to light mode")}
    </button>
  );
}
