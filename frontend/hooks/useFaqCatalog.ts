"use client";

import { useEffect, useState } from "react";
import { fetchFaqCatalog } from "@/lib/questionCatalog";
import type { QuestionCategory, StarterQuestion } from "@/types/questionCatalog";

export function useFaqCatalog() {
  const [categories, setCategories] = useState<QuestionCategory[]>([]);
  const [starters, setStarters] = useState<StarterQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchFaqCatalog();
        if (!cancelled) {
          setCategories(data.categories);
          setStarters(data.starters);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load FAQ");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return { categories, starters, loading, error };
}
