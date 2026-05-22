"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchCategories, fetchStarters, searchStarters } from "@/lib/questionCatalog";
import type { QuestionCategory, StarterQuestion } from "@/types/questionCatalog";

export function useQuestionCatalog() {
  const [categories, setCategories] = useState<QuestionCategory[]>([]);
  const [starters, setStarters] = useState<StarterQuestion[]>([]);
  const [activeCategoryId, setActiveCategoryId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const cats = await fetchCategories();
        if (!cancelled) {
          setCategories(cats);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load categories");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const selectCategory = useCallback(async (categoryId: string) => {
    setActiveCategoryId(categoryId);
    setLoading(true);
    try {
      const items = await fetchStarters(categoryId);
      setStarters(items);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load questions");
      setStarters([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const search = useCallback(
    async (
      query: string,
      filters?: { category_id?: string; table_id?: string; intent?: string }
    ) => {
      if (
        !query.trim() &&
        !filters?.category_id &&
        !filters?.intent &&
        !filters?.table_id
      ) {
        setStarters([]);
        return [];
      }
      const hits = await searchStarters(query, filters);
      setStarters(hits);
      setActiveCategoryId(null);
      return hits;
    },
    []
  );

  const clearCategory = useCallback(() => {
    setActiveCategoryId(null);
    setStarters([]);
  }, []);

  return {
    categories,
    starters,
    activeCategoryId,
    loading,
    error,
    selectCategory,
    search,
    clearCategory,
  };
}
