"use client";

import { useCallback, useEffect, useState } from "react";
import {
  createSession,
  deleteSession,
  getMe,
  listSessions,
  listTurns,
} from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { useChatStream } from "@/hooks/useChatStream";
import { FAQFullScreen } from "@/components/explore/FAQFullScreen";
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
  const [centerMode, setCenterMode] = useState<"chat" | "faq">("chat");
  const [activeCategory, setActiveCategory] = useState<QuestionCategory | null>(null);
  const [sidebarWidth, setSidebarWidth] = useState(320);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { getToken, firebaseEnabled } = useAuth();
  const { sendMessage, retryQuestion, streaming } = useChatStream();

  useEffect(() => {
    const saved =
      typeof window !== "undefined" ? window.localStorage.getItem("jaybel.sidebar.width") : null;
    const width = saved ? Number(saved) : NaN;
    if (!Number.isNaN(width)) {
      setSidebarWidth(Math.min(460, Math.max(260, width)));
    }
  }, []);

  const startSidebarResize = (e: React.MouseEvent<HTMLDivElement>) => {
    e.preventDefault();
    const startX = e.clientX;
    const startW = sidebarWidth;

    let latest = startW;
    const onMove = (ev: MouseEvent) => {
      latest = Math.min(460, Math.max(260, startW + (ev.clientX - startX)));
      setSidebarWidth(latest);
    };
    const onUp = () => {
      window.localStorage.setItem("jaybel.sidebar.width", String(latest));
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };

    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
  };

  const refreshSessions = useCallback(async (search?: string) => {
    const list = await listSessions(search);
    setSessions(list);
    return list;
  }, []);

  const loadSession = useCallback(async (id: string) => {
    setActiveId(id);
    const turns = await listTurns(id);
    setMessages(turnsToMessages(turns));
    setCenterMode("chat");
    setActiveCategory(null);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        if (firebaseEnabled) {
          const token = await getToken();
          if (!token) return;
        }
        const me = await getMe();
        if (cancelled) return;
        setUser(me);
        let list = await refreshSessions();
        if (list.length === 0) {
          const s = await createSession();
          list = [s];
          setSessions(list);
        }
        await loadSession(list[0].id);
      } catch (e) {
        if (!cancelled) {
          setLoadError(e instanceof Error ? e.message : "Failed to connect to API");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [refreshSessions, loadSession, firebaseEnabled, getToken]);

  useEffect(() => {
    const t = setTimeout(() => {
      refreshSessions(sessionSearch || undefined).catch(() => {});
    }, 300);
    return () => clearTimeout(t);
  }, [sessionSearch, refreshSessions]);

  const handleNew = async () => {
    const currentId = activeId;
    const discardEmpty =
      Boolean(currentId) &&
      messages.length === 0 &&
      !draftInput.trim() &&
      !streaming;

    if (discardEmpty && currentId) {
      await deleteSession(currentId);
    }

    const s = await createSession();
    setSessions((prev) =>
      discardEmpty && currentId
        ? [s, ...prev.filter((x) => x.id !== currentId)]
        : [s, ...prev]
    );
    setActiveId(s.id);
    setMessages([]);
    setCenterMode("chat");
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
      setCenterMode("chat");
    } else if (activeId === id) {
      await loadSession(list[0].id);
    } else {
      setSessions(list);
    }
  };

  const handlePickStarter = (starter: StarterQuestion) => {
    setDraftInput(starter.text);
    setSendMeta({ starter_id: starter.id, category_id: starter.category_id });
    setCenterMode("chat");
  };

  const handleFollowUpPick = (text: string) => {
    setDraftInput(text);
    setSendMeta({});
    setCenterMode("chat");
  };

  const handleClarificationPick = async (text: string) => {
    if (!activeId || streaming) return;
    setSendMeta({});
    await sendMessage(activeId, text, setMessages, {});
    await refreshSessions(sessionSearch || undefined);
  };

  const handleSend = async (question: string) => {
    if (!activeId) return;
    const meta = { ...sendMeta };
    setSendMeta({});
    await sendMessage(activeId, question, setMessages, meta);
    await refreshSessions(sessionSearch || undefined);
  };

  const handleRetry = async (
    question: string,
    replaceTurnId: string,
    meta: { starterId?: string; categoryId?: string }
  ) => {
    if (!activeId || streaming) return;
    await retryQuestion(activeId, question, replaceTurnId, setMessages, {
      starter_id: meta.starterId,
      category_id: meta.categoryId,
    });
    await refreshSessions(sessionSearch || undefined);
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
      {!sidebarCollapsed && (
        <>
          <SessionSidebar
            width={sidebarWidth}
            sessions={sessions}
            activeId={activeId}
            newChatActive={centerMode === "chat" && messages.length === 0}
            faqActive={centerMode === "faq"}
            searchQuery={sessionSearch}
            onSearchChange={setSessionSearch}
            onSelect={loadSession}
            onNew={handleNew}
            onOpenFaq={() => setCenterMode("faq")}
            onDelete={handleDelete}
            onCollapse={() => setSidebarCollapsed(true)}
          />
          <div
            className="w-1 cursor-col-resize bg-transparent hover:bg-sky-200 transition"
            onMouseDown={startSidebarResize}
            role="separator"
            aria-orientation="vertical"
            aria-label="Resize sidebar"
          />
        </>
      )}
      <main className="flex-1 flex flex-col min-w-0 relative">
        {centerMode === "faq" ? (
          <FAQFullScreen
            hasRepCode={Boolean(user?.sales_rep_code)}
            activeCategory={activeCategory}
            onCategoryChange={setActiveCategory}
            onClose={() => setCenterMode("chat")}
            onPickStarter={handlePickStarter}
            onSearchPick={handleFollowUpPick}
          />
        ) : (
          <ChatWindow
            messages={messages}
            sessionId={activeId}
            onSend={handleSend}
            onRetry={handleRetry}
            disabled={streaming || !activeId}
            draftInput={draftInput}
            onDraftChange={setDraftInput}
            onFollowUpPick={handleFollowUpPick}
            onClarificationPick={handleClarificationPick}
            hideFollowUps={streaming}
            streaming={streaming}
            sidebarCollapsed={sidebarCollapsed}
            onExpandSidebar={() => setSidebarCollapsed(false)}
          />
        )}
      </main>
    </div>
  );
}
