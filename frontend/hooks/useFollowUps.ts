"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchFollowUps } from "@/lib/questionCatalog";
import type { FollowUpQuestion } from "@/types/questionCatalog";

export function useFollowUps(params: {
  sessionId: string | null;
  turnId?: string;
  question?: string;
  starterId?: string;
  enabled?: boolean;
}) {
  const [items, setItems] = useState<FollowUpQuestion[]>([]);
  const [source, setSource] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!params.enabled || !params.sessionId || !params.turnId) {
      setItems([]);
      return;
    }
    setLoading(true);
    try {
      const res = await fetchFollowUps({
        session_id: params.sessionId,
        turn_id: params.turnId,
        question: params.question,
        starter_id: params.starterId,
      });
      setItems(res.follow_ups);
      setSource(res.source);
      setError(null);
    } catch (e) {
      setItems([]);
      setError(e instanceof Error ? e.message : "Failed to load follow-ups");
    } finally {
      setLoading(false);
    }
  }, [
    params.enabled,
    params.sessionId,
    params.turnId,
    params.question,
    params.starterId,
  ]);

  useEffect(() => {
    reload();
  }, [reload]);

  return { items, source, loading, error, reload };
}
