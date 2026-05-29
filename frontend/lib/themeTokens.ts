export type ThemeMode = "light" | "dark";

export function getThemeMode(): ThemeMode {
  if (typeof document === "undefined") return "light";
  return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
}

export function getChartPalette(theme: ThemeMode): string[] {
  const names = [
    "--chart-1",
    "--chart-2",
    "--chart-3",
    "--chart-4",
    "--chart-5",
    "--chart-6",
    "--chart-7",
    "--chart-8",
  ];
  if (typeof getComputedStyle === "undefined") {
    return theme === "dark"
      ? ["#38bdf8", "#22d3ee", "#4ade80", "#fbbf24", "#fb7185", "#a78bfa"]
      : ["#0284c7", "#0891b2", "#16a34a", "#d97706", "#dc2626", "#7c3aed"];
  }
  const root = getComputedStyle(document.documentElement);
  return names.map((name) => root.getPropertyValue(name).trim()).filter(Boolean);
}

