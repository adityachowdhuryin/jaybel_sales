"use client";

import type { ReactNode } from "react";
import { useAuth } from "@/hooks/useAuth";
import { LoginPage } from "./LoginPage";

export function AuthGuard({ children }: { children: ReactNode }) {
  const { user, loading, firebaseEnabled } = useAuth();

  if (!firebaseEnabled) {
    return <>{children}</>;
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-[var(--muted)] bg-[var(--bg)]">
        <div className="ui-card px-5 py-3 text-sm">Loading…</div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  return <>{children}</>;
}
