import type { ChatSession } from "@/types";

export type SessionGroupLabel = "Today" | "Yesterday" | "Last 7 days" | "Older";

const GROUP_ORDER: SessionGroupLabel[] = [
  "Today",
  "Yesterday",
  "Last 7 days",
  "Older",
];

function startOfDay(d: Date) {
  const x = new Date(d);
  x.setHours(0, 0, 0, 0);
  return x;
}

export function groupSessions(
  sessions: ChatSession[]
): { label: SessionGroupLabel; sessions: ChatSession[] }[] {
  const now = new Date();
  const today = startOfDay(now).getTime();
  const yesterday = today - 86400000;
  const weekAgo = today - 7 * 86400000;

  const buckets: Record<SessionGroupLabel, ChatSession[]> = {
    Today: [],
    Yesterday: [],
    "Last 7 days": [],
    Older: [],
  };

  for (const s of sessions) {
    const t = new Date(s.updated_at).getTime();
    if (t >= today) buckets.Today.push(s);
    else if (t >= yesterday) buckets.Yesterday.push(s);
    else if (t >= weekAgo) buckets["Last 7 days"].push(s);
    else buckets.Older.push(s);
  }

  return GROUP_ORDER.filter((label) => buckets[label].length > 0).map((label) => ({
    label,
    sessions: buckets[label],
  }));
}
