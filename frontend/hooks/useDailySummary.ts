"use client";

import { useEffect, useState } from "react";
import { fetchDailySummary } from "@/lib/api";
import type { DailyBusinessSummary } from "@/types/dashboard";

export function useDailySummary() {
  const [data, setData] = useState<DailyBusinessSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const summary = await fetchDailySummary();
        if (!cancelled) {
          setData(summary);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load summary");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return { data, loading, error };
}
