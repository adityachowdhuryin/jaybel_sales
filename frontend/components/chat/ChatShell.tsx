"use client";

import { useCallback, useEffect, useState } from "react";
import {
  createSession,
  deleteSession,
  getMe,
  listSessions,
  listTurns,
  updateProfile,
} from "@/lib/api";
import { useChatStream } from "@/hooks/useChatStream";
import { ExploreDrawer } from "@/components/explore/ExploreDrawer";
import { ChatWindow } from "./ChatWindow";
import { SessionSidebar } from "./SessionSidebar";
import type { AppUser, ChatMessage, ChatSendMeta, ChatSession, ChatTurn } from "@/types";
import type { QuestionCategory, StarterQuestion } from "@/types/questionCatalog";

function turnsToMessages(turns: ChatTurn[]): ChatMessage[] {
  const out: ChatMessage[] = [];
  for (const t of turns) {
    out.push({
      id: `u-${t.id}`,
      role: "user",
      content: t.question,
      createdAt: t.created_at,
    });
    out.push({
      id: `a-${t.id}`,
      role: "agent",
      content: t.answer ?? "",
      question: t.question,
      turnId: t.id,
      starterId: t.starter_id ?? undefined,
      categoryId: t.category_id ?? undefined,
      feedbackRating: t.feedback_rating ?? undefined,
      createdAt: t.created_at,
      sql: t.sql ?? undefined,
      tableDisplay: t.table_id ?? undefined,
      rows: t.results_sample ?? undefined,
      rowCount: t.row_count,
      chartSpec: t.chart_spec ?? undefined,
      queryId: t.query_id,
      costWarningBytes: extractCostWarning(t.events),
    });
  }
  return out;
}

function extractCostWarning(events: ChatTurn["events"]): number | undefined {
  if (!events) return undefined;
  for (const e of events) {
    if (e.type === "cost_warning" && e.bytes_scanned) return e.bytes_scanned as number;
  }
  return undefined;
}

export function ChatShell() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [sessionSearch, setSessionSearch] = useState("");
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [user, setUser] = useState<AppUser | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [draftInput, setDraftInput] = useState("");
  const [sendMeta, setSendMeta] = useState<ChatSendMeta>({});
  const [exploreOpen, setExploreOpen] = useState(false);
  const [activeCategory, setActiveCategory] = useState<QuestionCategory | null>(null);
  const { sendMessage, streaming } = useChatStream();

  const refreshSessions = useCallback(async (search?: string) => {
    const list = await listSessions(search);
    setSessions(list);
    return list;
  }, []);

  const loadSession = useCallback(async (id: string) => {
    setActiveId(id);
    const turns = await listTurns(id);
    setMessages(turnsToMessages(turns));
    setExploreOpen(false);
    setActiveCategory(null);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const me = await getMe();
        setUser(me);
        let list = await refreshSessions();
        if (list.length === 0) {
          const s = await createSession();
          list = [s];
          setSessions(list);
        }
        await loadSession(list[0].id);
      } catch (e) {
        setLoadError(e instanceof Error ? e.message : "Failed to connect to API");
      }
    })();
  }, [refreshSessions, loadSession]);

  useEffect(() => {
    const t = setTimeout(() => {
      refreshSessions(sessionSearch || undefined).catch(() => {});
    }, 300);
    return () => clearTimeout(t);
  }, [sessionSearch, refreshSessions]);

  const handleNew = async () => {
    const s = await createSession();
    setSessions((prev) => [s, ...prev]);
    setActiveId(s.id);
    setMessages([]);
    setExploreOpen(true);
    setActiveCategory(null);
    setDraftInput("");
    setSendMeta({});
  };

  const handleDelete = async (id: string) => {
    await deleteSession(id);
    const list = await refreshSessions(sessionSearch || undefined);
    if (list.length === 0) {
      const s = await createSession();
      setSessions([s]);
      setActiveId(s.id);
      setMessages([]);
      setExploreOpen(true);
    } else if (activeId === id) {
      await loadSession(list[0].id);
    } else {
      setSessions(list);
    }
  };

  const handlePickStarter = (starter: StarterQuestion) => {
    setDraftInput(starter.text);
    setSendMeta({ starter_id: starter.id, category_id: starter.category_id });
  };

  const handleFollowUpPick = (text: string) => {
    setDraftInput(text);
    setSendMeta({});
  };

  const handleSend = async (question: string) => {
    if (!activeId) return;
    const meta = { ...sendMeta };
    setSendMeta({});
    await sendMessage(activeId, question, setMessages, meta);
    await refreshSessions(sessionSearch || undefined);
  };

  const handleSaveProfile = async (data: {
    sales_rep_code: string | null;
    display_name?: string;
  }) => {
    const updated = await updateProfile(data);
    setUser(updated);
  };

  if (loadError) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8">
        <div className="max-w-md text-center">
          <p className="text-red-400 mb-2">Cannot reach API</p>
          <p className="text-sm text-[var(--muted)]">{loadError}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex">
      <SessionSidebar
        sessions={sessions}
        activeId={activeId}
        user={user}
        searchQuery={sessionSearch}
        onSearchChange={setSessionSearch}
        onSelect={loadSession}
        onNew={handleNew}
        onDelete={handleDelete}
        onSaveProfile={handleSaveProfile}
      />
      <main className="flex-1 flex flex-col min-w-0 relative">
        <ChatWindow
          messages={messages}
          sessionId={activeId}
          user={user}
          onSend={handleSend}
          disabled={streaming || !activeId}
          draftInput={draftInput}
          onDraftChange={setDraftInput}
          exploreOpen={exploreOpen}
          onOpenExplore={() => setExploreOpen(true)}
          activeCategory={activeCategory}
          onPickStarter={handlePickStarter}
          onFollowUpPick={handleFollowUpPick}
          hideFollowUps={streaming}
        />
        <ExploreDrawer
          open={exploreOpen}
          onClose={() => setExploreOpen(false)}
          hasRepCode={Boolean(user?.sales_rep_code)}
          activeCategory={activeCategory}
          onCategoryChange={setActiveCategory}
          onPickStarter={handlePickStarter}
          onSearchPick={handleFollowUpPick}
        />
      </main>
    </div>
  );
}
